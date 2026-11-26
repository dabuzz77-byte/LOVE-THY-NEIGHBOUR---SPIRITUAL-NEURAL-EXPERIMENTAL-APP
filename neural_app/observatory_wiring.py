"""Reviewed catalogue inputs and a staggered shared-process execution policy."""
import hashlib
import json
from pathlib import Path

MANIFEST=Path(__file__).resolve().parents[1]/'references/observatory-wiring.json'

def reviewed_modules(section):
    rows=json.loads(MANIFEST.read_text(encoding='utf-8'))['modules']
    approved=[]
    for row in rows:
        name=row['id']
        if name not in section.modules:continue
        source=section.root/section.modules[name]['file']
        try:digest=hashlib.sha256(source.read_bytes()).hexdigest()
        except OSError:continue
        if digest==row['sha256']:approved.append(name)
    return tuple(approved)

def automatic_inputs(section,name):
    """Use measured app state; never invent personal finances or resource stocks."""
    with section.lock:
        nodes=list(section.nodes.values())[:32]
        values=[float(n.get('activation',0)) for n in nodes]
        weights=[min(1.,abs(float(n.get('weight',0)))) for n in nodes]
        pulse=section.pulses
    snapshot={'pulse':pulse,'output':section.neural_output,'module_count':len(section.modules)}
    text=json.dumps(snapshot,separators=(',',':'))
    payload=None
    if name in ('elevated/TranslationStudio','elevated/TransformerMatrix','elevated/SifterRegistry'):
        payload={'text':text}
    elif name=='elevated/ConvergenceEngine' and values:
        payload={'velocities':values,'dimension_range':len(values)}
    elif name=='elevated/TelemetryProbability' and any(abs(v)>1e-12 for v in values):
        payload={'values':values}
    elif name=='expanded/BalancedTernaryMatrix' and values:
        a=[0 if abs(v)<.01 else 1 if v>0 else -1 for v in values]
        payload={'a':a,'b':list(reversed(a))}
    elif name=='expanded/SourceWeightOptimizer' and values:
        payload={'current':weights,'target':[min(1.,abs(v)) for v in values],'rate':.05}
    return {'inputs':{'payload':payload}} if payload is not None else None

def outcome(result):
    """Expose waiting states without confusing them with failed execution."""
    reports=result.get('reports',{})
    values=[v for v in reports.values() if isinstance(v,dict)]
    pending=[v.get('status','') for v in values if str(v.get('status','')).lower().startswith(('awaiting','waiting'))]
    return 'awaiting input' if pending else 'complete'
