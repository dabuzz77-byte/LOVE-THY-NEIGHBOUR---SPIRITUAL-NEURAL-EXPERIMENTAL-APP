import ast
import json
import pathlib
import re
ROOT = pathlib.Path(__file__).resolve().parent
text = (ROOT / 'manuscript.txt').read_text(encoding='utf-8-sig')
lines = text.splitlines()
modules = []
for i, line in enumerate(lines):
    if not re.match('^(class \\w+|def \\w+)', line):
        continue
    end = i + 1
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith((' ', '\t', '#'))):
        end += 1
    code = '\n'.join(lines[i:end]).rstrip() + '\n'
    try:
        node = ast.parse(code).body[0]
    except SyntaxError:
        continue

    def schema(fn):
        defaults = [None] * (len(fn.args.args) - len(fn.args.defaults)) + fn.args.defaults
        return [{'name': a.arg, 'type': ast.unparse(a.annotation) if a.annotation else '', 'default': ast.unparse(d) if d is not None else None} for a, d in zip(fn.args.args, defaults) if a.arg != 'self']
    methods = [{'name': n.name, 'args': schema(n), 'doc': ast.get_docstring(n) or ''} for n in (node.body if isinstance(node, ast.ClassDef) else [node]) if isinstance(n, ast.FunctionDef)]
    modules.append({'id': f'{node.name}-{i + 1}', 'name': node.name, 'line': i + 1, 'kind': 'class' if isinstance(node, ast.ClassDef) else 'function', 'doc': ast.get_docstring(node) or '', 'methods': methods, 'source': code})
sections = []
for m in re.finditer('Your prompt:\\s*\\n(.*?)(?=\\nYour prompt:|\\Z)', text, re.S):
    body = m.group(1)
    sections.append({'title': body.splitlines()[0], 'text': body, 'line': text[:m.start()].count('\n') + 1})
(ROOT / 'catalog.json').write_text(json.dumps({'modules': modules, 'sections': sections}, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'modules': len(modules), 'sections': len(sections), 'characters': len(text)}))
