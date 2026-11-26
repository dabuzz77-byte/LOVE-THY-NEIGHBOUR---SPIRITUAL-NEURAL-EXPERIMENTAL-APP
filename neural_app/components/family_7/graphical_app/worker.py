"""Execute a fixed catalogue calculation inside the shared process."""
import ast
import builtins,importlib
from neural_app import capture_output as contextlib
import io
import json
import os
from pathlib import Path
import sys
import traceback,types,time
from ..graphical_app.elevation import VIRTUE_RULES
from ..graphical_app.code_archetypes import LIBRARY
from ..graphical_app.predictive_rules import CONTRACT
from ..graphical_app.module_reasoning import ModuleReasoning
APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP / 'vendor'))

def clean(value, depth=0):
    if depth > 7:
        return str(value)[:500]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): clean(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [clean(v, depth + 1) for v in value]
    return str(value)[:500]

def run(path, overrides=None, sources=None, definitions=None, runtime=None, predictive=None, primary=None):
    LIBRARY.register_derived(definitions or {})
    source = path.read_text(encoding='utf-8-sig')
    tree = ast.parse(source, str(path))
    if path.stem in ('observatory_background_worker','observatory_background_worker2'):
        class SharedCycle(ast.NodeTransformer):
            def visit_While(self,node):
                self.generic_visit(node)
                return ast.copy_location(ast.For(target=ast.Name(id='_shared_cycle',ctx=ast.Store()),iter=ast.Call(func=ast.Name(id='range',ctx=ast.Load()),args=[ast.Constant(1)],keywords=[]),body=node.body,orelse=node.orelse),node)
            def visit_Await(self,node):
                self.generic_visit(node)
                if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='sleep':node.value.args=[ast.Constant(0)]
                return node
        tree=SharedCycle().visit(tree)
    overrides = overrides or {}
    applied = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in overrides:
                original = ast.literal_eval(node.value)
                if not isinstance(original, dict) or not isinstance(overrides[name], dict):
                    raise ValueError('Input overrides must be dictionaries')
                node.value = ast.parse(repr(overrides[name]), mode='eval').body
                applied.add(name)
    if applied != set(overrides):
        raise ValueError('Unknown input dictionary')
    ast.fix_missing_locations(tree)
    reasoning = ModuleReasoning(path.stem, source, tree, predictive)
    namespace = {'__name__': '__main__', '__file__': str(path), '__package__':__package__, 'OBSERVATORY_SOURCES': sources or [], 'OBSERVATORY_CODE_ARCHETYPES': LIBRARY, 'OBSERVATORY_PREDICTIVE': predictive or {}, 'OBSERVATORY_PREDICTIVE_CONTRACT': CONTRACT, 'OBSERVATORY_REASONING': reasoning, 'OBSERVATORY_PRIMARY_CASCADE': primary or {}, 'OBSERVATORY_DEFINITIONS': definitions or {}, 'OBSERVATORY_RUNTIME': runtime or {}, 'OBSERVATORY_POLICY': VIRTUE_RULES}
    from neural_app.observatory_reads import read as public_read
    import urllib.request as original_request
    observations=[];local_logs=[]
    request_proxy=types.SimpleNamespace(Request=original_request.Request,urlopen=lambda request,**kw:public_read(request,observations=observations,**kw))
    def shared_import(name,globals=None,locals=None,fromlist=(),level=0):
        if level==0 and name=='urllib.request':
            return request_proxy if fromlist else types.SimpleNamespace(request=request_proxy)
        if level==0 and (name=='graphical_app' or name.startswith('graphical_app.')):
            translated=__package__+name[len('graphical_app'):]
            result=importlib.import_module(translated)
            return result if fromlist else importlib.import_module(__package__)
        if level==0 and (APP/(name.split('.')[0]+'.py')).is_file():
            result=importlib.import_module(__package__+'.'+name)
            return result if fromlist else importlib.import_module(__package__+'.'+name.split('.')[0])
        return builtins.__import__(name,globals,locals,fromlist,level)
    class LocalLog(io.StringIO):
        def close(self):
            if not self.closed:local_logs.append(self.getvalue()[-16000:])
            super().close()
    def local_open(file,mode='r',*args,**kwargs):
        if path.stem in ('observatory_background_worker','observatory_background_worker2') and any(c in mode for c in 'wax+'):
            return LocalLog()
        return builtins.open(file,mode,*args,**kwargs)
    namespace['__builtins__']={**vars(builtins),'__import__':shared_import,'open':local_open}
    if str(path.parent) not in sys.path:sys.path.insert(0, str(path.parent))
    output = io.StringIO()
    previous_trace=sys.gettrace();line_count=0;deadline=time.monotonic()+15
    def bounded_trace(frame,event,arg):
        nonlocal line_count
        if event=='line' and frame.f_code.co_filename==str(path):
            line_count+=1
            if line_count>200000 or time.monotonic()>deadline:raise TimeoutError('Catalogue calculation exceeded its bounded processing step')
        return bounded_trace if frame.f_code.co_filename==str(path) else None
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            sys.settrace(bounded_trace)
            exec(compile(tree, str(path), 'exec'), namespace)
    finally:
        sys.settrace(previous_trace)
        sys.path[:]=list(dict.fromkeys(sys.path))
    reports, objects = ({}, {})
    assigned = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id not in assigned:
                    assigned.append(target.id)
    for name in assigned:
        value = namespace.get(name)
        if isinstance(value, (dict, list, tuple, bool, int, float, str)):
            reports[name] = clean(value)
        elif hasattr(value, '__dict__') and value.__class__.__module__ == '__main__':
            objects[name] = {k: clean(v) for k, v in vars(value).items() if isinstance(v, (dict, list, tuple, bool, int, float, str))}
    return {'reports': reports, 'objects': objects, 'stdout': output.getvalue()[-32000:], 'network_observations':observations,'captured_local_logs':local_logs,'executed_lines':line_count,'policy': VIRTUE_RULES, 'pid': os.getpid(), 'overrides': overrides, 'code_archetypes': LIBRARY.inspect(source), 'predictive_contract': CONTRACT, 'source_context': sources or [], 'functional_reasoning': reasoning.report(reports), 'definition_context': {'calls_supplied': len(definitions or {}), 'documented': sum((bool(d.get('definition')) for d in (definitions or {}).values())), 'definitions': definitions or {}}}
