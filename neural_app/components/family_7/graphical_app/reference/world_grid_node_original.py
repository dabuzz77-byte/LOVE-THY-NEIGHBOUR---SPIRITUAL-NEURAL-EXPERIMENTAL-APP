import asyncio
import json
import random
import socket
import ssl
import struct
import sys
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Set

class IllegalTransitionError(Exception):
    """Raised when an unauthorized or invalid state transition is attempted."""
    pass

class SecureStateMachine:

    def __init__(self, initial_state: str):
        self.__current_state: str = initial_state
        self.__transitions: Dict[str, Set[str]] = {}
        print(f"[System Init] Core baseline established at state: '{self.__current_state}'")

    def register_transition(self, from_state: str, to_state: str) -> None:
        if from_state not in self.__transitions:
            self.__transitions[from_state] = set()
        self.__transitions[from_state].add(to_state)

    @property
    def current_state(self) -> str:
        return self.__current_state

    def request_transition(self, target_state: str, auth_token: bool) -> None:
        allowed_paths = self.__transitions.get(self.__current_state, set())
        if target_state not in allowed_paths:
            raise IllegalTransitionError(f"Boundary Violation: Transition from '{self.__current_state}' to '{target_state}' is undefined.")
        if not auth_token:
            raise PermissionError(f"Authentication Failure: Integrity check failed for target state '{target_state}'.")
        old_state = self.__current_state
        self.__current_state = target_state
        print(f"[Transition Success] Checked '{old_state}' -> Moved to '{self.__current_state}'")

class ExecutionHandler(ABC):

    @abstractmethod
    def process_log(self, message: str) -> None:
        pass

class LocalSandboxHandler(ExecutionHandler):

    def process_log(self, message: str) -> None:
        print(f'[Local Sandbox Runtime] Confirmed operation: {message}')

class BinaryPacketParser:
    HEADER_FORMAT = '!II'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    MAGIC_NUMBER = 1296388936

    @classmethod
    def pack_payload(cls, message: str) -> bytes:
        encoded_data = message.encode('utf-8')
        data_length = len(encoded_data)
        header = struct.pack(cls.HEADER_FORMAT, cls.MAGIC_NUMBER, data_length)
        return header + encoded_data

class PacketReassembler:

    def __init__(self):
        self.buffer = bytearray()
        self.HEADER_FORMAT = '!II'
        self.HEADER_SIZE = struct.calcsize(self.HEADER_FORMAT)
        self.MAGIC_NUMBER = 1296388936

    def append_chunk(self, data_chunk: bytes) -> List[str]:
        self.buffer.extend(data_chunk)
        completed_messages = []
        while len(self.buffer) >= self.HEADER_SIZE:
            magic, length = struct.unpack(self.HEADER_FORMAT, self.buffer[:self.HEADER_SIZE])
            if magic != self.MAGIC_NUMBER:
                print('[Parser Fault] Dropped packet. Invalid Magic Number signature.')
                del self.buffer[:1]
                continue
            total_expected_size = self.HEADER_SIZE + length
            if len(self.buffer) < total_expected_size:
                break
            frame_bytes = self.buffer[self.HEADER_SIZE:total_expected_size]
            completed_messages.append(frame_bytes.decode('utf-8'))
            del self.buffer[:total_expected_size]
        return completed_messages

class MeshTelemetryReporter:

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.start_time = time.time()
        self.total_bytes_received = 0
        self.successful_computations = 0

    def record_ingress(self, byte_length: int):
        self.total_bytes_received += byte_length

    def increment_success(self):
        self.successful_computations += 1

    def print_terminal_dashboard(self):
        print('\n' + '=' * 40)
        print(f'📡 REAL-TIME MESH NODE METRICS: {self.node_id}')
        print('=' * 40)
        print(f' Running Uptime:  {round(time.time() - self.start_time, 1)} seconds')
        print(f' Ingress Traffic: {self.total_bytes_received} total bytes parsed')
        print(f' Logic Passes:    {self.successful_computations} operations complete')
        print('=' * 40 + '\n')

