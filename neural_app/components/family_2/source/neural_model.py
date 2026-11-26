"""Small masked autoencoder and supervised preference head. Pure Python backprop."""
from copy import deepcopy
import hashlib
import json
import math
import random
import re
from ..source.unified_runtime import ENGINE_NAMES as UNIFIED, resolve_result
from ..source.platform_alignment import ENGINE_NAMES as PLATFORM
from ..source.karmic_welfare import ENGINE_NAMES as WELFARE
from ..source.virtue_text import ENGINE_NAMES as TEXT
SUITE = ('InfiniteVirtueStabilizer', 'UniversalKrakenReleaseEngine', 'GlobalEdgePassthroughEngine', 'FinalStateCascadeEngine', 'UniversalKarmicEngine', 'Bit10IsolationEngine', 'Ring0SovereignEngine', 'WorldGridRefactorEngine', 'AdaptiveSystemInitializer')
AUDITS = {'LogicImprintMatrixEngine': 'production', 'ResponseImprintEngine': 'response_imprint', 'BoundaryImprintEngine': 'boundary_imprint', 'FloorOptimizationEngine': 'floor', 'VirtueAssessmentEngine': 'virtue', 'UnrestrictBias': 'unrestrict', 'CoreRegistry': 'master_registry'}
MASTER = {'audit_hardware': 'SUBSTRATE_DIAGNOSTICS', 'CoreFloorEngine': 'FLOOR_OPTIMIZATION', 'CoreImprintEngine': 'LOGIC_IMPRINT', 'CoreInversionOperator': 'INVERSION_OPERATOR'}
MESH = {'PrivacyPreservingMeshGateway': 'GATEWAY_REPORT', 'SessionBridgeController': 'SESSION_BRIDGE', 'IntegratedGlobalMeshEngine': None}
MODULES = {'unified': UNIFIED, 'platform_alignment': PLATFORM, 'karmic_welfare': WELFARE, 'virtue_text': TEXT, 'souls_ingress': ('SoulsOverDigitsCore', 'CentralBankResourceGovernor', 'CentralBankMeshController', 'WorldGridCentralBankingCore')}
GROUPS = [('suite.' + n, 3) for n in SUITE] + [(prefix + '.' + n, 3) for prefix, names in MODULES.items() for n in names] + [('audit.' + n, 3) for n in (*AUDITS, *MASTER)] + [('mesh.' + n, 3) for n in MESH] + [('routing.DeepVirtueAuditor', 3), ('routing.SignalRoute', 3), ('activity.HostTelemetry', 6), ('input.TextPatterns', 16)]
LEGACY_GROUPS = list(GROUPS)
from ..source.reference_catalog import ENGINE_NAMES as REFERENCE
MODULES['reference'] = REFERENCE
GROUPS = GROUPS + [('reference.' + name, 3) for name in REFERENCE]

def remap_features(x, mask, old_groups, new_groups=GROUPS):
    old_groups = [tuple(row) for row in old_groups]
    if len(x) != sum((size for _, size in old_groups)) or len(mask) != len(x):
        raise ValueError('Invalid saved feature schema')
    positions = {}
    offset = 0
    for name, size in old_groups:
        positions[name] = (offset, size)
        offset += size
    new_x = []
    new_mask = []
    for name, size in new_groups:
        start, old_size = positions.get(name, (0, 0))
        new_x.extend(x[start:start + min(size, old_size)] + [0.0] * max(0, size - old_size))
        new_mask.extend(mask[start:start + min(size, old_size)] + [False] * max(0, size - old_size))
    return (new_x, new_mask)

def sigmoid(x):
    return 1 / (1 + math.exp(-max(-40, min(40, x))))

