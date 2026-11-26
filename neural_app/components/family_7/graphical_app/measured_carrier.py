"""Fresh numeric station readings can drive the software pulse target."""
import datetime as dt
import json
import math
from neural_app import section_threads as threading
import time
import urllib.request
import urllib.parse
from ..graphical_app.privacy_network import urlopen, public_host
from ..graphical_app.sources import save_json, now
STATION_FEED = 'https://www.ressonanciaschumannhoje.com/dados/historico.json'
STATION_METHOD = 'https://www.ressonanciaschumannhoje.com/en/methodology'

class MeasuredCarrier:

    def __init__(self, rt):
        self.rt = rt
        self.lock = threading.RLock()
        self.path = rt.data / 'measured-carrier.json'
        self.config = {'enabled': True, 'url': STATION_FEED, 'max_age': 3600}
        self.reading = None
        self.error = None
        self.next_fetch = 0
        self.last_observed = None
        try:
            self.config.update(json.loads(self.path.read_text()))
        except (OSError, ValueError):
            pass

    def configure(self, body):
        values = {}
        if 'enabled' in body:
            if type(body['enabled']) is not bool:
                raise ValueError('Enabled must be boolean')
            values['enabled'] = body['enabled']
        if 'url' in body:
            value = body['url']
            if not isinstance(value, str) or len(value) > 2048:
                raise ValueError('Invalid measurement feed address')
            if value:
                parsed = urllib.parse.urlsplit(value)
                if parsed.scheme != 'https' or parsed.username or parsed.password or (parsed.port not in (None, 443)):
                    raise ValueError('Use a public HTTPS JSON endpoint')
                public_host(parsed.hostname or '')
            values['url'] = value
        if 'max_age' in body:
            if type(body['max_age']) is not int or not 30 <= body['max_age'] <= 3600:
                raise ValueError('Reading freshness must be 30–3,600 seconds')
            values['max_age'] = body['max_age']
        with self.lock:
            if values.get('url', self.config['url']) != self.config['url']:
                self.reading = None
            self.config.update(values)
            self.next_fetch = 0
            save_json(self.path, self.config)
        return self.view()

    def accept(self, body, derived=False):
        frequency = body.get('frequency_hz')
        station = body.get('station')
        stamp = body.get('measured_at')
        if type(frequency) not in (int, float) or not math.isfinite(frequency) or (not 5 <= frequency <= 12):
            raise ValueError('A measured fundamental peak must be a finite 5–12 Hz value')
        if not isinstance(station, str) or not 1 <= len(station) <= 200:
            raise ValueError('Identify the measurement station')
        if body.get('kind') not in (('spectrogram-derived',) if derived else ('measured',)):
            raise ValueError('A measured reading is required; no synthetic/default frequency')
        try:
            timestamp = dt.datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        except (AttributeError, ValueError, TypeError):
            raise ValueError('Supply measured_at as an ISO timestamp with timezone') from None
        if timestamp.tzinfo is None:
            raise ValueError('Measurement time needs a timezone')
        age = time.time() - timestamp.timestamp()
        observed = {'frequency_hz': frequency, 'station': station, 'measured_at': stamp, 'timestamp': timestamp.timestamp(), 'received': now(), 'kind': body['kind'], 'source_url': self.config['url'], 'method_url': STATION_METHOD if derived else None}
        with self.lock:
            self.last_observed = observed
        if not -30 <= age <= self.config['max_age']:
            raise ValueError('Latest source reading is stale or dated in the future; fixed fallback remains active')
        with self.lock:
            self.reading = observed
            self.error = None
        self.rt.binary_bus.feed('schumann-station-reading', self.reading)
        return self.view()

    def view(self):
        with self.lock:
            age = time.time() - self.reading['timestamp'] if self.reading else None
            fresh = self.reading is not None and -30 <= age <= self.config['max_age']
            active = self.config['enabled'] and fresh
            return {'config': dict(self.config), 'reading': dict(self.reading) if self.reading else None, 'age_seconds': round(age, 1) if age is not None else None, 'using_live_reading': active, 'target_hz': self.reading['frequency_hz'] if active else 7.83, 'error': self.error, 'status': ('station spectrogram-derived peak drives software pulse' if self.reading['kind'] == 'spectrogram-derived' else 'station reading drives software pulse') if active else 'fixed 7.83 Hz fallback; no fresh station reading', 'last_observed': dict(self.last_observed) if self.last_observed else None, 'preset_url': STATION_FEED, 'method_url': STATION_METHOD, 'scope': 'A supplied station peak controls software timing. Source measurement provenance is asserted by that station; this computer is not an ELF sensor.'}

    def frequency(self):
        return self.view()['target_hz']

    def refresh(self):
        with self.lock:
            url = self.config['url']
        if not url:
            raise ValueError('Configure a numeric measurement feed or submit a reading from a sensor')
        request = urllib.request.Request(url, headers={'User-Agent': 'PostscarcityObservatory/4.0', 'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read(65537)
                if len(raw) > 65536:
                    raise ValueError('Measurement response is too large')
                payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError('Measurement feed must return a JSON object')
            if url == STATION_FEED:
                if payload.get('campos') != ['t', 'hz', 'intensidade', 'estado']:
                    raise ValueError('Station series format changed')
                rows = payload.get('dados', [])
                if not isinstance(rows, list) or not rows:
                    raise ValueError('Station series is empty')
                latest = max(rows, key=lambda r: dt.datetime.fromisoformat(r[0]).timestamp())
                if len(latest) != 4 or latest[3] != 'ok' or latest[1] is None:
                    with self.lock:
                        self.reading = None
                    raise ValueError('Station rejected its latest reading; waiting for a usable measurement')
                return self.accept({'frequency_hz': latest[1], 'station': 'Tomsk SOS-70 · extracted by Ressonância Schumann Hoje', 'measured_at': latest[0], 'kind': 'spectrogram-derived'}, derived=True)
            return self.accept(payload)
        except Exception as exc:
            with self.lock:
                self.error = str(exc)
            raise

    def loop(self):
        for _shared_tick in range(1):
            with self.lock:
                due = self.config['enabled'] and self.config['url'] and (time.monotonic() >= self.next_fetch)
                if due:
                    self.next_fetch = time.monotonic() + 60
            if due:
                try:
                    self.refresh()
                except Exception:
                    pass
