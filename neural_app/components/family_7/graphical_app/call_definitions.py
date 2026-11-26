"""Every module call mapped to original code or official library documentation."""
import ast
import builtins
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
from neural_app import section_threads as threading
import time
import urllib.parse
import urllib.request
from ..graphical_app.privacy_network import urlopen
from ..graphical_app.sources import now, save_json
PYDOC = 'https://docs.python.org/3.12/'
METHODS = {'get': ('dict.get', 'stdtypes.html'), 'items': ('dict.items', 'stdtypes.html'), 'values': ('dict.values', 'stdtypes.html'), 'append': ('list.append', 'tutorial/datastructures.html'), 'lower': ('str.lower', 'stdtypes.html'), 'strip': ('str.strip', 'stdtypes.html'), 'split': ('str.split', 'stdtypes.html'), 'replace': ('str.replace', 'stdtypes.html'), 'isoformat': ('datetime.datetime.isoformat', 'datetime.html'), 'total_seconds': ('datetime.timedelta.total_seconds', 'datetime.html'), 'findall': ('xml.etree.ElementTree.Element.findall', 'xml.etree.elementtree.html'), 'find': ('xml.etree.ElementTree.Element.find', 'xml.etree.elementtree.html'), 'read': ('http.client.HTTPResponse.read', 'http.client.html'), 'memory_info': ('psutil.Process.memory_info', 'psutil')}
for method in ('join', 'upper', 'startswith', 'endswith', 'casefold', 'encode', 'removeprefix', 'isalnum', 'isascii', 'lstrip', 'rstrip', 'splitlines'):
    METHODS[method] = ('str.' + method, 'stdtypes.html')
for method in ('decode', 'hex', 'fromhex'):
    METHODS[method] = ('bytes.' + method, 'stdtypes.html')
for method in ('update', 'setdefault', 'fromkeys', 'keys'):
    METHODS[method] = ('dict.' + method, 'stdtypes.html')
for method in ('extend', 'reverse', 'sort'):
    METHODS[method] = ('list.' + method, 'stdtypes.html')
for method in ('discard', 'issubset', 'issuperset'):
    METHODS[method] = ('set.' + method, 'stdtypes.html')
for method in ('resolve', 'read_text', 'read_bytes', 'write_text', 'write_bytes', 'relative_to', 'is_relative_to', 'is_file', 'is_dir', 'is_symlink', 'mkdir', 'glob', 'rglob', 'open', 'with_suffix', 'as_posix', 'expanduser', 'stat'):
    METHODS[method] = ('pathlib.Path.' + method, 'pathlib.html')
for method in ('is_set', 'wait', 'set', 'clear'):
    METHODS[method] = ('threading.Event.' + method, 'threading.html')
for method in ('execute', 'executemany', 'commit', 'rollback'):
    METHODS[method] = ('sqlite3.Connection.' + method, 'sqlite3.html')
for method in ('fetchone', 'fetchall'):
    METHODS[method] = ('sqlite3.Cursor.' + method, 'sqlite3.html')
for method in ('is_finite', 'quantize'):
    METHODS[method] = ('decimal.Decimal.' + method, 'decimal.html')
for method in ('getheader', 'getheaders', 'getcode'):
    METHODS[method] = ('http.client.HTTPResponse.' + method, 'http.client.html')