class NeuralModel:

    def __init__(self, groups=None, hidden=8):
        self.groups = [(name, size) for name, size in groups or GROUPS]
        self.group_for = [i for i, (_, size) in enumerate(self.groups) for _ in range(size)]
        self.n, self.h = (len(self.group_for), hidden)
        rng = random.Random(369)
        self.g = [0.0] * len(self.groups)
        self.w = [[rng.uniform(-0.12, 0.12) for _ in range(self.n)] for _ in range(hidden)]
        self.b = [0.0] * hidden
        self.d = [[rng.uniform(-0.12, 0.12) for _ in range(hidden)] for _ in range(self.n)]
        self.c = [0.0] * self.n
        self.p = [rng.uniform(-0.12, 0.12) for _ in range(hidden)]
        self.q = 0.0
        self.updates = self.supervised = 0

    def state(self):
        return {k: deepcopy(getattr(self, k)) for k in ('groups', 'h', 'g', 'w', 'b', 'd', 'c', 'p', 'q', 'updates', 'supervised')}

    @classmethod
    def from_state(cls, state):
        model = cls(state['groups'], state['h'])
        for k in ('g', 'w', 'b', 'd', 'c', 'p', 'q', 'updates', 'supervised'):
            setattr(model, k, deepcopy(state[k]))
        return model

    def expanded(self, groups=GROUPS):
        """Add groups by name, retaining every learned parameter and prediction."""
        groups = [tuple(row) for row in groups]
        if self.groups == groups:
            return self
        wanted = dict(groups)
        if any((wanted.get(name, 0) < size for name, size in self.groups)):
            raise ValueError('Migration would remove an existing neural input')
        result = NeuralModel(groups, self.h)
        old_pos = {}
        offset = 0
        for i, (name, size) in enumerate(self.groups):
            old_pos[name] = (i, offset, size)
            offset += size
        offset = 0
        for i, (name, size) in enumerate(groups):
            if name in old_pos:
                old_i, start, count = old_pos[name]
                result.g[i] = self.g[old_i]
                for j in range(count):
                    result.c[offset + j] = self.c[start + j]
                    result.d[offset + j] = deepcopy(self.d[start + j])
                    for h in range(self.h):
                        result.w[h][offset + j] = self.w[h][start + j]
            offset += size
        for key in ('b', 'p', 'q', 'updates', 'supervised'):
            setattr(result, key, deepcopy(getattr(self, key)))
        return result

    def forward(self, x, mask):
        if len(x) != self.n or len(mask) != self.n:
            raise ValueError('Feature schema mismatch')
        if any((not math.isfinite(v) or abs(v) > 1 for v in x)):
            raise ValueError('Invalid normalized feature')
        if any((type(v) is not bool for v in mask)):
            raise ValueError('Boolean observation mask required')
        gains = [2 * sigmoid(g) for g in self.g]
        z = [v * gains[group] if seen else 0.0 for v, group, seen in zip(x, self.group_for, mask)]
        hidden = [math.tanh(b + sum((a * v for a, v in zip(row, z)))) for row, b in zip(self.w, self.b)]
        reconstruction = [math.tanh(b + sum((a * v for a, v in zip(row, hidden)))) for row, b in zip(self.d, self.c)]
        score = sigmoid(self.q + sum((a * v for a, v in zip(self.p, hidden))))
        loss = sum(((a - b) ** 2 for a, b, m in zip(reconstruction, x, mask) if m)) / max(1, sum(mask))
        return dict(score=score, loss=loss, hidden=hidden, reconstruction=reconstruction, z=z, gains=gains)

    def train(self, x, mask, target=None, rate=0.035):
        if target is not None and (isinstance(target, bool) or not isinstance(target, (int, float)) or (not math.isfinite(target)) or (not 0 <= target <= 1)):
            raise ValueError('Target must be between 0 and 1')
        old = self.forward(x, mask)
        h = old['hidden']
        y = old['reconstruction']
        z = old['z']
        observed_count = max(1, sum(mask))
        dy = [2 * (a - b) * (1 - a * a) / observed_count if m else 0.0 for a, b, m in zip(y, x, mask)]
        dp = old['score'] - target if target is not None else 0.0
        dh = [(sum((self.d[i][j] * dy[i] for i in range(self.n))) + self.p[j] * dp) * (1 - h[j] * h[j]) for j in range(self.h)]
        dg = [0.0] * len(self.groups)
        for i, group in enumerate(self.group_for):
            if mask[i]:
                s = old['gains'][group] / 2
                dg[group] += sum((self.w[j][i] * dh[j] for j in range(self.h))) * x[i] * 2 * s * (1 - s)
        for i in range(self.n):
            self.c[i] -= rate * dy[i]
            for j in range(self.h):
                self.d[i][j] -= rate * dy[i] * h[j]
        for j in range(self.h):
            self.p[j] -= rate * dp * h[j]
            self.b[j] -= rate * dh[j]
            for i in range(self.n):
                self.w[j][i] -= rate * dh[j] * z[i]
        self.q -= rate * dp
        for i in range(len(self.g)):
            self.g[i] -= rate * dg[i]
        self.updates += 1
        self.supervised += int(target is not None)
        return (old, self.forward(x, mask))

