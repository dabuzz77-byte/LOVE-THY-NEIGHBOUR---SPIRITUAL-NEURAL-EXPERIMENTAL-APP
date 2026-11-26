"""Chunked, acknowledged local-hub delivery with idempotent durable receipts."""
import base64
import hashlib
import json
import re
import socket
import time
import zlib
from .hub import database
from .payload_storage import pack_text

def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def initialize_mesh_tables(db_path):
    with database(db_path) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS mesh_receipts (routing_tag TEXT PRIMARY KEY, sha256 TEXT NOT NULL, payload_json TEXT NOT NULL, received_bytes INTEGER NOT NULL, received_at REAL NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS mesh_parts (routing_tag TEXT NOT NULL, part INTEGER NOT NULL, total INTEGER NOT NULL, sha256 TEXT NOT NULL, data BLOB NOT NULL, PRIMARY KEY(routing_tag,part))')

def receive_mesh_frame(frame, db_path):
    initialize_mesh_tables(db_path)
    tag, digest = (frame.get('routing_tag'), frame.get('sha256'))
    part, total = (frame.get('part'), frame.get('total'))
    if not isinstance(tag, str) or not tag or (not isinstance(digest, str)) or (not re.fullmatch('[0-9a-f]{64}', digest)):
        raise ValueError('Missing routing tag or SHA-256 fingerprint')
    if type(part) is not int or type(total) is not int or (not 0 <= part < total):
        raise ValueError('Invalid part index or total')
    data = base64.b64decode(frame.get('data', ''), validate=True)
    with database(db_path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        receipt = conn.execute('SELECT sha256,received_bytes FROM mesh_receipts WHERE routing_tag=?', (tag,)).fetchone()
        if receipt:
            if receipt['sha256'] != digest:
                raise ValueError('Routing tag already belongs to different content')
            return {'status': 'ACK', 'routing_tag': tag, 'sha256': digest, 'received_bytes': receipt['received_bytes'], 'duplicate': True}
        previous = conn.execute('SELECT total,sha256 FROM mesh_parts WHERE routing_tag=? LIMIT 1', (tag,)).fetchone()
        if previous and (previous['total'] != total or previous['sha256'] != digest):
            raise ValueError('Transfer metadata changed between parts')
        existing = conn.execute('SELECT data FROM mesh_parts WHERE routing_tag=? AND part=?', (tag, part)).fetchone()
        if existing and zlib.decompress(existing[0]) != data:
            raise ValueError('A received part was changed')
        conn.execute('INSERT OR IGNORE INTO mesh_parts VALUES (?,?,?,?,?)', (tag, part, total, digest, zlib.compress(data, 6)))
        count = conn.execute('SELECT COUNT(*) FROM mesh_parts WHERE routing_tag=?', (tag,)).fetchone()[0]
        if count != total:
            return {'status': 'PART_ACK', 'routing_tag': tag, 'sha256': digest, 'part': part, 'received_parts': count}
        raw = b''.join((zlib.decompress(row[0]) for row in conn.execute('SELECT data FROM mesh_parts WHERE routing_tag=? ORDER BY part', (tag,))))
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Complete transfer fingerprint mismatch')
        text = raw.decode('utf-8')
        if not isinstance(json.loads(text), dict):
            raise ValueError('Mesh payload must be a JSON object')
        conn.execute('INSERT INTO mesh_receipts VALUES (?,?,?,?,?)', (tag, digest, pack_text(conn, text), len(raw), time.time()))
        conn.execute('DELETE FROM mesh_parts WHERE routing_tag=?', (tag,))
    return {'status': 'ACK', 'routing_tag': tag, 'sha256': digest, 'received_bytes': len(raw), 'duplicate': False}

def send_mesh_packet(packet, routing_tag, host='127.0.0.1', port=9999, timeout=3, stop_event=None):
    raw = encoded(packet).encode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    chunk_size = 384 * 1024
    total = max(1, (len(raw) + chunk_size - 1) // chunk_size)
    sent = False
    try:
        for part in range(total):
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Module is stopping; delivery remains pending')
            frame = {'type': 'flux_mesh_chunk', 'routing_tag': routing_tag, 'sha256': digest, 'part': part, 'total': total, 'data': base64.b64encode(raw[part * chunk_size:(part + 1) * chunk_size]).decode('ascii')}
            with socket.create_connection((host, port), timeout=timeout) as client:
                client.settimeout(timeout)
                client.sendall(encoded(frame).encode('utf-8'))
                sent = True
                response = None
                buffer = bytearray()
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    client.settimeout(max(0.01, deadline - time.monotonic()))
                    chunk = client.recv(8192)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if len(buffer) > 1048576:
                        raise ValueError('Acknowledgement exceeds the hub frame size')
                    try:
                        response = json.loads(buffer.decode('utf-8'))
                        break
                    except (ValueError, UnicodeDecodeError):
                        pass
            if not isinstance(response, dict):
                raise ValueError('Incomplete hub acknowledgement')
            if response.get('status') not in ('ACK', 'PART_ACK'):
                return {'status': 'REJECTED', 'delivery_confirmed': False, 'error': response.get('error', 'Hub rejected the packet'), 'routing_tag': routing_tag}
            if response.get('routing_tag') != routing_tag or response.get('sha256') != digest:
                raise ValueError('Acknowledgement does not match the submitted packet')
            if response['status'] == 'ACK':
                if response.get('received_bytes') != len(raw):
                    raise ValueError('Acknowledged byte count differs from submitted content')
                return {**response, 'delivery_confirmed': True, 'parts': total, 'address': f'tcp://{host}:{port}'}
            if response.get('part') != part:
                raise ValueError('Acknowledgement refers to another part')
        raise ValueError('The hub has not acknowledged the complete transfer')
    except (OSError, ValueError) as error:
        return {'status': 'UNCONFIRMED' if sent else 'FAILED', 'delivery_confirmed': False, 'routing_tag': routing_tag, 'error': str(error), 'address': f'tcp://{host}:{port}'}