class DocSections(HTMLParser):
    """Capture each official reference anchor and its associated definition."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = {}
        self.current = None
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ('script', 'style'):
            self.hidden += 1
        if values.get('id'):
            previous = self.sections.get(self.current)
            self.current = values['id']
            self.sections.setdefault(self.current, previous if previous is not None and (not ''.join(previous).strip()) else [])

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, value):
        if self.current and (not self.hidden):
            self.sections[self.current].append(value)

    def result(self):
        return {key: ' '.join(' '.join(parts).split())[:4000] for key, parts in self.sections.items()}

def receiver_types(tree, classes, imports):
    """Resolve declared/constructed receivers without importing or running module code."""
    result = {}

    class Resolver(ast.NodeVisitor):

        def __init__(self):
            self.bindings = {}
            self.owner = None

        def annotation(self, node):
            if isinstance(node, ast.Subscript):
                return self.annotation(node.value)
            if node is None:
                return None
            name = ast.unparse(node)
            return {'List': 'list', 'Dict': 'dict', 'Set': 'set', 'Tuple': 'tuple'}.get(name, imports.get(name, name))

        def value_type(self, node):
            if isinstance(node, (ast.List, ast.ListComp)):
                return 'list'
            if isinstance(node, (ast.Dict, ast.DictComp)):
                return 'dict'
            if isinstance(node, (ast.Set, ast.SetComp)):
                return 'set'
            if isinstance(node, ast.Constant):
                return type(node.value).__name__
            if isinstance(node, (ast.Name, ast.Attribute)):
                return self.bindings.get(ast.unparse(node))
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name in ('list', 'dict', 'set', 'tuple', 'str', 'bytes'):
                    return name
                if name in classes:
                    return name
                if name in imports and name[:1].isupper():
                    return imports[name]
                if name == 'logging.getLogger':
                    return 'logging.Logger'
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'copy':
                    return self.value_type(node.func.value)
            return None

        def visit_ClassDef(self, node):
            previous, owner = (self.bindings, self.owner)
            self.bindings = dict(previous)
            self.bindings['self'] = node.name
            self.owner = node.name
            for item in sorted(node.body, key=lambda n: not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == '__init__')):
                self.visit(item)
            self.bindings, self.owner = (previous, owner)

        def visit_FunctionDef(self, node):
            previous = self.bindings
            self.bindings = dict(previous)
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                if arg.arg != 'self':
                    self.bindings[arg.arg] = self.annotation(arg.annotation)
            self.generic_visit(node)
            if self.owner and node.name == '__init__':
                previous.update({k: v for k, v in self.bindings.items() if k.startswith('self.')})
            self.bindings = previous
        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Assign(self, node):
            self.generic_visit(node)
            for target in node.targets:
                if isinstance(target, (ast.Name, ast.Attribute)):
                    self.bindings[ast.unparse(target)] = self.value_type(node.value)

        def visit_AnnAssign(self, node):
            self.generic_visit(node)
            if isinstance(node.target, (ast.Name, ast.Attribute)):
                self.bindings[ast.unparse(node.target)] = self.annotation(node.annotation) or self.value_type(node.value)

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                owner = self.value_type(node.func.value)
                if owner:
                    result[id(node)] = owner + '.' + node.func.attr
            self.generic_visit(node)
    Resolver().visit(tree)
    return result

def inventory(path, module, source=None, tree=None):
    if source is None:
        source = path.read_text(encoding='utf-8-sig')
    if tree is None:
        tree = ast.parse(source, filename=str(path))
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    methods = {}
    for cls in classes.values():
        for n in cls.body:
            if isinstance(n, ast.FunctionDef):
                methods.setdefault(n.name, []).append((cls.name + '.' + n.name, n))
    imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split('.')[0]] = alias.name if alias.asname else alias.name.split('.')[0]
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports[alias.asname or alias.name] = (node.module or '') + '.' + alias.name
    receivers = receiver_types(tree, classes, imports)
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        expression = ast.unparse(node.func)
        leaf = node.func.attr if isinstance(node.func, ast.Attribute) else expression
        local = functions.get(expression) or classes.get(expression)
        qualified = expression
        kind = 'unresolved'
        definition = ''
        url = ''
        resolution = 'unresolved'
        if local is None and len(methods.get(leaf, [])) == 1:
            qualified, local = methods[leaf][0]
        if local is not None:
            kind = 'local'
            resolution = 'source definition'
            definition = (ast.get_docstring(local) or 'Original project implementation.') + '\n' + ast.get_source_segment(source, local)[:2200]
            url = PYDOC + ('tutorial/classes.html' if isinstance(local, ast.ClassDef) else 'tutorial/controlflow.html#defining-functions')
        elif isinstance(node.func, ast.Name) and callable(getattr(builtins, expression, None)):
            kind = 'builtin'
            qualified = expression
            resolution = 'Python built-in'
            definition = getattr(builtins, expression).__doc__ or expression
            url = PYDOC + 'library/' + ('exceptions.html#' + expression if expression.endswith('Error') else 'functions.html#' + ('func-dict' if expression == 'dict' else expression))
        elif expression.startswith('re.'):
            qualified = expression
            kind = 'library'
            resolution = 'imported regular-expression function'
            url = PYDOC + 'library/re.html#' + qualified
        elif leaf in METHODS:
            qualified, page = METHODS[leaf]
            kind = 'library'
            resolution = 'method reference (receiver checked at execution)'
            url = 'https://psutil.readthedocs.io/stable/#' + qualified if page == 'psutil' else PYDOC + ('' if page.startswith('tutorial/') else 'library/') + page + '#' + ('tut-morelists' if qualified == 'list.append' else qualified)
        else:
            prefix = expression.split('.')[0]
            if prefix in imports:
                qualified = imports[prefix] + expression[len(prefix):]
                kind = 'library'
                resolution = 'imported library'
                if qualified.startswith('psutil.'):
                    url = 'https://psutil.readthedocs.io/stable/#' + qualified
                elif qualified.startswith('numpy.'):
                    if '(' in qualified and leaf in ('reshape', 'all'):
                        qualified = 'numpy.ndarray.' + leaf
                    if qualified == 'numpy.abs':
                        qualified = 'numpy.absolute'
                    url = 'https://numpy.org/doc/stable/reference/random/generator.html#numpy.random.default_rng' if qualified == 'numpy.random.default_rng' else 'https://numpy.org/doc/stable/reference/' + ('random/' if qualified.startswith('numpy.random.') else '') + 'generated/' + qualified + '.html'
                elif qualified.startswith('pynvml.'):
                    url = 'https://pypi.org/project/nvidia-ml-py/#description'
                    definition = 'Optional NVIDIA NVML Python binding ' + qualified + '. Requires nvidia-ml-py, an NVIDIA driver and compatible hardware. This source catches unavailable NVML and reports missing GPU readings instead of inventing them.'
                else:
                    library = 'urllib.request' if qualified.startswith('urllib.request.') else 'xml.etree.elementtree' if qualified.startswith('xml.etree.ElementTree.') else qualified.split('.')[0]
                    url = PYDOC + 'library/' + library + '.html#' + qualified
        receiver = receivers.get(id(node))
        if receiver:
            owner, _, method = receiver.rpartition('.')
            target = next((n for n in classes.get(owner, ast.Module(body=[], type_ignores=[])).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method), None)
            if target is not None:
                qualified = receiver
                kind = 'local'
                resolution = 'Declared receiver source definition'
                definition = (ast.get_docstring(target) or 'Original project method.') + '\n' + (ast.get_source_segment(source, target) or '')[:2200]
                url = PYDOC + 'tutorial/classes.html'
            elif owner in ('list', 'dict', 'set', 'str', 'bytes', 'tuple'):
                obj = getattr(getattr(builtins, owner), method, None)
                if callable(obj):
                    qualified = receiver
                    kind = 'library'
                    resolution = 'Declared receiver library definition'
                    definition = obj.__doc__ or ''
                    url = PYDOC + 'library/stdtypes.html#' + receiver
            elif owner == 'logging.Logger':
                qualified = receiver
                kind = 'library'
                resolution = 'logging.getLogger return type'
                definition = ''
                url = PYDOC + 'library/logging.html#' + receiver
            elif '.' in owner:
                qualified = receiver
                kind = 'library'
                resolution = 'Constructed imported receiver; project lookup pending'
                definition = ''
                url = ''
        result.append({'id': module + ':' + str(node.lineno) + ':' + str(node.col_offset), 'module': module, 'line': node.lineno, 'expression': expression, 'qualified': qualified, 'kind': kind, 'resolution': resolution, 'local_definition': definition[:2600], 'url': url})
    return sorted(result, key=lambda item: (item['line'], item['id']))

class CallDefinitions:

    def __init__(self, runtime):
        self.rt = runtime
        self.lock = threading.RLock()
        self.path = runtime.data / 'call-definitions.json'
        try:
            self.pages = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            try:
                self.pages = json.loads((Path(__file__).parent / 'reference' / 'call-pages.json').read_text(encoding='utf-8'))
            except (OSError, ValueError):
                self.pages = {}
        try:
            seeds = json.loads((Path(__file__).parent / 'reference' / 'foundation-call-pages.json').read_text(encoding='utf-8'))
            for url, page in seeds.items():
                current = self.pages.get(url, {})
                if current.get('status') != 'ready' or str(current.get('retrieved') or '') < str(page.get('retrieved') or ''):
                    self.pages[url] = page
        except (OSError, ValueError):
            pass
        self.calls = []
        self.hashes = {}
        self.scan_errors = {}
        self.feedback = {}
        self.last_scan = None
        self.scan()

    @staticmethod
    def source_digest(path):
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None

    def scan(self):
        records = []
        project = {}
        project_files = {}
        method_index = {}
        hashes = {}
        errors = {}
        parsed = {}
        app = Path(__file__).parent
        paths = {'graphical_app/' + p.stem: p for p in app.glob('*.py')}
        paths.update({m['id']: self.rt.root / m['file'] for m in self.rt.modules.values()})
        for name, path in paths.items():
            hashes[name] = None
            try:
                raw = path.read_bytes()
                hashes[name] = hashlib.sha256(raw).hexdigest()
                source = raw.decode('utf-8-sig')
                tree = ast.parse(source, filename=str(path))
            except (OSError, UnicodeError, SyntaxError) as exc:
                errors[name] = str(exc)
                continue
            parsed[name] = (path, source, tree)
            project_files[path.stem] = path
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    project[path.stem + '.' + node.name] = (ast.get_docstring(node) or 'Project source definition.') + '\n' + (ast.get_source_segment(source, node) or '')[:2400]
                    if isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                method_index[path.stem + '.' + node.name + '.' + method.name] = (ast.get_docstring(method) or 'Project method implementation.') + '\n' + (ast.get_source_segment(source, method) or '')[:2400]
        for name, (path, source, tree) in parsed.items():
            records.extend(inventory(path, name, source=source, tree=tree))
        project.update(method_index)
        receivers = {'self.rt': 'app.Runtime', 'runtime': 'app.Runtime', 'self.rt.binary_bus': 'chiral.BinaryChiralBus', 'self.binary_bus': 'chiral.BinaryChiralBus', 'self.rt.chiral': 'chiral.ChiralGenerator', 'self.chiral': 'chiral.ChiralGenerator', 'self.rt.model_hub': 'models.ModelHub', 'self.rt.source_hub': 'sources.SourceHub', 'self.rt.workbench': 'workbench.Workbench', 'self.rt.call_definitions': 'call_definitions.CallDefinitions', 'self.rt.screen_hub': 'screen.ScreenHub', 'self.rt.interpreter': 'interpreter.Interpreter', 'self.rt.field_voice': 'field_voice.FieldVoice', 'self.rt.v3': 'v3_hub.V3Hub', 'self.v3': 'v3_hub.V3Hub', 'self.v3.wav': 'wav_modulator.WavModulator', 'self.wav': 'wav_modulator.WavModulator', 'self.core': 'ported_core.CoreEngine', 'self.hub': 'v3_hub.V3Hub', 'self.hub.knowledge': 'local_knowledge.LocalKnowledge', 'self.journal': 'ported_core.Journal', 'self.rt.resources': 'resource_ledger.ResourceLedger', 'self.resources': 'resource_ledger.ResourceLedger', 'self.rt.watch': 'opportunity_watch.OpportunityWatch', 'self.watch': 'opportunity_watch.OpportunityWatch', 'self.rt.python': 'python_hub.PythonHub', 'self.python': 'python_hub.PythonHub', 'self.model': 'classifier_core.TotalBitRealityEngine', 'self.sampler': 'ambient_runtime.SystemActivitySampler', 'self.rt.privacy': 'privacy_network.PrivacyNetwork', 'self.privacy': 'privacy_network.PrivacyNetwork', 'self.rt.pathway': 'web_pathway.WebPathway', 'self.pathway': 'web_pathway.WebPathway', 'self.rt.inference': 'inference_engine.InferenceEngine', 'self.inference': 'inference_engine.InferenceEngine', 'self.rt.flux': 'flux_hub.FluxHub', 'self.flux': 'flux_hub.FluxHub'}
        for call in records:
            receiver, _, method = call['expression'].rpartition('.')
            target = receivers.get(receiver, '') + '.' + method
            if target in project:
                call['qualified'] = target
            expression = call['expression']
            if expression.startswith('hashlib.') and method in ('hexdigest', 'digest'):
                call.update(kind='library', qualified='hash.' + method, url=PYDOC + 'library/hashlib.html#hash.' + method, local_definition=getattr(hashlib.sha256(), method).__doc__)
            elif expression == 'ctypes.windll.kernel32.GetSystemTimes':
                call.update(kind='library', qualified='Win32.GetSystemTimes', resolution='Documented Win32 API through ctypes', url='https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes#syntax', local_definition='GetSystemTimes writes cumulative idle, kernel and user CPU times into FILETIME structures supplied by pointer. Kernel time includes idle time. Returns nonzero on success, zero on failure; GetLastError supplies error information. The original sampler computes usage from differences between successful readings.')
            elif expression == 'ctypes.windll.kernel32.GlobalMemoryStatusEx':
                call.update(kind='library', qualified='Win32.GlobalMemoryStatusEx', resolution='Documented Win32 API through ctypes', url='https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex#syntax', local_definition='GlobalMemoryStatusEx accepts a pointer to MEMORYSTATUSEX with dwLength set to the structure size. It fills physical and virtual memory availability and memory-load fields. Returns nonzero on success, zero on failure; GetLastError supplies error information. Values describe the system at the measurement time.')
            elif expression.startswith('threading.Thread(') and expression.endswith('.start'):
                call.update(kind='library', qualified='threading.Thread.start', url=PYDOC + 'library/threading.html#threading.Thread.start')
            elif expression.startswith('re.sub(') and method in ('replace', 'strip'):
                call.update(kind='library', qualified='str.' + method, url=PYDOC + 'library/stdtypes.html#str.' + method)
            elif expression == 'sys.path.insert':
                call.update(kind='library', qualified='list.insert', url=PYDOC + 'tutorial/datastructures.html')
            qualified = call['qualified']
            if qualified.startswith('numpy.'):
                import numpy
                obj = numpy
                try:
                    for member in qualified.split('.')[1:]:
                        obj = getattr(obj, member)
                    call['local_definition'] = (getattr(obj, '__doc__', '') or '')[:2600]
                except AttributeError:
                    pass
            if qualified.startswith('pathlib.Path.') and method in ('as_posix', 'is_relative_to', 'relative_to', 'with_suffix'):
                qualified = qualified.replace('pathlib.Path.', 'pathlib.PurePath.')
                call.update(qualified=qualified, url=PYDOC + 'library/pathlib.html#' + qualified)
            owner, _, attribute = qualified.partition('.')
            if owner in ('str', 'bytes', 'dict', 'list', 'set', 'int', 'float') and attribute:
                obj = getattr(getattr(builtins, owner), attribute, None)
                if callable(obj):
                    call['local_definition'] = obj.__doc__ or ''
            if qualified in project:
                call.update(kind='local', resolution='Imported Python project definition', local_definition=project[qualified], url=PYDOC + 'tutorial/controlflow.html#defining-functions')
            elif qualified.split('.')[0] in project_files and call['kind'] == 'library':
                call.update(kind='unresolved', resolution='Project member needs receiver resolution', url='')
            elif call['kind'] == 'library':
                for library in ('concurrent.futures', 'http.server', 'http.client', 'html.parser', 'urllib.parse', 'urllib.error', 'urllib.request', 'os.path', 'xml.etree.ElementTree'):
                    if qualified.startswith(library + '.'):
                        call['url'] = PYDOC + 'library/' + library.lower() + '.html#' + qualified
                        break
            if call['kind'] == 'unresolved':
                call.update(resolution='Dynamic call; receiver resolved at execution', url=PYDOC + 'reference/datamodel.html#emulating-callable-objects')
        with self.lock:
            self.calls = records
            self.hashes = hashes
            self.scan_errors = errors
            self.last_scan = now()
            referenced = {urllib.parse.urldefrag(c['url'])[0] for c in records if c['url']}
            self.pages = {url: page for url, page in self.pages.items() if url in referenced}
            for call in records:
                if call['url']:
                    url = urllib.parse.urldefrag(call['url'])[0]
                    self.pages.setdefault(url, {'url': url, 'status': 'pending', 'next_fetch': 0, 'attempts': 0, 'sections': {}, 'retrieved': None, 'error': None})
        for call in records:
            key = 'call-definition:' + call['qualified'] if call['kind'] != 'local' else 'call-definition:' + call['module'] + ':' + call['qualified']
            call['node'] = key
            with self.rt.lock:
                node = self.rt.node(key, call['qualified'], 'definition')
                if call['module'] in self.rt.modules:
                    self.rt.edges.setdefault(key + '|module:' + call['module'], 0.1)
                value = 1 if self.definition(call)['text'] else 0
                node.update(input=value, activation=math.tanh(value * node['weight']), updates=node['updates'] + 1)
        self.rt.activate('carrier', 1)

    def definition(self, call):
        page = self.pages.get(urllib.parse.urldefrag(call['url'])[0], {})
        anchor = urllib.parse.urldefrag(call['url'])[1]
        sections = page.get('sections', {})
        text = sections.get(anchor, '') if anchor else ''
        if not text and call['kind'] == 'local':
            text = sections.get('defining-functions', '') or sections.get('a-first-look-at-classes', '')
        return {'text': call['local_definition'] or text, 'web_text': text, 'web_status': page.get('status', 'unresolved'), 'retrieved': page.get('retrieved'), 'error': page.get('error'), 'url': call['url']}

    def view(self):
        with self.lock:
            calls = [{**call, **self.definition(call)} for call in self.calls]
            return {'calls': calls, 'call_sites': len(calls), 'modules': len(self.rt.modules), 'last_scan': self.last_scan, 'source_errors': dict(self.scan_errors), 'local_or_documented': sum((bool(call['text']) for call in calls)), 'unresolved': sum((call['kind'] == 'unresolved' for call in calls)), 'runtime_call_sites': sum((c['module'].startswith('graphical_app/') for c in calls)), 'web_pages_ready': sum((p['status'] == 'ready' for p in self.pages.values())), 'web_pages_total': len(self.pages), 'feedback': self.feedback, 'automatic': self.rt.config['ingestion']}

    def context(self, module):
        with self.lock:
            output = {}
            for call in self.calls:
                if call['module'] != module:
                    continue
                definition = self.definition(call)
                output[call['expression']] = {'definition': definition['text'][:1000], 'url': definition['url'], 'retrieved': definition['retrieved'], 'resolution': call['resolution']}
            return output

    def feedback_from(self, module, result):
        with self.lock:
            self.feedback[module] = {'time': now(), 'ok': bool(result.get('ok')), 'error': str(result.get('error', ''))[:500]}
            if not result.get('ok'):
                for call in self.calls:
                    if call['module'] == module and call['url']:
                        page = self.pages[urllib.parse.urldefrag(call['url'])[0]]
                        if page['status'] != 'ready':
                            page['next_fetch'] = min(page['next_fetch'], time.time() + 15)

    def fetch(self, url):
        request = urllib.request.Request(url, headers={'User-Agent': 'PostscarcityObservatory/2.0 (API definition lookup)'})
        with urlopen(request, timeout=45) as response:
            raw = response.read(3 * 1024 * 1024 + 1)
            charset = response.headers.get_content_charset() or 'utf-8'
            if len(raw) > 3 * 1024 * 1024:
                raise ValueError('Documentation page exceeds 3 MB')
        parser = DocSections()
        parser.feed(raw.decode(charset, errors='replace'))
        sections = parser.result()
        if not sections:
            raise ValueError('No documentation anchors were found')
        with self.lock:
            page = self.pages[url]
            page.update(sections=sections, status='ready', retrieved=now(), error=None, format=2, next_fetch=time.time() + self.rt.config['refresh_hours'] * 3600, attempts=page['attempts'] + 1)
            related = [call for call in self.calls if urllib.parse.urldefrag(call['url'])[0] == url]
            save_json(self.path, self.pages)
        for call in related:
            if self.definition(call)['text']:
                self.rt.activate(call['node'], 1)
        self.rt.binary_bus.feed('call-definitions', {'url': url, 'retrieved': page['retrieved'], 'sections': sections})
        self.rt.publish('call-definitions', {'url': url, 'status': 'ready', 'call_sites': len(related)})

    def loop(self):
        last_scan = 0
        for _shared_tick in range(1):
            try:
                if time.monotonic() - last_scan > 60:
                    current = {module['id']: self.source_digest(self.rt.root / module['file']) for module in self.rt.modules.values()}
                    current.update({'graphical_app/' + p.stem: self.source_digest(p) for p in Path(__file__).parent.glob('*.py')})
                    if current != self.hashes:
                        self.scan()
                    last_scan = time.monotonic()
                with self.lock:
                    page = next((p for p in self.pages.values() if p['next_fetch'] <= time.time()), None) if self.rt.config['ingestion'] and self.rt.privacy.ready() else None
                    if page:
                        page['status'] = 'fetching'
                if not page:
                    self.rt.stop.wait(1)
                    continue
                try:
                    self.fetch(page['url'])
                except Exception as exc:
                    with self.lock:
                        page['attempts'] += 1
                        page.update(status='retry', error=str(exc), next_fetch=time.time() + min(3600, 30 * 2 ** min(page['attempts'], 6)))
                        save_json(self.path, self.pages)
                self.rt.stop.wait(self.rt.config['ingest_seconds'])
            except Exception as exc:
                self.rt.publish('call-definitions', {'status': 'error', 'error': str(exc)[:500]})
                self.rt.stop.wait(15)
