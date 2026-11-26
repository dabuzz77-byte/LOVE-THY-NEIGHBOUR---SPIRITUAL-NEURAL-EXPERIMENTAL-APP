"""Integrated Ambient2 service; original transport, telemetry and output-meter logic.
No desktop window, startup workers or automatic sends are created.
"""
from __future__ import annotations
import hashlib,json,math,os,platform,threading,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from typing import Any
try:
 import psutil
except ImportError:
 psutil=None
MAX_PAYLOAD_BYTES=16*1024
HTTP_TIMEOUT_SECONDS=8
class _WindowsOutputMeter:
    """Read Windows' default playback peak meter without recording audio.

    COM pointers are created, read, and released on the audio worker thread.
    The meter is before master-volume attenuation (Windows Core Audio behavior).
    No third-party audio package, microphone, or loopback recording is needed.
    """

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("System audio metering is available on Windows.")
        import ctypes
        import uuid

        self._ct = ctypes
        self._com_initialized = False
        self._enumerator = ctypes.c_void_p()
        self._meter = ctypes.c_void_p()
        self._device_id = ""
        self._next_device_check = 0.0

        class GUID(ctypes.Structure):
            _fields_ = [("data1", ctypes.c_uint32), ("data2", ctypes.c_uint16),
                        ("data3", ctypes.c_uint16), ("data4", ctypes.c_ubyte * 8)]

        self._guid_type = GUID
        self._meter_iid = GUID.from_buffer_copy(uuid.UUID("C02216F6-8C67-4B5B-9D00-D008E73E0064").bytes_le)
        clsid = GUID.from_buffer_copy(uuid.UUID("BCDE0395-E52F-467C-8E3D-C4579291692E").bytes_le)
        iid = GUID.from_buffer_copy(uuid.UUID("A95664D2-9614-4F35-A746-DE8DB63617E6").bytes_le)
        self._ole = ctypes.OleDLL("ole32")
        self._ole.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self._ole.CoInitializeEx.restype = ctypes.c_long
        self._ole.CoCreateInstance.argtypes = [ctypes.POINTER(GUID), ctypes.c_void_p,
            ctypes.c_uint32, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
        self._ole.CoCreateInstance.restype = ctypes.c_long
        self._ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        self._ole.CoTaskMemFree.restype = None
        self._ole.CoUninitialize.argtypes = []
        self._ole.CoUninitialize.restype = None
        try:
            self._check(self._ole.CoInitializeEx(None, 0))  # COINIT_MULTITHREADED
            self._com_initialized = True
            self._check(self._ole.CoCreateInstance(ctypes.byref(clsid), None, 1,
                ctypes.byref(iid), ctypes.byref(self._enumerator)))
            self._refresh_device()
        except Exception:
            self.close()
            raise

    @staticmethod
    def _check(result: int) -> None:
        if result < 0:
            raise OSError(f"Windows audio meter error 0x{result & 0xffffffff:08X}")

    def _method(self, pointer, slot, argtypes, *args):
        ct = self._ct
        table = ct.cast(pointer, ct.POINTER(ct.POINTER(ct.c_void_p))).contents
        function = ct.WINFUNCTYPE(ct.c_long, ct.c_void_p, *argtypes)(table[slot])
        return function(pointer, *args)

    def _release(self, pointer) -> None:
        if pointer:
            self._method(pointer, 2, [])  # IUnknown::Release
            pointer.value = None

    def _refresh_device(self) -> None:
        ct = self._ct
        device, device_id, new_meter = ct.c_void_p(), ct.c_void_p(), ct.c_void_p()
        try:
            # IMMDeviceEnumerator::GetDefaultAudioEndpoint(eRender, eMultimedia)
            self._check(self._method(self._enumerator, 4,
                [ct.c_int, ct.c_int, ct.POINTER(ct.c_void_p)], 0, 1, ct.byref(device)))
            self._check(self._method(device, 5, [ct.POINTER(ct.c_void_p)], ct.byref(device_id)))
            identifier = ct.wstring_at(device_id)
            if identifier != self._device_id or not self._meter:
                # IMMDevice::Activate(IAudioMeterInformation)
                self._check(self._method(device, 3, [ct.POINTER(self._guid_type), ct.c_uint32,
                    ct.c_void_p, ct.POINTER(ct.c_void_p)], ct.byref(self._meter_iid),
                    23, None, ct.byref(new_meter)))
                self._release(self._meter)
                self._meter, new_meter = new_meter, ct.c_void_p()
                self._device_id = identifier
        finally:
            if device_id:
                self._ole.CoTaskMemFree(device_id)
            self._release(new_meter)
            self._release(device)
        self._next_device_check = time.monotonic() + 1.0

    def read(self) -> dict[str, Any]:
        if time.monotonic() >= self._next_device_check:
            self._refresh_device()
        peak = self._ct.c_float()
        self._check(self._method(self._meter, 3,
            [self._ct.POINTER(self._ct.c_float)], self._ct.byref(peak)))
        return {"available": True, "peak": round(max(0.0, min(1.0, peak.value)), 6),
                "device_id": self._device_id}

    def close(self) -> None:
        self._release(self._meter)
        self._release(self._enumerator)
        if self._com_initialized:
            self._ole.CoUninitialize()
            self._com_initialized = False

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Keep a POST tied to the destination the user entered."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class AmbientFieldEngine:
    """Collect live host counters and send a user-authored JSON payload on demand."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._window = None
        self._send_in_progress = False
        self._last_send: dict[str, Any] = {"status": "idle"}
        self._payload_buffer = bytearray(MAX_PAYLOAD_BYTES)

    def attach_window(self, window: Any) -> None:
        self._window = window

    def _prepare_payload(self, payload: Any, tuning_factor: Any) -> tuple[dict[str, Any] | None, str | None]:
        if not isinstance(payload, str) or not payload.strip():
            return None, "Enter a message before previewing or sending."
        encoded = payload.encode("utf-8")
        if len(encoded) > MAX_PAYLOAD_BYTES:
            return None, f"The UTF-8 payload exceeds the {MAX_PAYLOAD_BYTES:,}-byte limit."
        try:
            factor = float(tuning_factor)
        except (TypeError, ValueError):
            return None, "Tuning factor must be a number from 0.1 to 10.0."
        if not math.isfinite(factor) or not 0.1 <= factor <= 10.0:
            return None, "Tuning factor must be between 0.1 and 10.0."
        digest = hashlib.sha256(encoded).hexdigest()
        with self._lock:
            self._payload_buffer[:] = b"\0" * len(self._payload_buffer)
            self._payload_buffer[:len(encoded)] = encoded
        return {"payload": payload, "payload_bytes": len(encoded), "tuning_factor": factor, "sha256": digest}, None

    def preview_payload(self, payload: str, tuning_factor: float) -> dict[str, Any]:
        prepared, error = self._prepare_payload(payload, tuning_factor)
        if error:
            return {"ok": False, "message": error}
        assert prepared is not None
        return {"ok": True, "bytes": prepared["payload_bytes"], "sha256": prepared["sha256"],
                "message": "Payload previewed locally; nothing was transmitted."}

    @staticmethod
    def _validate_endpoint(endpoint: str) -> tuple[str | None, str | None]:
        if not isinstance(endpoint, str) or not endpoint.strip():
            return None, "Enter the HTTPS endpoint that should receive this message."
        try:
            parsed = urllib.parse.urlsplit(endpoint.strip())
            hostname = parsed.hostname
        except ValueError:
            return None, "The destination URL is not valid."
        if not parsed.scheme or not hostname or parsed.username or parsed.password or parsed.fragment:
            return None, "Enter a complete URL without credentials or a fragment."
        scheme = parsed.scheme.lower()
        if scheme == "https" or (scheme == "http" and hostname.lower() in {"localhost", "127.0.0.1", "::1"}):
            return endpoint.strip(), None
        return None, "Use HTTPS. HTTP is allowed only for localhost, 127.0.0.1, or ::1."

    def transmit_payload(self, payload: str, tuning_factor: float, endpoint: str) -> dict[str, Any]:
        prepared, error = self._prepare_payload(payload, tuning_factor)
        if error:
            return {"ok": False, "message": error}
        valid_endpoint, error = self._validate_endpoint(endpoint)
        if error:
            return {"ok": False, "message": error}
        assert prepared is not None and valid_endpoint is not None
        with self._lock:
            if self._send_in_progress:
                return {"ok": False, "message": "A request is already in progress; wait for its response."}
            self._send_in_progress = True
            self._last_send = {"status": "sending", "sha256": prepared["sha256"]}

        body = json.dumps({
            "payload": prepared["payload"],
            "tuning_factor": prepared["tuning_factor"],
            "sha256": prepared["sha256"],
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False).encode("utf-8")
        try:
            worker = threading.Thread(
                target=self._send_request,
                args=(valid_endpoint, body, prepared["sha256"]),
                name="ambient-field-http-send",
                daemon=True,
            )
            worker.start()
        except Exception as exc:
            with self._lock:
                self._send_in_progress = False
            return {"ok": False, "message": f"Could not start the network request: {exc}"}
        host = urllib.parse.urlsplit(valid_endpoint).hostname or "destination"
        return {"ok": True, "status": "sending", "host": host, "sha256": prepared["sha256"]}

    def _send_request(self, endpoint: str, body: bytes, digest: str) -> None:
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8", "Accept": "application/json, text/plain, */*"},
            method="POST",
        )
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                response.read(2048)
                status = int(response.status)
                result = {"ok": 200 <= status < 300,
                          "message": f"HTTP {status} · {urllib.parse.urlsplit(endpoint).hostname}",
                          "sha256": digest}
        except urllib.error.HTTPError as exc:
            result = {"ok": False, "message": f"HTTP {exc.code} · {urllib.parse.urlsplit(endpoint).hostname}", "sha256": digest}
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            result = {"ok": False, "message": f"Request failed: {str(reason)[:220]}", "sha256": digest}
        except Exception as exc:
            result = {"ok": False, "message": f"Request failed: {str(exc)[:220]}", "sha256": digest}

        with self._lock:
            self._send_in_progress = False
            self._last_send = {"status": "ok" if result["ok"] else "error", **result}
            window = self._window
        if window is not None:
            try:
                payload_json = json.dumps(result, ensure_ascii=True)
                window.evaluate_js(f"window.setTransmissionResult({payload_json})")
            except Exception:
                pass

    def live_telemetry(self, elapsed: float, previous_rx: int | None, previous_tx: int | None) -> dict[str, Any]:
        sampled = datetime.now(timezone.utc).isoformat()
        try:
            cpu_percent = float(psutil.cpu_percent(interval=None))
            memory = psutil.virtual_memory()
            process_rss = int(psutil.Process(os.getpid()).memory_info().rss)
            pernic = psutil.net_io_counters(pernic=True) or {}
            interface_stats = psutil.net_if_stats() or {}
            active_names = [name for name in pernic if name in interface_stats and interface_stats[name].isup]
            if not active_names:
                active_names = list(pernic)
            rx_total = sum(int(pernic[name].bytes_recv) for name in active_names)
            tx_total = sum(int(pernic[name].bytes_sent) for name in active_names)
            elapsed = max(elapsed, 0.001)
            rx_rate = 0.0 if previous_rx is None else max(0.0, (rx_total - previous_rx) / elapsed)
            tx_rate = 0.0 if previous_tx is None else max(0.0, (tx_total - previous_tx) / elapsed)
            with self._lock:
                send_state = self._last_send.copy()
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": float(memory.percent),
                "memory_used": int(memory.used), "memory_total": int(memory.total),
                "process_rss": process_rss,
                "rx_total": rx_total, "tx_total": tx_total, "rx_rate": rx_rate, "tx_rate": tx_rate,
                "active_interfaces": len(active_names), "interface_names": active_names[:6],
                "hostname": platform.node() or "This computer",
                "platform": f"{platform.system()} {platform.release()}",
                "sampled_at": sampled, "last_send": send_state,
            }
        except Exception as exc:
            return {
                "cpu_percent": None, "memory_percent": None, "memory_used": None, "memory_total": None,
                "process_rss": None, "rx_total": None, "tx_total": None, "rx_rate": None, "tx_rate": None,
                "active_interfaces": 0, "interface_names": [],
                "hostname": platform.node() or "This computer",
                "platform": f"{platform.system()} {platform.release()}",
                "sampled_at": sampled, "telemetry_error": str(exc)[:180],
            }
class IntegratedAmbient2:
 def __init__(self,data):
  from .earth_field_sources import EarthFieldSources
  self.sources=EarthFieldSources(data)
  self.engine=AmbientFieldEngine();self.previous=None;self.sample_lock=threading.Lock()
 def telemetry(self):
  with self.sample_lock:
   now=time.monotonic();old=self.previous
   data=self.engine.live_telemetry(now-old[0] if old else 1,old[1] if old else None,old[2] if old else None)
   self.previous=(now,data.get('rx_total'),data.get('tx_total'))
  meter=None
  try:
   meter=_WindowsOutputMeter();data['audio']=meter.read()
  except Exception:
   data['audio']={'available':False,'peak':0,'message':'Output peak meter unavailable on this system.'}
  finally:
   if meter is not None:meter.close()
  return data
