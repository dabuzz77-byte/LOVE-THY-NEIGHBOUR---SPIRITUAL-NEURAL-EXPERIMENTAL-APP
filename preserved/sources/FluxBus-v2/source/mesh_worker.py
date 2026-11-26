"""Always-available mesh worker with a saved switch and lossless durable outbox."""
from copy import deepcopy
import json
import threading
import time
import uuid
from hub import database
from mesh_engine import prepare_mesh_run, packet_for, complete_run
from mesh_transport import encoded, initialize_mesh_tables, send_mesh_packet
from payload_storage import pack_text


class ContinuousMeshModule:
    MANUAL_SQL = "SELECT p.rowid AS sequence,p.id,p.source,p.input_json FROM mesh_requests r CROSS JOIN pipeline_jobs p ON p.id=r.job_id ORDER BY r.rowid LIMIT 1"
    NEXT_SQL = "SELECT rowid AS sequence,id,source,input_json FROM pipeline_jobs WHERE rowid>(SELECT cursor FROM mesh_control WHERE id=1) ORDER BY rowid LIMIT 1"

    def __init__(self, db_path, target, ready=None):
        self.db_path = str(db_path)
        self.target = target  # Reads the existing hub's actual bound address/port.
        self.ready = ready or (lambda: True)
        self.lock = threading.RLock(); self.stop_event = threading.Event(); self.wake = threading.Event()
        self.thread = None; self.latest = {}; self.error = ""; self.active_job = None
        initialize_mesh_tables(self.db_path)
        with database(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS mesh_control (id INTEGER PRIMARY KEY CHECK(id=1),enabled INTEGER NOT NULL,cursor INTEGER NOT NULL,session_id TEXT NOT NULL,settings_json TEXT NOT NULL)")
            cursor = conn.execute("SELECT COALESCE(MAX(rowid),0) FROM pipeline_jobs").fetchone()[0]
            conn.execute("INSERT OR IGNORE INTO mesh_control VALUES (1,1,?,?,?)", (cursor, str(uuid.uuid4()), encoded({"identifiers": []})))
            conn.execute("CREATE TABLE IF NOT EXISTS mesh_outbox (job_id TEXT PRIMARY KEY,sequence INTEGER NOT NULL,source TEXT NOT NULL,routing_tag TEXT NOT NULL,status TEXT NOT NULL,manual INTEGER NOT NULL,attempts INTEGER NOT NULL,next_attempt REAL NOT NULL,created_at REAL NOT NULL,updated_at REAL NOT NULL,packet_json TEXT,result_json TEXT NOT NULL,error TEXT)")
            conn.execute("CREATE INDEX IF NOT EXISTS mesh_due ON mesh_outbox(status,next_attempt)")
            conn.execute("CREATE INDEX IF NOT EXISTS mesh_recent ON mesh_outbox(created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS mesh_updated ON mesh_outbox(updated_at DESC)")
            conn.execute("CREATE TABLE IF NOT EXISTS mesh_requests (job_id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE IF NOT EXISTS mesh_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,created_at REAL NOT NULL,status TEXT NOT NULL,result_json TEXT NOT NULL)")
            control = conn.execute("SELECT * FROM mesh_control WHERE id=1").fetchone()
            self.enabled = bool(control["enabled"]); self.session_id = control["session_id"]
            self.settings = json.loads(control["settings_json"])
            latest = conn.execute("SELECT job_id,status,attempts,result_json,error FROM mesh_outbox ORDER BY updated_at DESC LIMIT 1").fetchone()
            if latest: self.latest = self.summary(latest["job_id"], latest["status"], latest["attempts"], json.loads(latest["result_json"]), latest["error"])

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, name="Local mesh gateway", daemon=True); self.thread.start()

    def stop(self):
        self.stop_event.set(); self.wake.set()
        if self.thread: self.thread.join(timeout=12)

    def set_enabled(self, enabled):
        with self.lock, database(self.db_path) as conn:
            conn.execute("UPDATE mesh_control SET enabled=? WHERE id=1", (int(bool(enabled)),))
            self.enabled = bool(enabled)
        self.wake.set()

    def set_identifiers(self, identifiers):
        values = list(dict.fromkeys(value.strip() for value in identifiers if value.strip()))
        with self.lock, database(self.db_path) as conn:
            self.settings = {"identifiers": values}
            conn.execute("UPDATE mesh_control SET settings_json=? WHERE id=1", (pack_text(conn, encoded(self.settings)),))

    def request(self, job_id):
        with database(self.db_path) as conn:
            if not conn.execute("SELECT 1 FROM pipeline_jobs WHERE id=?", (job_id,)).fetchone(): raise ValueError("Input was not found")
            conn.execute("INSERT OR IGNORE INTO mesh_requests VALUES (?)", (job_id,))
        self.wake.set()

    def _prepare_next(self):
        with self.lock, database(self.db_path) as conn:
            manual = conn.execute(self.MANUAL_SQL).fetchone()
            row = manual or (conn.execute(self.NEXT_SQL).fetchone() if self.enabled else None)
            if row is None: return False
            existing = conn.execute("SELECT status FROM mesh_outbox WHERE job_id=?", (row["id"],)).fetchone()
            if existing:
                if manual is not None and existing["status"] in ("READY", "RETRY"):
                    conn.execute("UPDATE mesh_outbox SET manual=1,next_attempt=0 WHERE job_id=?", (row["id"],))
                conn.execute("DELETE FROM mesh_requests WHERE job_id=?", (row["id"],))
                if manual is None: conn.execute("UPDATE mesh_control SET cursor=MAX(cursor,?) WHERE id=1", (row["sequence"],))
                return True
            identifiers = self.settings["identifiers"][:]
        tag = str(uuid.uuid4()); packet = None; error = None
        try:
            host, port = self.target()
            result = prepare_mesh_run(json.loads(row["input_json"]), f"tcp://{host}:{port}", self.session_id, identifiers, tag)
            packet = packet_for(result["GATEWAY_REPORT"])
            status = "READY" if result["GATEWAY_REPORT"]["VIRTUE_PASSED"] else "HOLD"
            result["SESSION_BRIDGE"]["RESOLUTION_DIRECTIVE"] = "LOCAL_OUTBOX_PERSISTED"
        except Exception as failure:
            status = "ERROR"; error = str(failure); result = {"status": "ERROR", "error": error}
        now = time.time()
        with database(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("INSERT OR IGNORE INTO mesh_outbox VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (row["id"],row["sequence"],row["source"],tag,status,int(manual is not None),0,0,now,now,
                          pack_text(conn, encoded(packet)) if packet is not None else None,pack_text(conn, encoded(result)),error))
            conn.execute("DELETE FROM mesh_requests WHERE job_id=?", (row["id"],))
            if manual is None: conn.execute("UPDATE mesh_control SET cursor=MAX(cursor,?) WHERE id=1", (row["sequence"],))
        with self.lock: self.latest = self.summary(row["id"], status, 0, result, error)
        return True

    def _dispatch_due(self):
        with self.lock, database(self.db_path) as conn:
            row = conn.execute("SELECT job_id,routing_tag,attempts,packet_json,result_json FROM mesh_outbox WHERE status IN ('READY','RETRY') AND next_attempt<=? AND (? OR manual=1) ORDER BY next_attempt,sequence LIMIT 1", (time.time(), int(self.enabled))).fetchone()
            if row is None: return False
            self.active_job = row["job_id"]
        try:
            host, port = self.target()
            receipt = (send_mesh_packet(json.loads(row["packet_json"]),row["routing_tag"],host,port,stop_event=self.stop_event)
                       if self.ready() else {"status":"FAILED","delivery_confirmed":False,"error":"The Flux Bus local hub is stopped or could not bind its port"})
            report = json.loads(row["result_json"]); complete_run(report, receipt)
            delivered = receipt.get("delivery_confirmed") is True
            if delivered: report["SESSION_BRIDGE"]["RESOLUTION_DIRECTIVE"] = "LOCAL_SESSION_AND_HUB_RECEIPT_PERSISTED"
            status = "ACK" if delivered else "RETRY"
            attempts = row["attempts"] + 1
            next_attempt = 0 if delivered else time.time() + min(60, 2 ** min(attempts, 6))
            with database(self.db_path) as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("INSERT INTO mesh_attempts(job_id,created_at,status,result_json) VALUES (?,?,?,?)",
                             (row["job_id"],time.time(),receipt["status"],pack_text(conn, encoded(receipt))))
                conn.execute("UPDATE mesh_outbox SET status=?,attempts=?,next_attempt=?,updated_at=?,result_json=?,error=?,manual=0 WHERE job_id=?",
                             (status,attempts,next_attempt,time.time(),pack_text(conn, encoded(report)),receipt.get("error"),row["job_id"]))
            with self.lock:
                self.latest = self.summary(row["job_id"],status,attempts,report,receipt.get("error")); self.error = ""
            return True
        finally:
            with self.lock: self.active_job = None

    def process_next(self):
        prepared = self._prepare_next()
        return self._dispatch_due() or prepared

    def _loop(self):
        while not self.stop_event.is_set():
            try:
                if self.process_next(): continue
            except Exception as failure:
                with self.lock: self.error = str(failure)
            self.wake.wait(.5); self.wake.clear()

    @staticmethod
    def summary(job_id, status, attempts, report, error=None):
        gateway = report.get("GATEWAY_REPORT", {})
        return {"job_id": job_id, "status": status, "attempts": attempts, "error": error,
                "mesh_status": report.get("GLOBAL_TELEMETRY", {}).get("CORE_MESH_STATUS"),
                "gateway_bits": gateway.get("MESH_INTEGRATION_ARRAY", []), "binary": report.get("BINARY", []),
                "balanced_ternary": report.get("BALANCED_TERNARY", []), "net_virtue_score": gateway.get("NET_VIRTUE_SCORE"),
                "reserve": report.get("RESERVE_POOL_BALANCE"), "floor_stable": report.get("RESOURCE_FLOOR_STABLE"),
                "delivery": gateway.get("DELIVERY", {}), "redaction": gateway.get("REDACTION", {})}

    def snapshot(self):
        with self.lock:
            host, port = self.target()
            return {"enabled": self.enabled,"running": bool(self.thread and self.thread.is_alive()),
                    "active_job": self.active_job,"target": f"tcp://{host}:{port}","latest": deepcopy(self.latest),"error": self.error}

    def history(self, limit=100):
        with database(self.db_path) as conn:
            return [dict(row) for row in conn.execute("SELECT job_id,source,status,attempts,created_at,error FROM mesh_outbox ORDER BY created_at DESC LIMIT ?", (limit,))]

    def detail(self, job_id):
        with database(self.db_path) as conn:
            row = conn.execute("SELECT job_id,source,status,attempts,result_json,error FROM mesh_outbox WHERE job_id=?", (job_id,)).fetchone()
        if not row:return None
        result=dict(row);result["result"]=json.loads(result.pop("result_json"));return result

    def metadata(self, job_id):
        with database(self.db_path) as conn:
            row=conn.execute("SELECT job_id,status,attempts FROM mesh_outbox WHERE job_id=?",(job_id,)).fetchone()
        return dict(row) if row else None
