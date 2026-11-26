import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from ..source.hub import database, MultiSessionHistoryParser
from ..source.payload_storage import MAGIC, pack_text
from ..source.pipeline import DataPipeline
from ..source.storage_maintenance import compact_database

class LosslessStorageTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'history.db'
        self.addCleanup(self.temp.cleanup)

    def test_unicode_and_legacy_text_are_exact(self):
        values = [None, '', 'old text', 'π 🙂\n' * 5000, json.dumps({'text': 'α' * 2000, 'values': list(range(3000))})]
        with database(self.path) as db:
            db.execute('CREATE TABLE records(value)')
            for value in values:
                db.execute('INSERT INTO records VALUES (?)', (pack_text(db, value),))
        with database(self.path) as db:
            self.assertEqual([r[0] for r in db.execute('SELECT value FROM records')], values)

    def test_duplicate_records_share_chunks_without_removing_records(self):
        payload = json.dumps([{'name': f'process-{i}', 'pid': i, 'details': 'unchanged detail' * 30} for i in range(200)])
        with database(self.path) as db:
            db.execute('CREATE TABLE records(value)')
            for i in range(100):
                db.execute('INSERT INTO records VALUES (?)', (pack_text(db, payload),))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM records').fetchone()[0], 100)
            self.assertLess(db.execute('SELECT SUM(length(data)) FROM _flux_chunks').fetchone()[0], len(payload) // 4)
            self.assertEqual(db.execute('SELECT value FROM records LIMIT 1').fetchone()[0], payload)
        self.assertLess(self.path.stat().st_size, len(payload) * 2)

    def test_corrupt_payload_is_reported(self):
        with database(self.path) as db:
            db.execute('CREATE TABLE records(value)')
            db.execute('INSERT INTO records VALUES (?)', (pack_text(db, 'abc' * 5000),))
            db.execute('UPDATE _flux_chunks SET raw_size=raw_size+1')
        with database(self.path) as db:
            with self.assertRaises(sqlite3.DatabaseError):
                db.execute('SELECT value FROM records').fetchone()

    def test_rollback_does_not_leave_broken_references(self):
        with database(self.path) as db:
            db.execute('CREATE TABLE records(value)')
        with self.assertRaises(RuntimeError):
            with database(self.path) as db:
                db.execute('INSERT INTO records VALUES (?)', (pack_text(db, 'rollback' * 1000),))
                raise RuntimeError('cancel')
        with database(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM records').fetchone()[0], 0)

    def test_full_pipeline_and_vocabulary_keep_all_inputs(self):
        pipeline = DataPipeline(self.path, auto=False)
        payload = {'text': 'learning preserved ' * 2000, 'state': 'evil', 'can': False}
        identity = pipeline.submit('manual', 'test', payload, run_now=True)
        result = pipeline.process(pipeline._claim())
        restored = json.loads(pipeline.detail(identity)['result_json'])
        self.assertEqual(restored, result)
        self.assertEqual(restored['input'], payload)
        with database(self.path) as db:
            self.assertEqual(json.loads(db.execute('SELECT content FROM history_blocks').fetchone()[0]), payload)
            self.assertEqual(db.execute("SELECT frequency FROM historical_tokens WHERE token='learning'").fetchone()[0], 1999)

    def test_migration_preserves_every_value_and_sequence(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE history_blocks(id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, source TEXT, timestamp REAL)')
            db.execute('CREATE TABLE historical_tokens(token TEXT PRIMARY KEY, frequency INTEGER)')
            db.execute('INSERT INTO historical_tokens VALUES (?,?)', ('learned', 12345))
            for i in range(35):
                db.execute('INSERT INTO history_blocks VALUES (?,?,?,?)', (i + 1, ('past record ' + str(i) + '\n') * 3000, 'user input', 1.234 + i))
            db.execute('UPDATE sqlite_sequence SET seq=99')
        db.close()
        report = compact_database(self.path)
        self.assertEqual(report['tables']['history_blocks']['rows'], 35)
        self.assertTrue(all((t['all_values_verified'] for t in report['tables'].values())))
        with database(self.path) as db:
            self.assertEqual(db.execute('SELECT content FROM history_blocks WHERE id=35').fetchone()[0], 'past record 34\n' * 3000)
            self.assertEqual(db.execute('SELECT frequency FROM historical_tokens').fetchone()[0], 12345)
            self.assertEqual(db.execute('SELECT seq FROM sqlite_sequence').fetchone()[0], 99)
        self.assertLess(report['after_bytes'], report['before_bytes'] / 3)

    def test_failed_verification_preserves_original(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE history_blocks(content TEXT)')
            db.execute('INSERT INTO history_blocks VALUES (?)', ('original text ' * 1000,))
        db.close()
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch('storage_maintenance.pack_text', return_value='wrong text'):
            with self.assertRaisesRegex(RuntimeError, 'verification failed'):
                compact_database(self.path)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)

    def test_resume_preserves_prefix_and_remaining_history(self):
        with database(self.path) as db:
            db.execute('CREATE TABLE history_blocks(id INTEGER PRIMARY KEY, content TEXT)')
            db.executemany('INSERT INTO history_blocks VALUES (?,?)', [(i, ('entry ' + str(i) + ' π ') * 300) for i in range(1300)])

        def interrupt(progress):
            if progress.get('copied') == 1000:
                raise RuntimeError('interrupted')
        with self.assertRaisesRegex(RuntimeError, 'interrupted'):
            compact_database(self.path, interrupt)
        report = compact_database(self.path, resume=True)
        self.assertEqual(report['tables']['history_blocks']['rows'], 1300)
        with database(self.path) as db:
            self.assertEqual(db.execute('SELECT content FROM history_blocks WHERE id=1299').fetchone()[0], 'entry 1299 π ' * 300)
            self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0], 'delete')

    def test_resume_rejects_changed_prefix_without_replacing_original(self):
        with database(self.path) as db:
            db.execute('CREATE TABLE history_blocks(id INTEGER PRIMARY KEY, content TEXT)')
            db.executemany('INSERT INTO history_blocks VALUES (?,?)', [(i, 'original ' * 300) for i in range(1001)])

        def interrupt(progress):
            if progress.get('copied') == 1000:
                raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            compact_database(self.path, interrupt)
        with database(self.path.with_name(self.path.name + '.compacting')) as db:
            db.execute("UPDATE history_blocks SET content='wrong' WHERE id=1")
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError, 'verification failed'):
            compact_database(self.path, resume=True)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)
