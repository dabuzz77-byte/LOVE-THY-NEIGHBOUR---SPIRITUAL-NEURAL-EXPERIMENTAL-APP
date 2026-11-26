"""Rebuild the app-owned windowless Java libraries after an approved source edit."""
import json,os,subprocess,time,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 (ROOT/'data').mkdir(parents=True,exist_ok=True)
 lock=(ROOT/'data'/'instance.lock').open('a+b')
 try:
  if os.name=='nt':
   import msvcrt
   lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
   try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
   except OSError:raise RuntimeError('Close Neural App before rebuilding its Java sections.')
  compilers=sorted(Path('C:/Program Files/Java').glob('jdk-*/bin/javac.exe'),reverse=True)
  if not compilers and shutil.which('javac'):compilers=[Path(shutil.which('javac'))]
  if not compilers:raise RuntimeError('A Java development kit was not found. Install a JDK and add javac to PATH.')
  library=ROOT/'neural_app'/'java_library';work=ROOT/'data'/'java-build';work.mkdir(parents=True,exist_ok=True);report=[]
  imported_manifest=ROOT/'references'/'desktop-java'/'manifest.json'
  imported={p['family']:p for p in json.loads(imported_manifest.read_text(encoding='utf-8'))['projects']} if imported_manifest.exists() else {}
  java_classpath=os.pathsep.join(map(str,[library/'common',*sorted((library/'dependencies').glob('*.jar')),*sorted((ROOT/'vendor-javafx').glob('*.jar'))]))
  targets=[('common',ROOT/'neural_app'/'java_src',library/'common')]+[(folder.name,folder/'src',folder/'classes') for folder in sorted(library.glob('family_*'))]
  for name,source,destination in targets:
   selected={}
   for path in source.rglob('*.java'):
    if path.name in imported.get(name,{}).get('platform_dependencies',[]):continue
    package=re.search(r'package\s+([\w.]+)\s*;',path.read_text(encoding='utf-8-sig'));package=package.group(1) if package else '';identity=(package,path.name)
    if identity not in selected or path.parent.as_posix().endswith(package.replace('.','/')):selected[identity]=path
   files=list(selected.values());destination.mkdir(parents=True,exist_ok=True);arguments=work/(name+'.args')
   arguments.write_text('\n'.join('"'+p.as_posix()+'"' for p in files),encoding='utf8')
   command=[str(compilers[0]),'-encoding','UTF-8','-classpath',java_classpath,'-d',str(destination),'@'+str(arguments)]
   result=subprocess.run(command,capture_output=True,text=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   row={'family':name,'files':len(files),'ok':result.returncode==0,'diagnostics':result.stderr};report.append(row);print(name+(': ready' if row['ok'] else ': build failed'),flush=True)
   if not row['ok']:print(result.stderr,flush=True);break
  (work/'last-build.json').write_text(json.dumps({'time':time.time(),'libraries':report},indent=2));return 0 if len(report)==len(targets) and all(row['ok'] for row in report) else 1
 finally:lock.close()

if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as error:print(str(error),flush=True);raise SystemExit(1)
