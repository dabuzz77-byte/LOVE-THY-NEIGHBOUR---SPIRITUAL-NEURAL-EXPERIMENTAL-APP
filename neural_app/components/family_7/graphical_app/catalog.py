"""Source-derived inventory, with a visible account of each module's inputs."""
import ast
import hashlib
import os
import re
from pathlib import Path
ALIASES = {'BUDDHA_LAW': ['Gautama Buddha', 'Compassion', 'Avidya', 'Raga', 'Dvesha'], 'TESLA_LAW': ['Nikola Tesla', 'Energy', 'Scarcity'], 'TESLA_LEARNING': ['Nikola Tesla', 'Energy', 'Knowledge'], 'KRISHNA_LAW': ['Krishna', 'Dharma', 'Adharma'], 'FULLER_FRESCO_LAW': ['Buckminster Fuller', 'Jacque Fresco', 'Resource-based economy'], 'ROBIN_HOOD_VIRTUE': ['Robin Hood', 'Economic inequality'], 'LEDGER_JOKER_REFACTOR': ['Joker (The Dark Knight)', 'Greed'], 'REST_JUSTICE': ['Restorative justice', 'Rehabilitation (penology)']}
CONCEPTS = ['compassion', 'empathy', 'virtue', 'justice', 'rehabilitation', 'redemption', 'covenant', 'freedom', 'scarcity', 'abundance', 'greed', 'transparency', 'sustainability', 'resilience', 'equilibrium', 'invariant', 'repentance', 'forgiveness', 'Bodhi tree', "Jacob's Ladder", 'ternary logic', 'binary', 'neural network', 'Schumann resonances', 'autonomy', 'harmony', 'reciprocity', 'predation', 'altruism', 'restoration', 'integrity', 'discernment', 'protection', 'consciousness', 'truth', 'good and evil', 'sovereignty', 'malice', 'suffering', 'brotherhood', 'ego', 'Dharma', 'ahimsa']

def words(name):
    return re.sub('(?<=[a-z])(?=[A-Z])', ' ', name).replace('_', ' ')

def family(name):
    if any((x in name for x in ['Registry', 'UniversalVirtue'])):
        return 'Registry'
    if any((x in name for x in ['Covenant', 'ChinaDoll', 'Bodhi', 'Parental', 'Sovereign'])):
        return 'Covenant'
    if any((x in name for x in ['Safeguard', 'Enforcement', 'Integrity', 'protection', 'boundary'])):
        return 'Safeguard'
    if any((x in name for x in ['Telemetry', 'RealTime', 'Online', 'Probe', 'Trajectory', 'Observation', 'ingest'])):
        return 'Telemetry'
    if any((x in name for x in ['Compassion', 'Redempt', 'Repentance', 'Ethical', 'Cognition'])):
        return 'Restoration'
    return 'Logic'

def inspect_module(path):
    source = path.read_text(encoding='utf-8-sig')
    tree = ast.parse(source, str(path))
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    description = next((ast.get_docstring(n) for n in classes + functions if ast.get_docstring(n)), '')
    inputs, definitions, methods = ({}, {}, [])
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                value = ast.literal_eval(node.value)
                if isinstance(value, dict) and value:
                    inputs[node.targets[0].id] = value
            except (ValueError, TypeError):
                pass
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in ('definitions', 'virtue_matrix', 'weights'):
                    try:
                        value = ast.literal_eval(node.value)
                        if isinstance(value, dict):
                            definitions.update(value)
                    except (ValueError, TypeError):
                        pass
        if isinstance(node, ast.FunctionDef) and (not node.name.startswith('__')):
            methods.append({'name': node.name, 'description': ast.get_docstring(node) or ''})
    terms = set()
    for key in definitions:
        terms.update(ALIASES.get(key, [words(key).title()]))
    lower = source.lower()
    for concept in CONCEPTS:
        if concept.lower() in lower or (concept == 'Schumann resonances' and '7.83' in lower):
            terms.add(concept)
    live_host = 'psutil.' in source
    live_network = any((x in source for x in ('urlopen(', 'urlopen (', 'socket.create_connection(', 'requests.get(')))
    input_basis = 'Live host readings' if live_host else 'Rule calculation'
    if live_network:
        input_basis += ' + network requests'
    if inputs:
        input_basis += ' + declared inputs'
    if path.stem == 'verify_protection_rings':
        input_basis = 'Process identity + supplied ring evidence'
    if path.stem == 'UnifiedProbeAndStressEngine':
        input_basis += ' · scenario comparison'
    return {'id': path.stem, 'file': path.name, 'title': words(path.stem).replace(' Engine', ''), 'family': family(path.stem), 'description': description, 'methods': methods, 'inputs': inputs, 'definitions': definitions, 'terms': sorted(terms, key=str.lower), 'input_basis': input_basis, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'lines': len(source.splitlines())}

def build_catalog(root):
    root = Path(root).resolve()
    modules = []
    paths = []
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = sorted((d for d in subdirs if not d.startswith('.') and d not in {'graphical_app', '__pycache__', 'node_modules', 'vendor', 'venv'}))
        paths.extend((Path(directory) / name for name in files if name.endswith('.py') and name!='__init__.py'))
    for path in sorted(paths):
        relative = path.relative_to(root)
        try:
            module = inspect_module(path)
        except (SyntaxError, UnicodeError, OSError) as exc:
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                digest = None
            module = {'id': path.stem, 'file': path.name, 'title': words(path.stem), 'family': 'Logic', 'description': str(exc), 'methods': [], 'inputs': {}, 'definitions': {}, 'terms': [], 'error': str(exc), 'sha256': digest}
        module.update(id=relative.with_suffix('').as_posix(), file=relative.as_posix())
        modules.append(module)
    return modules
