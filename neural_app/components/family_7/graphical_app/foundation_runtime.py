"""Automatic scheduling defaults and actual local receipts for Flux foundation."""
import hashlib
import json
import os
from ..graphical_app.sources import now
MODULE_ID = 'FluxGroupVirtueFoundation'
MODULE_IDS = (MODULE_ID, 'VirtueInitializationLedger')
DEFAULT_WEIGHT = 3.0
DEFAULT_INTERVAL = 2.0

def configure(rt):
    rt.config['weights'] = dict(rt.config.get('weights', {}))
    rt.config['module_loops'] = dict(rt.config.get('module_loops', {}))
    for name in MODULE_IDS:
        if name in rt.modules:
            rt.config['weights'].setdefault('module:' + name, DEFAULT_WEIGHT)
            rt.config['module_loops'].setdefault(name, DEFAULT_INTERVAL)

class FoundationRecorder:
    """Append verified local receipts; rotate one backup at 5 MiB."""

    def __init__(self, rt):
        self.rt = rt
        self.path = rt.data / 'work' / 'flux-foundation.jsonl'

    def record(self, name, result):
        if name not in MODULE_IDS or not result.get('ok'):
            return
        output = result.get('reports', {}).get('module_result', {})
        current = output.get('current', {})
        if not current.get('validated'):
            return
        stage = current['stage_5']
        receipt = {'timestamp': now(), 'module': name, 'worker_pid': result.get('pid'), 'input_sha256': current['input_sha256'], 'output_sha256': stage['CAST_BACK_ALL']['output_sha256'], 'output_hex': stage['CAST_BACK_ALL']['output_hex'], 'input_bytes': current['input_byte_count'], 'changed_bits': stage['TRAJECTORY_SWEEP']['hamming_distance'], 'domain': current['stage_0']['domain'], 'literal_gate': current['global_virtue_state'], 'register_mode': current['register_mode'], 'recovery_verified': stage['TRAJECTORY_SWEEP']['xor_recovery_verified'], 'resource_delivery_verified': False}
        raw = json.dumps(receipt, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')
        receipt['sha256'] = hashlib.sha256(raw).hexdigest()
        line = (json.dumps(receipt, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists() and self.path.stat().st_size + len(line) > 5 * 1024 * 1024:
                self.path.replace(self.path.with_suffix('.previous.jsonl'))
            with self.path.open('a+b') as stream:
                start = stream.tell()
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
                stream.seek(start)
                if stream.read(len(line)) != line:
                    raise OSError('Receipt byte verification failed')
            stage['PILEDRIVE_AFRICAN_FLOOR'].update(local_ledger='written and byte-verified', receipt_path=str(self.path), receipt_sha256=receipt['sha256'])
        except OSError as exc:
            stage['PILEDRIVE_AFRICAN_FLOOR'].update(local_ledger='write failed', error=str(exc))

    def transport(self, name, result, accepted):
        if name not in MODULE_IDS:
            return
        current = result.get('reports', {}).get('module_result', {}).get('current', {})
        if not current.get('validated'):
            return
        current['stage_5']['FURTHEST_TRIBES'].update(local_chiral_queue_accepted=bool(accepted), remote_delivery_verified=False, delivery_status='Local queue receipt only; recipient delivery not verified')
