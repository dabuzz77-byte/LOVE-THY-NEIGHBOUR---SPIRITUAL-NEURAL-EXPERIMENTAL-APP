"""Local Java/Python message bus with a measured 7.83 Hz software heartbeat.

Python 3.10+, standard library only. Does not load discovered applications.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import deque
import hashlib
import hmac
import json
import math
from pathlib import Path
import re
import secrets
import socket
import sqlite3
import struct
import time
import uuid

MAGIC = b"VB01"
HEADER = struct.Struct("!4sI")
MAX_FRAME = 262144
HZ = 7.83
PERIOD = 1 / HZ
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")
TOPICS = {"service.status", "text.annotation", "workflow.request", "workflow.result"}
THEMES = {
    "compassion": ["compassion", "merciful", "mercy", "kindness", "gentleness"],
    "truthfulness": ["truth", "truthfulness", "honesty"],
    "restraint": ["restraint", "forbearance", "patience"],
    "stewardship": ["economy", "stewardship", "sustainability"],
    "cooperation": ["cooperation", "peace", "peacemakers"],
    "invention": ["invention", "inventions", "inventor"],
    "learning": ["learning", "knowledge", "research"],
    "humility": ["humility", "humble"],
}
BASE = Path(__file__).resolve().parent


def encoded(value):
    body = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if not 0 < len(body) <= MAX_FRAME:
        raise ValueError("Frame exceeds 256 KiB")
    return HEADER.pack(MAGIC, len(body)) + body


def decoded(body):
    def invalid(value):
        raise ValueError("Non-finite JSON number")
    value = json.loads(body, parse_constant=invalid)
    if not isinstance(value, dict):
        raise ValueError("Message must be an object")
    return value


def size_from(header):
    magic, size = HEADER.unpack(header)
    if magic != MAGIC or not 0 < size <= MAX_FRAME:
        raise ValueError("Invalid VB01 frame header")
    return size


async def read_frame(reader):
    size = size_from(await reader.readexactly(HEADER.size))
    return decoded(await reader.readexactly(size))


def read_exact(sock, count):
    result = bytearray()
    while len(result) < count:
        chunk = sock.recv(count - len(result))
        if not chunk:
            raise EOFError("Backbone disconnected")
        result.extend(chunk)
    return bytes(result)


def token_at(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as file:
            file.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    token = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        raise ValueError("Invalid token file; expected 64 lowercase hex characters")
    return token


class Client:
    """Blocking client. Use from one worker thread; never from a GUI callback."""
    def __init__(self, port=17830, token_file=None, service="python-client", topics=None):
        token = Path(token_file or BASE / "data" / "token.txt").read_text(encoding="utf-8").strip()
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        self.sock.settimeout(10)
        self.pending = deque()
        self.dropped = 0
        try:
            self.sock.sendall(encoded({"op": "hello", "token": token, "service": service,
                                       "topics": topics if topics is not None else ["pulse"]}))
            welcome = self._read()
            if welcome.get("op") != "welcome":
                raise ConnectionError(welcome.get("error", "Handshake rejected"))
            self.welcome = welcome
        except BaseException:
            self.sock.close()
            raise

    def _read(self):
        return decoded(read_exact(self.sock, size_from(read_exact(self.sock, HEADER.size))))

    def receive(self):
        return self.pending.popleft() if self.pending else self._read()

    def request(self, op, **fields):
        request_id = uuid.uuid4().hex
        self.sock.sendall(encoded(dict(fields, op=op, request_id=request_id)))
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            message = self._read()
            if message.get("request_id") == request_id:
                if message.get("op") == "error":
                    raise ValueError(message.get("error"))
                return message
            if len(self.pending) == 256:
                self.pending.popleft()
                self.dropped += 1
            self.pending.append(message)
        raise TimeoutError("No reply within 10 seconds")

    def publish(self, topic, data):
        return self.request("publish", topic=topic, data=data)

    def graph(self):
        nodes, edges, offset = {}, [], 0
        while True:
            page = self.request("graph", offset=offset)["data"]
            nodes.update((n["id"], n) for n in page["nodes"])
            edges.extend(page["edges"])
            if page["next_offset"] is None:
                return {"nodes": list(nodes.values()), "edges": edges, "note": page["note"]}
            offset = page["next_offset"]

    def close(self):
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Knowledge:
    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS passages (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, data TEXT NOT NULL)")

    def put(self, passage):
        if not isinstance(passage, dict):
            raise ValueError("Passage must be an object")
        required = {"id": 80, "title": 300, "author": 200, "reference": 500,
                    "source": 1000, "text": 20000}
        clean = {}
        for key, limit in required.items():
            value = passage.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"{key} must contain 1..{limit} characters")
            clean[key] = value.strip()
        if not ID.fullmatch(clean["id"]):
            raise ValueError("Invalid passage id")
        themes = passage.get("themes", [])
        if not isinstance(themes, list) or len(themes) > len(THEMES) or any(not isinstance(t, str) or t not in THEMES for t in themes):
            raise ValueError("Unknown theme; see THEMES in backbone.py")
        kind = passage.get("kind", "quotation")
        if kind not in {"quotation", "paraphrase", "user-note"}:
            raise ValueError("kind must be quotation, paraphrase or user-note")
        clean.update(kind=kind, themes=sorted(set(themes)),
                     sha256=hashlib.sha256(clean["text"].encode("utf-8")).hexdigest())
        self.db.execute("INSERT INTO passages VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                        (clean["id"], json.dumps(clean, ensure_ascii=False)))
        self.db.commit()
        return clean

    def graph(self, offset=0):
        if type(offset) is not int or offset < 0:
            raise ValueError("offset must be a nonnegative integer")
        rows = self.db.execute("SELECT data FROM passages ORDER BY id LIMIT 50 OFFSET ?", (offset,)).fetchall()
        passages, used = [], 0
        for row in rows:
            size = len(row[0].encode("utf-8")) + 4000
            if passages and used+size > 180000:
                break
            passages.append(json.loads(row[0]))
            used += size
        total = self.db.execute("SELECT COUNT(*) FROM passages").fetchone()[0]
        nodes, edges, present = [], [], set()
        for p in passages:
            node_id = "text:" + p["id"]
            nodes.append(dict(p, id=node_id, type="passage"))
            words = set(re.findall(r"\w+", p["text"].lower()))
            matches = {theme for theme, keys in THEMES.items() if words.intersection(keys)}
            for theme in sorted(set(p["themes"]) | matches):
                present.add(theme)
                edges.append({"from": node_id, "to": "theme:" + theme,
                              "basis": "editor-assigned" if theme in p["themes"] else "keyword-suggestion",
                              "status": "interpretation"})
        nodes.extend({"id": "theme:" + t, "type": "theme", "title": t} for t in sorted(present))
        return {"nodes": nodes, "edges": edges, "total_passages": total,
                "next_offset": offset+len(passages) if offset+len(passages)<total else None,
                "note": "Theme links are interpretations, not proof of equivalent teachings or effects on physical systems."}

    def record(self, event):
        cursor = self.db.execute("INSERT INTO events(data) VALUES (?)", (json.dumps(event, ensure_ascii=False),))
        event_id = cursor.lastrowid
        self.db.execute("DELETE FROM events WHERE id <= ?", (event_id - 10000,))
        self.db.commit()
        return event_id

    def close(self):
        self.db.close()


class Peer:
    def __init__(self, writer, service, topics):
        self.writer, self.service, self.topics = writer, service, set(topics)
        self.queue = asyncio.Queue(maxsize=64)
        self.connected_at = time.time()

    def offer(self, packet):
        try:
            self.queue.put_nowait(packet)
            return True
        except asyncio.QueueFull:
            self.writer.close()
            return False

    async def send_loop(self):
        while True:
            packet = await self.queue.get()
            self.writer.write(packet)
            await asyncio.wait_for(self.writer.drain(), timeout=2)


class Bus:
    def __init__(self, token, knowledge):
        self.token, self.knowledge = token, knowledge
        self.peers = {}
        self.tick = 0
        self.sent = 0
        self.skipped = 0
        self.slow_disconnects = 0
        self.lateness = deque(maxlen=600)
        self.pulse_times = deque(maxlen=600)
        self.stop = asyncio.Event()
        self.started = time.time()
        self.session = uuid.uuid4().hex

    def snapshot(self):
        times = list(self.pulse_times)
        rate = (len(times) - 1) / (times[-1] - times[0]) if len(times) > 1 else None
        late = sorted(self.lateness)
        return {"session": self.session, "target_hz": HZ, "period_ms": PERIOD * 1000,
                "measured_hz": rate, "pulse_count": self.sent, "skipped_ticks": self.skipped,
                "lateness_p95_ms": late[min(len(late)-1, math.ceil(len(late)*.95)-1)] if late else None,
                "slow_disconnects": self.slow_disconnects,
                "uptime_s": time.time() - self.started,
                "services": [{"id": p.service, "topics": sorted(p.topics),
                              "connected_at": p.connected_at} for p in list(self.peers.values())]}

    def broadcast(self, topic, data, service="backbone", durable=True):
        event = {"op": "event", "topic": topic, "service": service, "data": data,
                 "utc_ns": time.time_ns(), "session": self.session}
        # Encode before persistence or delivery so invalid/oversized input has no effects.
        encoded(event)
        if durable:
            event["event_id"] = self.knowledge.record(event)
        packet = encoded(event)
        for peer in list(self.peers.values()):
            if topic in peer.topics or "*" in peer.topics:
                if not peer.offer(packet):
                    self.slow_disconnects += 1
                    self.peers.pop(peer.service, None)

    async def pulse_loop(self):
        epoch = time.perf_counter()
        self.tick = 1
        while not self.stop.is_set():
            deadline = epoch + self.tick * PERIOD
            try:
                await asyncio.wait_for(self.stop.wait(), timeout=max(0, deadline - time.perf_counter()))
                break
            except asyncio.TimeoutError:
                pass
            actual = time.perf_counter()
            # Do not emit catch-up bursts after load or machine sleep.
            due = max(self.tick, int((actual - epoch) / PERIOD))
            missed = due - self.tick
            self.skipped += missed
            self.tick = due
            deadline = epoch + self.tick * PERIOD
            late_ms = max(0, (actual - deadline) * 1000)
            self.lateness.append(late_ms)
            self.pulse_times.append(actual)
            self.sent += 1
            self.broadcast("pulse", {"sequence": self.tick, "target_hz": HZ,
                           "period_ns": round(PERIOD * 1e9), "deadline_monotonic_ns": round(deadline * 1e9),
                           "sent_monotonic_ns": round(actual * 1e9), "lateness_ms": late_ms,
                           "skipped_this_pulse": missed, "skipped_total": self.skipped}, durable=False)
            self.tick += 1

    async def handle(self, reader, writer):
        peer = None
        sender = None
        try:
            if len(self.peers) >= 64:
                raise ValueError("Service limit reached")
            hello = await asyncio.wait_for(read_frame(reader), timeout=5)
            supplied = hello.get("token", "")
            if hello.get("op") != "hello" or not isinstance(supplied, str) or not hmac.compare_digest(supplied, self.token):
                raise ValueError("Authentication failed")
            service = hello.get("service")
            topics = hello.get("topics", [])
            if not isinstance(service, str) or not ID.fullmatch(service) or service in self.peers:
                raise ValueError("Invalid or already-connected service id")
            if not isinstance(topics, list) or len(topics) > 16 or any(not isinstance(t, str) or (t != "*" and not ID.fullmatch(t)) for t in topics):
                raise ValueError("Invalid subscriptions")
            if len(self.peers) >= 64:
                raise ValueError("Service limit reached")
            peer = Peer(writer, service, topics)
            self.peers[service] = peer
            peer.offer(encoded({"op": "welcome", "protocol": "VB01", "target_hz": HZ,
                                "service": service, "session": self.session}))
            sender = asyncio.create_task(peer.send_loop())
            # A failed writer closes the reader, ensuring the peer is unregistered.
            sender.add_done_callback(lambda task: writer.close())
            self.broadcast("service.status", {"id": service, "state": "connected"})
            while not self.stop.is_set():
                request = await asyncio.wait_for(read_frame(reader), timeout=300)
                request_id = request.get("request_id")
                if not isinstance(request_id, str) or not ID.fullmatch(request_id):
                    raise ValueError("Invalid request id")
                try:
                    op = request.get("op")
                    if op == "publish":
                        topic, data = request.get("topic"), request.get("data")
                        if not isinstance(topic, str) or not (topic in TOPICS or (topic.startswith("user.") and ID.fullmatch(topic))):
                            raise ValueError("Topic is reserved or unsupported")
                        if not isinstance(data, dict):
                            raise ValueError("Event data must be an object")
                        if len(encoded(data)) > 64000:
                            raise ValueError("Published data exceeds 64 KB")
                        self.broadcast(topic, data, service)
                        result = {"accepted": True}
                    elif op == "status":
                        result = self.snapshot()
                    elif op == "graph":
                        result = self.knowledge.graph(request.get("offset", 0))
                    elif op == "import":
                        passage = self.knowledge.put(request.get("passage"))
                        self.broadcast("knowledge.updated", {"id": passage["id"], "sha256": passage["sha256"]}, service)
                        result = {"id": passage["id"], "sha256": passage["sha256"]}
                    else:
                        raise ValueError("Unsupported operation")
                    response = encoded({"op": "reply", "request_id": request_id, "data": result})
                except (ValueError, TypeError) as exc:
                    response = encoded({"op": "error", "request_id": request_id, "error": str(exc)})
                if not peer.offer(response):
                    break
        except (ValueError, TypeError, UnicodeError, ConnectionError, OSError, asyncio.IncompleteReadError, asyncio.TimeoutError) as exc:
            if peer is None:
                try:
                    writer.write(encoded({"op": "error", "error": str(exc)}))
                    await asyncio.wait_for(writer.drain(), 1)
                except (OSError, asyncio.TimeoutError):
                    pass
        finally:
            if peer is not None:
                if self.peers.get(peer.service) is peer:
                    self.peers.pop(peer.service, None)
                self.broadcast("service.status", {"id": peer.service, "state": "disconnected"})
            if sender is not None:
                sender.cancel()
                await asyncio.gather(sender, return_exceptions=True)
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    async def close(self):
        self.stop.set()
        for peer in list(self.peers.values()):
            peer.writer.close()


async def serve(args):
    args.data.mkdir(parents=True, exist_ok=True)
    token = token_at(args.data / "token.txt")
    knowledge = Knowledge(args.data / "backbone.sqlite3")
    if not knowledge.db.execute("SELECT 1 FROM passages LIMIT 1").fetchone():
        for passage in json.loads((BASE / "corpus" / "starter.json").read_text(encoding="utf-8")):
            knowledge.put(passage)
    bus = Bus(token, knowledge)
    try:
        async with await asyncio.start_server(bus.handle, "127.0.0.1", args.port) as server:
            address = server.sockets[0].getsockname()
            print(f"Backbone listening on {address[0]}:{address[1]} | target {HZ} Hz", flush=True)
            pulse = asyncio.create_task(bus.pulse_loop())
            try:
                await server.serve_forever()
            finally:
                await bus.close()
                pulse.cancel()
                await asyncio.gather(pulse, return_exceptions=True)
                # Give active handlers a chance to unregister before closing the database.
                await asyncio.sleep(.05)
    finally:
        knowledge.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["serve", "status", "probe", "import", "graph"])
    parser.add_argument("--port", type=int, default=17830)
    parser.add_argument("--data", type=Path, default=BASE / "data")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if args.command == "serve":
        try:
            asyncio.run(serve(args))
        except KeyboardInterrupt:
            print("Backbone stopped.")
        return
    topics = ["pulse"] if args.command == "probe" else []
    with Client(args.port, args.data / "token.txt", "cli-" + uuid.uuid4().hex[:10], topics) as client:
        if args.command in {"status", "graph"}:
            value = client.graph() if args.command == "graph" else client.request(args.command)["data"]
            output = json.dumps(value, indent=2, ensure_ascii=False)
            if args.file:
                args.file.write_text(output, encoding="utf-8")
            else:
                print(output)
        elif args.command == "import":
            if not args.file:
                parser.error("import requires --file")
            passages = json.loads(args.file.read_text(encoding="utf-8-sig"))
            if not isinstance(passages, list):
                passages = [passages]
            for passage in passages:
                print(client.request("import", passage=passage)["data"]["id"])
        else:
            if not math.isfinite(args.seconds) or not 1 <= args.seconds <= 3600:
                parser.error("--seconds must be between 1 and 3600")
            started = time.monotonic()
            count = 0
            while time.monotonic() - started < args.seconds:
                msg = client.receive()
                if msg.get("topic") == "pulse":
                    count += 1
                    print(f"pulse {msg['data']['sequence']} | late {msg['data']['lateness_ms']:.3f} ms")
            print(json.dumps(client.request("status")["data"], indent=2))


if __name__ == "__main__":
    main()
