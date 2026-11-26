"""Offline source-release checks. No server, network or model is started."""
from pathlib import Path
import ast,json,os,sys,hashlib,re
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
def main():
    errors=[];python_count=json_count=0
    for path in ROOT.rglob('*'):
        if any(part in {'.git','.venv','__pycache__','node_modules'} for part in path.relative_to(ROOT).parts):continue
        if not path.is_file():continue
        rel=path.relative_to(ROOT).as_posix()
        if path.stat().st_size>=25_000_000:errors.append('Too large for browser upload: '+rel)
        if rel.startswith(('data/','preserved/data/','preserved/database-weights/','runtime/','runtime-recovered/')):errors.append('Private/runtime directory present: '+rel)
        if path.suffix.lower() in {'.sqlite','.sqlite3','.db','.gguf','.safetensors','.pyc','.class'}:errors.append('Runtime artifact present: '+rel)
        if path.suffix.lower() in {'.py','.java','.js','.txt','.json','.jsonl','.md'}:
            try:
                text=path.read_text(encoding='utf-8-sig')
                credential_pattern=r"(?i)\b(?:API_?KEY(?:_?(?:SECRET|VALUE))?|(?:GOOGLE|GEMINI|OPENAI|GCP|AZURE)_(?:API_?)?KEY|ACCESS_?TOKEN|CLIENT_?SECRET|SECRET_?KEY)\s*[=:]\s*[\"']([^\"'\r\n]{20,})[\"']"
                for match in re.finditer(credential_pattern,text):
                    value=match.group(1)
                    placeholders=['YOUR_','REDACT','REPLACE','PLACEHOLDER','EXAMPLE','ENTER_','INSERT_']
                    if not any(word in value.upper() for word in placeholders) and not any(c.isspace() for c in value) and len(set(value))>=8:
                        errors.append('Potential hard-coded credential: '+rel)
            except UnicodeError:
                pass
        if path.suffix=='.py':
            try:ast.parse(path.read_text(encoding='utf-8-sig'),filename=rel);python_count+=1
            except (SyntaxError,UnicodeError) as exc:errors.append(rel+': '+str(exc))
        elif path.suffix in {'.json','.geojson','.webmanifest'}:
            try:json.loads(path.read_text(encoding='utf-8-sig'));json_count+=1
            except (ValueError,UnicodeError) as exc:errors.append(rel+': '+str(exc))
    for name in ['desktop.py','ui/index.html','ui/app.js','README.md','LICENSE','requirements.txt','.gitignore','original-panels.json','python-sections.json','java-sections.json','web-sections.json']:
        if not (ROOT/name).is_file():errors.append('Missing required file: '+name)
    from neural_app import translation as btq
    for raw in [b'',b'\0\0leading and trailing\0',bytes(range(256)),bytes(range(256))*64,'Neural \U0001f30d \u00b7 \u4e09\u9032\u6570'.encode()]:
        if btq.decode(btq.encode(raw))!=raw:errors.append('Lossless transport round trip failed')
    for bits in ['0','0000','001011','01'*2048]:
        if btq.translate_bits(bits)['recovered_binary']!=bits:errors.append('Bit-width round trip failed')
    for i in range(3):
        if btq.inverse_fourier(btq.fourier(i))!=i:errors.append('Qutrit representation round trip failed')
    print(json.dumps({'python_files_parsed':python_count,'json_files_parsed':json_count,'transport_checks':'passed' if not errors else 'see errors','errors':errors},indent=2))
    return bool(errors)
if __name__=='__main__':raise SystemExit(main())