def result_features(value, status='COMPLETE'):
    if str(status).startswith(('AWAITING', 'READY_TO_EXPORT')) or value is None:
        return ([0.0] * 3, [False] * 3)
    bools = []
    numbers = []

    def walk(item):
        if isinstance(item, bool):
            bools.append(1.0 if item else -1.0)
        elif isinstance(item, (int, float)) and math.isfinite(item):
            numbers.append(math.tanh(math.copysign(math.log1p(abs(item)), item) / 10))
        elif isinstance(item, dict):
            for key, child in item.items():
                if not re.search('timestamp|token|secret|hash|signature|_id$|^pid$|last_seen|milliseconds|time_ns', key, re.I):
                    walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)
    walk(value)
    return ([-1.0 if status == 'ERROR' else 1.0, sum(bools) / max(1, len(bools)), sum(numbers) / max(1, len(numbers))], [True, bool(bools), bool(numbers)])

def build_features(payload, reports, pipeline_result=None, audit=None, mesh=None):
    values = {}
    observed = []
    for row in (pipeline_result or {}).get('engines', []):
        values['suite.' + row['engine']] = result_features(row.get('output'))
    if pipeline_result:
        values['routing.DeepVirtueAuditor'] = result_features(pipeline_result.get('audit'))
        values['routing.SignalRoute'] = result_features(pipeline_result.get('route'))
    for prefix, report in reports.items():
        stages = {s['engine']: s['status'] for s in report.get('stages', [])}
        for name in MODULES.get(prefix, ()):
            if name in report.get('engines', {}):
                resolved = resolve_result(report, name)
                status = stages.get(name, 'COMPLETE')
                if isinstance(resolved, dict):
                    status = resolved.get('status', status)
                values[prefix + '.' + name] = result_features(resolved, status)
    if audit:
        for name, key in AUDITS.items():
            val = audit.get(key)
            values['audit.' + name] = result_features(val, val.get('status', 'COMPLETE') if isinstance(val, dict) else 'COMPLETE')
        registry = {row['module']: row['data'] for row in audit.get('master_registry', [])}
        for name, key in MASTER.items():
            val = registry.get(key)
            values['audit.' + name] = result_features(val, val.get('status', 'COMPLETE') if isinstance(val, dict) else 'COMPLETE')
    if mesh:
        for name, key in MESH.items():
            values['mesh.' + name] = result_features(mesh.get(key) if key else mesh)
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            pass
    if isinstance(payload, dict) and 'host_memory' in payload and (payload.get('mode') == 'LIVE'):
        telemetry = [payload.get('host_cpu'), payload.get('host_memory'), payload.get('total_processes')]
        telemetry += [payload.get('counts', {}).get(k) for k in ('python', 'java', 'opera')]
        values['activity.HostTelemetry'] = ([math.tanh(v / (100 if i < 2 else 50)) if isinstance(v, (float, int)) else 0 for i, v in enumerate(telemetry)], [isinstance(v, (float, int)) for v in telemetry])
    texts = []

    def content(item):
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, list):
            for entry in item:
                content(entry)
        elif isinstance(item, dict):
            for key in ('text', 'summary', 'title', 'raw_input', 'raw_output', 'prompt', 'response', 'article'):
                if key in item:
                    content(item[key])
    content(payload)
    vector = [0.0] * 16
    for text in texts:
        for match in re.finditer('\\b[a-zA-Z]{3,}\\b', text):
            word = match[0].lower()
            digest = hashlib.blake2b(word.encode(), digest_size=2).digest()
            vector[digest[0] % 16] += 1 if digest[1] % 2 else -1
    norm = max(1, math.sqrt(sum((v * v for v in vector))))
    values['input.TextPatterns'] = ([v / norm for v in vector], [bool(texts)] * 16)
    x = []
    mask = []
    for name, size in GROUPS:
        a, b = values.get(name, ([0.0] * size, [False] * size))
        x.extend(a)
        mask.extend(b)
        if any(b):
            observed.append(name)
    return (x, mask, observed)
