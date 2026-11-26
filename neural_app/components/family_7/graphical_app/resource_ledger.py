"""Transactional local inventory, reservations and attributed delivery records."""
import csv
import hashlib
import io
import json
import re
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
from ..graphical_app.elevation import allocate, money
from ..graphical_app.sources import now

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)

class ResourceLedger:

    def __init__(self, folder):
        self.path = folder / 'resources.sqlite3'
        with closing(self.connect()) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, body TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, request_hash TEXT NOT NULL, body TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)')
            db.execute('INSERT OR IGNORE INTO state VALUES (1, ?)', (canonical({'revision': 0, 'unit': '', 'stock': [], 'needs': [], 'orders': [], 'source': None}),))
            db.commit()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10.0)
        db.execute('PRAGMA busy_timeout=5000')
        db.execute('PRAGMA synchronous=NORMAL')
        return db

    def view(self):
        with closing(self.connect()) as db:
            state = json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
        state['physical_delivery_verified'] = False
        state['basis'] = 'User-attributed inventory and local reservations. Delivery records require human evidence; physical events are not independently verified.'
        return state

    @staticmethod
    def allocation_input(state):
        stock = {r['id']: dict(r) for r in state['stock']}
        needs = {r['id']: dict(r) for r in state['needs']}
        for order in state['orders']:
            if order['status'] != 'reserved':
                continue
            for t in order['transfers']:
                stock[t['from']]['available'] = str(Decimal(stock[t['from']]['available']) - Decimal(t['amount']))
                needs[t['to']]['amount'] = str(Decimal(needs[t['to']]['amount']) - Decimal(t['amount']))
        return {'unit': state['unit'], 'donors': list(stock.values()), 'needs': list(needs.values())}

    def preview(self):
        state = self.view()
        data = self.allocation_input(state)
        return {'revision': state['revision'], 'input': data, 'plan': allocate(data), 'source': state['source'], 'reserved': False}

    @staticmethod
    def parse_import(body):
        text = body.get('csv')
        source = str(body.get('reference', '')).strip()
        unit = str(body.get('unit', '')).strip()
        observed = str(body.get('observed_at', '')).strip()
        if not isinstance(text, str) or not 1 <= len(text) <= 200000:
            raise ValueError('Import CSV text up to 200 KB')
        if not source or len(source) > 2000 or (not unit) or (len(unit) > 40):
            raise ValueError('Supply a resource unit and a source reference')
        try:
            date = datetime.fromisoformat(observed.replace('Z', '+00:00'))
            if date.tzinfo is None or date > datetime.now(timezone.utc):
                raise ValueError()
        except ValueError:
            raise ValueError('Supply the observation time with a timezone; future observations are not accepted') from None
        reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
        if not reader.fieldnames or not {'kind', 'id', 'amount'}.issubset(reader.fieldnames):
            raise ValueError('CSV columns must include kind, id and amount')
        stock, needs, seen = ([], [], set())

        def quantity(value):
            result = money(value)
            if Decimal(str(value)) != result:
                raise ValueError('Quantities support at most two decimal places; no silent rounding')
            return str(result)
        for row in reader:
            if len(seen) >= 500:
                raise ValueError('Import at most 500 records')
            key = (row.get('id') or '').strip()
            if not key or len(key) > 100 or key in seen:
                raise ValueError('Resource and need IDs must be nonempty and unique')
            seen.add(key)
            kind = (row.get('kind') or '').strip().lower()
            if kind == 'stock':
                item = {'id': key, 'available': quantity(row['amount'])}
                for field in ('floor', 'protected_earnings', 'protected_top'):
                    item[field] = quantity(row.get(field) or '0')
                stock.append(item)
            elif kind == 'need':
                priority = money(row.get('priority') or '1')
                if priority > 100:
                    raise ValueError('Priority must be 0–100')
                needs.append({'id': key, 'amount': quantity(row['amount']), 'priority': float(priority)})
            else:
                raise ValueError('Each kind must be stock or need')
        if not stock:
            raise ValueError('Import at least one stock record')
        allocate({'unit': unit, 'donors': stock, 'needs': needs})
        return (stock, needs, unit, {'reference': source, 'observed_at': observed, 'imported_at': now(), 'sha256': hashlib.sha256(text.encode()).hexdigest(), 'basis': 'User-supplied observation'})

    def mutate(self, action, body):
        request_id = body.get('request_id', '')
        if not isinstance(request_id, str) or not re.fullmatch('[A-Za-z0-9_-]{8,100}', request_id):
            raise ValueError('A request ID is required')
        expected = body.get('revision')
        if type(expected) is not int:
            raise ValueError('Refresh the inventory before changing it')
        request_hash = hashlib.sha256(canonical({'action': action, 'body': body}).encode()).hexdigest()
        db = self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT request_hash,body FROM events WHERE request_id=?', (request_id,)).fetchone()
            if previous:
                if previous[0] != request_hash:
                    raise ValueError('Request ID was already used for different contents')
                db.rollback()
                return {**json.loads(previous[1])['result'], 'replayed': True}
            state = json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            if state['revision'] != expected:
                raise ValueError('Inventory changed. Refresh and review the new allocation before continuing')
            if action == 'import':
                if any((o['status'] == 'reserved' for o in state['orders'])):
                    raise ValueError('Complete or cancel existing reservations before replacing inventory')
                stock, needs, unit, source = self.parse_import(body)
                state.update(stock=stock, needs=needs, unit=unit, source=source)
                result = {'status': 'inventory imported', 'records': len(stock) + len(needs), 'source': source}
            elif action == 'reserve':
                plan = allocate(self.allocation_input(state))
                if not plan['transfers']:
                    raise ValueError('No eligible stock remains for outstanding needs')
                order = {'id': uuid.uuid4().hex[:12], 'status': 'reserved', 'created': now(), 'transfers': plan['transfers'], 'source': state['source'], 'physical_delivery_verified': False}
                state['orders'].append(order)
                result = {'status': 'reserved', 'order': order, 'plan': plan}
            elif action in ('deliver', 'cancel'):
                order = next((o for o in state['orders'] if o['id'] == body.get('id')), None)
                if not order or order['status'] != 'reserved':
                    raise ValueError('Choose an open reservation')
                reference = str(body.get('reference', '')).strip()
                reviewer = str(body.get('reviewer', '')).strip()
                if not reference or not reviewer or len(reference) > 2000 or (len(reviewer) > 120):
                    raise ValueError('Record the responsible person and evidence reference or cancellation reason')
                if action == 'deliver':
                    stock = {r['id']: r for r in state['stock']}
                    needs = {r['id']: r for r in state['needs']}
                    for transfer in order['transfers']:
                        d = stock[transfer['from']]
                        n = needs[transfer['to']]
                        amount = Decimal(transfer['amount'])
                        d['available'] = str(Decimal(d['available']) - amount)
                        n['amount'] = str(Decimal(n['amount']) - amount)
                    allocate(self.allocation_input({**state, 'orders': [o for o in state['orders'] if o['id'] != order['id']]}))
                order.update(status='delivery recorded' if action == 'deliver' else 'cancelled', closed=now(), reviewer=reviewer, reference=reference)
                result = {'status': order['status'], 'order': order}
            else:
                raise ValueError('Unknown resource action')
            state['revision'] += 1
            result.update(revision=state['revision'], physical_delivery_verified=False)
            last = db.execute('SELECT digest FROM events ORDER BY seq DESC LIMIT 1').fetchone()
            prev = last[0] if last else '0' * 64
            event = canonical({'action': action, 'time': now(), 'request_id': request_id, 'request_hash': request_hash, 'result': result})
            digest = hashlib.sha256((prev + event).encode()).hexdigest()
            db.execute('UPDATE state SET body=? WHERE id=1', (canonical(state),))
            db.execute('INSERT INTO events(request_id,request_hash,body,previous,digest) VALUES(?,?,?,?,?)', (request_id, request_hash, event, prev, digest))
            db.commit()
            return {**result, 'receipt_hash': digest, 'replayed': False}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def verify(self):
        prev = '0' * 64
        count = 0
        with closing(self.connect()) as db:
            for row in db.execute('SELECT body,previous,digest FROM events ORDER BY seq'):
                if row[1] != prev or hashlib.sha256((prev + row[0]).encode()).hexdigest() != row[2]:
                    raise ValueError('Resource receipt chain did not verify')
                prev = row[2]
                count += 1
        return {'verified': True, 'events': count, 'last_hash': prev, 'basis': 'Local integrity check; no independent authentication'}
