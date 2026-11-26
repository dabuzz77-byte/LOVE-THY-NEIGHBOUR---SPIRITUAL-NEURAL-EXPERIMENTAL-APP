"""Own the local listening socket, neural inference, heartbeat and process observer."""
from __future__ import annotations
import asyncio
from collections import deque
import json
from pathlib import Path
from neural_app import section_threads as threading
import time
import uuid
from ..PostscarcityHub.bus_protocol import BASE, Bus, HZ, Knowledge, token_at
from ..PostscarcityHub.neural_engine import NeuralEngine
from ..PostscarcityHub.process_monitor import ProcessMonitor
DEFAULT_SCENARIO = {'access': 45.0, 'comfort': 12.0, 'transition': 0.0, 'automation': 15.0, 'valve': True, 'gate': True}

class HubBus(Bus):

    def __init__(self, token, knowledge, runtime, model):
        super().__init__(token, knowledge)
        self.runtime, self.model = (runtime, model)
        self.processes = {'status': 'starting', 'processes': [], 'note': 'Waiting for the first process sample.'}
        self.inferences = 0

    def snapshot(self):
        result = super().snapshot()
        result.update(inference_count=self.inferences, process_count=len(self.processes['processes']), model_id=self.model.metadata['model_id'], model_mae=self.model.metadata['held_out_mae_points'])
        return result

    def broadcast(self, topic, data, service='backbone', durable=True):
        super().broadcast(topic, data, service, durable)
        self.runtime.push(topic, data)
        if topic == 'pulse':
            self.runtime.set_state(pulse=data, status=self.snapshot())

    async def extension(self, request, peer):
        if request.get('op') == 'infer':
            result = self.model.infer(request.get('scenario'))
            self.inferences += 1
            self.broadcast('inference.result', {'request_id': request['request_id'], 'service': peer.service, 'predicted': result['predicted'], 'latency_ms': result['latency_ms']}, durable=True)
            return result
        if request.get('op') == 'processes':
            offset = request.get('offset', 0)
            if type(offset) is not int or offset < 0:
                raise ValueError('Invalid process offset')
            rows = self.processes['processes']
            return {'processes': rows[offset:offset + 100], 'total': len(rows), 'note': self.processes['note'], 'next_offset': offset + 100 if offset + 100 < len(rows) else None}
        return await super().extension(request, peer)

class Runtime:

    def __init__(self, port=17300, data_dir=None, model_dir=None):
        self.port = port
        self.data_dir = Path(data_dir or BASE / 'data')
        self.model_dir = Path(model_dir or BASE / 'models')
        self.lock = threading.Lock()
        self.state = {'phase': 'stopped', 'address': f'127.0.0.1:{port}', 'error': None, 'processes': {'status': 'waiting', 'processes': [], 'note': ''}, 'status': {}, 'pulse': None}
        self.events = deque(maxlen=200)
        self.thread = None
        self.loop = None
        self.bus = None
        self.stop_requested = threading.Event()
        self.model = None

    def set_state(self, **values):
        with self.lock:
            self.state.update(values)

    def push(self, topic, data):
        if topic != 'pulse':
            with self.lock:
                self.events.append({'time': time.time(), 'topic': topic, 'data': data})

    def take(self):
        with self.lock:
            state = dict(self.state)
            events = list(self.events)
            self.events.clear()
        return (state, events)

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_requested.clear()
        self.set_state(phase='starting', error=None, status={}, pulse=None, processes={'status': 'starting', 'processes': [], 'note': 'Waiting for discovery.'})
        self.thread = threading.Thread(target=self._run, name='postscarcity-hub', daemon=True)
        self.thread.start()

    def _run(self):
        try:
            asyncio.run(self._serve())
        except Exception as exc:
            self.set_state(phase='error', error=str(exc))
        finally:
            self.loop = None
            self.bus = None

    async def _serve(self):
        self.loop = asyncio.get_running_loop()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        token = token_at(self.data_dir / 'token.txt')
        self.model = NeuralEngine(self.model_dir)
        knowledge = Knowledge(self.data_dir / 'hub.sqlite3')
        self.bus = HubBus(token, knowledge, self, self.model)
        monitor = ProcessMonitor()
        tasks = []
        server = None
        try:
            server = await asyncio.start_server(self.bus.handle, '127.0.0.1', self.port)
            self.port = server.sockets[0].getsockname()[1]
            self.set_state(phase='listening', address=f'127.0.0.1:{self.port}', model=self.model.metadata)
            self.push('hub.status', {'message': f'Listening on 127.0.0.1:{self.port} · {HZ} Hz target'})
            tasks = [asyncio.create_task(self.bus.pulse_loop()), asyncio.create_task(self._observe(monitor)), asyncio.create_task(self._labels(monitor))]
            while not self.stop_requested.is_set():
                await asyncio.sleep(0.08)
        finally:
            if server:
                server.close()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.bus.close()
            if server:
                await server.wait_closed()
            knowledge.close()
            if self.stop_requested.is_set():
                self.set_state(phase='stopped', status={}, pulse=None)

    async def _labels(self, monitor):
        while True:
            await asyncio.to_thread(monitor.refresh_labels)
            await asyncio.sleep(30)

    async def _observe(self, monitor):
        previous = {}
        while True:
            sample = await asyncio.to_thread(monitor.snapshot)
            now = {p['id']: p for p in sample['processes']}
            for id_, row in now.items():
                if id_ not in previous:
                    self.bus.broadcast('process.observed', {'id': id_, 'pid': row['pid'], 'label': row['label'], 'language': row['language']})
            for id_, row in previous.items():
                if id_ not in now:
                    self.bus.broadcast('process.ended', {'id': id_, 'pid': row['pid'], 'label': row['label']})
            self.bus.processes = sample
            self.set_state(processes=sample, status=self.bus.snapshot())
            rows = sample['processes']
            batches = max(1, (len(rows) + 49) // 50)
            for batch in range(batches):
                self.bus.broadcast('process.sample', {'sample_id': sample.get('sample_monotonic'), 'batch': batch, 'batches': batches, 'total': len(rows), 'processes': rows[batch * 50:batch * 50 + 50]}, durable=False)
            previous = now
            await asyncio.sleep(2)

    def infer(self, scenario):
        if not self.loop or not self.bus:
            raise RuntimeError('Start the hub before running inference')

        async def work():
            peer = type('DesktopPeer', (), {'service': 'desktop-scenario'})()
            return await self.bus.extension({'op': 'infer', 'request_id': uuid.uuid4().hex, 'scenario': scenario}, peer)
        return asyncio.run_coroutine_threadsafe(work(), self.loop)

    def shutdown(self):
        self.stop_requested.set()
        if self.thread and self.thread.is_alive():
            self.set_state(phase='stopping')

    def wait_stopped(self, timeout=8):
        if self.thread:
            self.thread.join(timeout)
        return not (self.thread and self.thread.is_alive())