class ChaosNetworkInjector:

    def __init__(self, target_success_rate: float=0.85, max_latency_ms: int=150):
        self.success_rate = target_success_rate
        self.max_latency_ms = max_latency_ms

    async def pipeline_inject(self, data_payload: bytes, writer: asyncio.StreamWriter) -> bool:
        if random.random() > self.success_rate:
            print(f'[Chaos Injector] DROPPED PACKET: Evicted payload frame ({len(data_payload)} bytes)')
            return False
        latency = random.randint(10, self.max_latency_ms) / 1000.0
        await asyncio.sleep(latency)
        writer.write(data_payload)
        await writer.drain()
        print(f'[Chaos Injector] DELIVERED PACKET: Delayed frame pass by {int(latency * 1000)}ms')
        return True

class MeshDiscoveryBeacon:

    def __init__(self, broadcast_port: int, node_id: str):
        self.port = broadcast_port
        self.node_id = node_id

    async def start_broadcast_loop(self, interval: int=5):
        print(f'[Discovery] Initialising UDP broadcast beacon loop on port {self.port}...')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)
        payload = f'DISCOVER_NODE:{self.node_id}'.encode('utf-8')
        loop = asyncio.get_running_loop()
        try:
            while True:
                await loop.sock_sendto(sock, payload, ('255.255.255.255', self.port))
                print(f"[Discovery Sent] Broadcasted identity beacon: '{self.node_id}'")
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            print('[Discovery] Stopping broadcast loop.')
        finally:
            sock.close()

class ConcurrentMeshServer:

    def __init__(self, host: str, port: int, node_id: str):
        self.host = host
        self.port = port
        self.telemetry = MeshTelemetryReporter(node_id)
        self.active_connections: Set[asyncio.StreamWriter] = set()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.active_connections.add(writer)
        peer_addr = writer.get_extra_info('peername')
        reassembler = PacketReassembler()
        print(f'[Core Loop] Node connected online: {peer_addr}. Active nodes: {len(self.active_connections)}')
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                self.telemetry.record_ingress(len(data))
                messages = reassembler.append_chunk(data)
                for msg in messages:
                    print(f"[Telemetry Receive] Source: {peer_addr} | Decoded: '{msg}'")
                    self.telemetry.increment_success()
                writer.write(b'CONCURRENT_ACK\n')
                await writer.drain()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f'[Core Loop Exception] Stream error with {peer_addr}: {e}')
        finally:
            if writer in self.active_connections:
                self.active_connections.remove(writer)
            writer.close()
            await writer.wait_closed()
            print(f'[Core Loop] Node disconnected: {peer_addr}. Active remaining: {len(self.active_connections)}')

    async def run_server(self, ssl_context: ssl.SSLContext | None=None):
        server = await asyncio.start_server(self.handle_client, self.host, self.port, ssl=ssl_context)
        print(f'[Core Loop Server] Accepting streams on secure interface {self.host}:{self.port}...')

        async def telemetry_dashboard_loop():
            while True:
                await asyncio.sleep(10)
                self.telemetry.print_terminal_dashboard()
            if sys.version_info >= (3, 11):
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(server.serve_forever())
                    tg.create_task(telemetry_dashboard_loop())
            else:
                await asyncio.gather(server.serve_forever(), telemetry_dashboard_loop())

async def main():
    print('=== NATIVE USER-SPACE REAL-TIME CODE MANIFOLD RUNTIME ===')
    state_verifier = SecureStateMachine(initial_state='ISOLATED_SANDBOX')
    state_verifier.register_transition('ISOLATED_SANDBOX', 'VERIFYING_COMPLIANCE')
    state_verifier.request_transition('VERIFYING_COMPLIANCE', auth_token=True)
    LOCAL_INTERFACE = '127.0.0.1'
    MESH_PORT = 9999
    BEACON_PORT = 9998
    server_node = ConcurrentMeshServer(LOCAL_INTERFACE, MESH_PORT, node_id='LOCAL_PC_CORE_NODE')
    discovery_service = MeshDiscoveryBeacon(BEACON_PORT, node_id='LOCAL_PC_CORE_NODE')
    ssl_context_active = None
    print('[Engine Ready] Launching integrated multi-tasking network frames.')
    if sys.version_info >= (3, 11):
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(server_node.run_server(ssl_context=ssl_context_active))
                tg.create_task(discovery_service.start_broadcast_loop(interval=5))
        except KeyboardInterrupt:
            print('\n[Node Shutdown] Safely closing server frameworks.')
    else:
        try:
            await asyncio.gather(server_node.run_server(ssl_context=ssl_context_active), discovery_service.start_broadcast_loop(interval=5))
        except KeyboardInterrupt:
            print('\n[Node Shutdown] Safely closing server frameworks.')
