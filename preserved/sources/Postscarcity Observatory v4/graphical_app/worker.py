"""Execute one original module in a bounded child process and collect its results."""
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import traceback
from elevation import VIRTUE_RULES
from code_archetypes import LIBRARY
from predictive_rules import CONTRACT
from module_reasoning import ModuleReasoning

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP / 'vendor'))

def clean(value, depth=0):
    if depth > 7: return str(value)[:500]
    if value is None or isinstance(value, (str, int, float, bool)): return value
    if isinstance(value, dict): return {str(k): clean(v, depth+1) for k,v in value.items()}
    if isinstance(value, (list, tuple, set)): return [clean(v, depth+1) for v in value]
    return str(value)[:500]

def run(path, overrides=None, sources=None, definitions=None, runtime=None, predictive=None, primary=None):
    LIBRARY.register_derived(definitions or {})
    source = path.read_text(encoding='utf-8-sig')
    tree = ast.parse(source, str(path))
    overrides = overrides or {}
    applied = set()
    # Only declared top-level input dictionaries may be replaced. Method bodies are untouched.
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in overrides:
                original = ast.literal_eval(node.value)
                if not isinstance(original, dict) or not isinstance(overrides[name], dict):
                    raise ValueError('Input overrides must be dictionaries')
                node.value = ast.parse(repr(overrides[name]), mode='eval').body
                applied.add(name)
    if applied != set(overrides): raise ValueError('Unknown input dictionary')
    ast.fix_missing_locations(tree)
    reasoning=ModuleReasoning(path.stem,source,tree,predictive)
    namespace = {'__name__':'__main__', '__file__':str(path), 'OBSERVATORY_SOURCES':sources or [],
        'OBSERVATORY_CODE_ARCHETYPES':LIBRARY, 'OBSERVATORY_PREDICTIVE':predictive or {}, 'OBSERVATORY_PREDICTIVE_CONTRACT':CONTRACT,
        'OBSERVATORY_REASONING':reasoning,
        'OBSERVATORY_PRIMARY_CASCADE':primary or {},
        'OBSERVATORY_DEFINITIONS':definitions or {}, 'OBSERVATORY_RUNTIME':runtime or {}, 'OBSERVATORY_POLICY':VIRTUE_RULES}
    sys.path.insert(0, str(path.parent))
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        exec(compile(tree, str(path), 'exec'), namespace)
    reports, objects = {}, {}
    # Only named outputs survive; loop-local names and imported modules do not become reports.
    assigned = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id not in assigned: assigned.append(target.id)
    for name in assigned:
        value = namespace.get(name)
        if isinstance(value, (dict, list, tuple, bool, int, float, str)):
            reports[name] = clean(value)
        elif hasattr(value, '__dict__') and value.__class__.__module__ == '__main__':
            objects[name] = {k:clean(v) for k,v in vars(value).items()
                if isinstance(v, (dict,list,tuple,bool,int,float,str))}
    return {'reports': reports, 'objects':objects, 'stdout':output.getvalue()[-32000:], 'policy':VIRTUE_RULES,
        'pid':os.getpid(), 'overrides':overrides, 'code_archetypes':LIBRARY.inspect(source), 'predictive_contract':CONTRACT,
        'source_context':sources or [],
        'functional_reasoning':reasoning.report(reports),
        'definition_context':{'calls_supplied':len(definitions or {}),'documented':sum(bool(d.get('definition')) for d in (definitions or {}).values()),
            'definitions':definitions or {}}}

if __name__ == '__main__':
    try:
        request = json.load(sys.stdin)
        from privacy_network import install_worker
        install_worker(request.get("privacy",{}))
        result = run(Path(request['path']), request.get('inputs'), request.get('sources'), request.get('definitions'),request.get('runtime'),request.get('predictive'),request.get('primary_cascade'))
        print(json.dumps({'ok':True, **result,'primary_cascade':request.get('primary_cascade')}, ensure_ascii=True, allow_nan=False))
    except BaseException as exc:
        print(json.dumps({'ok':False,'error':str(exc),'traceback':traceback.format_exc()}))
