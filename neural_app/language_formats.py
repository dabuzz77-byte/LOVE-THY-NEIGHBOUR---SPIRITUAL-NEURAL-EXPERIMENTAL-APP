"""Local source-format recognition and explicit syntax checks; never run submitted programs."""
import ast,collections,functools,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VENDOR=ROOT/'vendor-language'
if str(VENDOR) not in sys.path:sys.path.insert(0,str(VENDOR))

@functools.lru_cache(maxsize=1)
def formats():
 from pygments.lexers import get_all_lexers
 return sorted([{'name':name,'aliases':list(aliases),'files':list(files),'mime':list(mime)} for name,aliases,files,mime in get_all_lexers(plugins=False)],key=lambda r:r['name'].lower())

@functools.lru_cache(maxsize=1)
def tools():
 vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
 visual=None
 if vswhere.is_file():
  try:visual=subprocess.run([str(vswhere),'-latest','-products','*','-property','installationPath'],capture_output=True,text=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).stdout.strip()
  except (OSError,subprocess.TimeoutExpired):pass
 csc=Path(visual)/'MSBuild/Current/Bin/Roslyn/csc.exe' if visual else None
 jdks=sorted((Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Java').glob('jdk*/bin/javac.exe'),reverse=True);javac=str(jdks[0]) if jdks else shutil.which('javac')
 return {'python':sys.executable,'java':shutil.which('java'),'javac':javac,'visual_studio':visual,'csharp_compiler':str(csc) if csc and csc.is_file() else None,'powershell':shutil.which('pwsh') or shutil.which('powershell'),'node':shutil.which('node')}

def catalog():
 import pygments
 return {'formats':formats(),'count':len(formats()),'engine':'Pygments '+pygments.__version__,'tools':tools(),'scope':'Built-in syntax formats, aliases and lexical rules. Recognition alone is not a syntax test or program execution.','references':[{'title':'Pygments format API','url':'https://pygments.org/docs/api/'},{'title':'Python AST','url':'https://docs.python.org/3/library/ast.html'},{'title':'Java compiler','url':'https://docs.oracle.com/en/java/javase/25/docs/specs/man/javac.html'},{'title':'PowerShell parser','url':'https://learn.microsoft.com/en-us/dotnet/api/system.management.automation.language.parser.parseinput'}]}

@functools.lru_cache(maxsize=1)
def recognizers():
 from pygments.lexers import find_lexer_class_by_name
 return [(row,find_lexer_class_by_name(row['aliases'][0])) for row in formats() if row['aliases']]

def recognize(body):
 from pygments.lexers import get_lexer_by_name,get_lexer_for_filename,find_lexer_class_by_name
 code=str(body.get('source',''))
 if len(code)>64000:raise ValueError('Use up to 64,000 characters per check.')
 alias=str(body.get('language','auto'));known={a for row in formats() for a in row['aliases']};filename=Path(str(body.get('filename','')).replace('\\','/')).name;candidates=[]
 if alias!='auto':
  if alias not in known:raise ValueError('Choose a registered built-in format.')
  lexer=get_lexer_by_name(alias);basis='Selected format'
 elif filename:
  try:lexer=get_lexer_for_filename(filename,code);basis='Filename / format rule'
  except Exception:lexer=get_lexer_by_name('text');basis='No filename rule matched'
 else:
  for row,cls in recognizers():
   score=float(cls.analyse_text(code[:16000]) or 0)
   if score>0:candidates.append({'name':row['name'],'alias':row['aliases'][0],'format_score':score})
  candidates.sort(key=lambda r:-r['format_score']);lexer=get_lexer_by_name(candidates[0]['alias'] if candidates else 'text');basis='Built-in format heuristics; scores are not probabilities' if candidates else 'No distinctive format recognised'
 counts=collections.Counter();tokens=[];offset=0
 for token,value in lexer.get_tokens(code):
  counts[str(token)]+=len(value)
  if len(tokens)<4000:tokens.append({'type':str(token),'text':value,'offset':offset})
  offset+=len(value)
 return {'name':lexer.name,'aliases':list(lexer.aliases),'basis':basis,'candidates':candidates[:8],'characters':len(code),'lines':len(code.splitlines()),'token_characters':dict(counts),'tokens':tokens,'token_output_limit':4000,'program_executed':False}

def _command(args,code=None,cwd=None):
 env=os.environ.copy()
 for key in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','JDK_JAVAC_OPTIONS','_JAVA_OPTIONS','CLASSPATH'):env.pop(key,None)
 r=subprocess.run(args,input=code,capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=cwd,env=env,timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 return {'passed':r.returncode==0,'exit_code':r.returncode,'diagnostics':(r.stdout+r.stderr)[:32000],'program_executed':False}

def syntax(body,data):
 source=str(body.get('source',''));language=str(body.get('language','')).lower();filename=str(body.get('filename','')).lower()
 if len(source)>64000:raise ValueError('Use up to 64,000 source characters.')
 if language=='auto':language=recognize(body)['aliases'][0]
 if language in ('python','python3','py') or filename.endswith('.py'):
  try:tree=ast.parse(source);return {'passed':True,'method':'Python AST parser','nodes':len(list(ast.walk(tree))),'program_executed':False}
  except SyntaxError as e:return {'passed':False,'method':'Python AST parser','diagnostics':{'message':e.msg,'line':e.lineno,'column':e.offset},'program_executed':False}
 if language in ('bat','batch','dosbatch') or filename.endswith(('.bat','.cmd')):
  issues=[];redirections=[];numeric_calls=[]
  for n,line in enumerate(source.splitlines(),1):
   line=line.strip()
   if not line or line.startswith('::') or re.match(r'(?i)@?rem(?:\s|$)',line):continue
   unescaped=re.sub(r'\^.', '',line)
   for match in re.finditer(r'(>>?)\s*(?:"([^"]+)"|([^\s<>|&]+))',unescaped):redirections.append({'line':n,'operator':match.group(1),'target':match.group(2) or match.group(3),'effect':'stdout file creation/truncation or append; file can be extensionless'})
   if re.match(r'^\d+(?:\s|$)',unescaped):numeric_calls.append({'line':n,'command':unescaped.split()[0],'effect':'May resolve to a same-named batch file in the working directory or PATH.'})
   if unescaped.count('"')%2:issues.append({'line':n,'message':'Unpaired double quote; review command context.'})
  return {'passed':not issues,'method':'Basic batch static lint · not a complete cmd.exe parser','diagnostics':issues,'effects':{'output_redirections':redirections,'numeric_command_invocations':numeric_calls},'program_executed':False,'scope':'No commands run. Dynamic expansion and external command availability are not evaluated.'}
 t=tools()
 if language in ('powershell','pwsh','ps1') or filename.endswith('.ps1'):
  if not t['powershell']:raise ValueError('PowerShell parser is not installed.')
  script="$PSModuleAutoLoadingPreference='None'; $null=[Console]::InputEncoding=[System.Text.Encoding]::UTF8; $s=[Console]::In.ReadToEnd(); $t=$null; $e=$null; $null=[System.Management.Automation.Language.Parser]::ParseInput($s,[ref]$t,[ref]$e); foreach($item in $e){[Console]::WriteLine($item.Message+' | line '+$item.Extent.StartLineNumber+' column '+$item.Extent.StartColumnNumber)}; if($e.Count){exit 1}else{[Console]::WriteLine('Parse OK')}"
  import base64
  result=_command([t['powershell'],'-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],source)
  result['method']='Installed PowerShell AST parser · submitted script not invoked';return result
 base=Path(data).resolve()/'language-checks';base.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='syntax-',dir=base) as directory:
  folder=Path(directory).resolve();assert folder.is_relative_to(base.resolve())
  if language=='java' or filename.endswith('.java'):
   if not t['javac']:raise ValueError('Java compiler is not installed.')
   match=re.search(r'\bpublic\s+(?:(?:abstract|final|sealed)\s+)*(?:class|interface|enum|record)\s+([A-Za-z_$][\w$]*)',source);name=match.group(1) if match else 'Main'
   file=folder/(name+'.java');file.write_text(source,encoding='utf-8');out=folder/'classes';out.mkdir()
   result=_command([t['javac'],'-J-Xmx128m','-proc:none','-encoding','UTF-8','-classpath',str(folder),'-sourcepath',str(folder),'-d',str(out),str(file)],cwd=folder);result['method']='Installed javac · annotation processors disabled · classes not run';return result
  if language in ('csharp','c#','cs') or filename.endswith('.cs'):
   if not t['csharp_compiler']:raise ValueError('Visual Studio C# compiler was not found.')
   file=folder/'Check.cs';file.write_text(source,encoding='utf-8');result=_command([t['csharp_compiler'],'/nologo','/noconfig','/target:library','/out:'+str(folder/'Check.dll'),str(file)],cwd=folder);result['method']='Visual Studio Roslyn C# compile check · assembly not run';return result
  if language in ('javascript','js') or filename.endswith(('.js','.mjs')):
   if not t['node']:raise ValueError('Node.js syntax checker was not found.')
   file=folder/'check.mjs';file.write_text(source,encoding='utf-8');result=_command([t['node'],'--check',str(file)],cwd=folder);result['method']='Node.js syntax check · code not run';return result
  if language=='json' or filename.endswith('.json'):
   try:json.loads(source);return {'passed':True,'method':'JSON parser','program_executed':False}
   except ValueError as e:return {'passed':False,'method':'JSON parser','diagnostics':str(e),'program_executed':False}
 return {'passed':None,'method':'Lexical recognition available; no syntax validator configured for this format.','program_executed':False}

def scan(body,data):
 """Small round-robin windows; classification and static checks only."""
 sources=[s for s in body.get('sources',[])[:256] if s.get('stochastic') is True and s.get('predefined_text') is False and s.get('contains_model_text') is False and isinstance(s.get('text'),str)]
 if not sources:return {'results':[],'sources':0,'programs_executed':0}
 cursor=max(0,int(body.get('cursor',0)));width=max(32,min(2048,int(body.get('width',256))));count=max(1,min(8,int(body.get('windows',4))));rows=[];tested=False
 safe_aliases={'python','python3','py','json','java','csharp','c#','cs','powershell','pwsh','bat','batch','dosbatch','javascript','js'}
 for i in range(count):
  index=(cursor+i)%len(sources);source=sources[index];text=source['text'][:1048576];offset=((cursor+i)//len(sources)*max(1,width-32))%max(1,len(text));snippet=text[offset:offset+width];r=recognize({'source':snippet});alias=r['aliases'][0] if r['aliases'] else 'text';score=r['candidates'][0]['format_score'] if r['candidates'] else 0
  row={'source':str(source.get('name','generated'))[:160],'offset':offset,'snippet':snippet,'recognised':r['name'],'alias':alias,'format_score':score,'candidates':r['candidates'][:3],'program_executed':False}
  if body.get('test',True) and not tested and alias in safe_aliases and score>=.2:
   try:row['syntax_check']=syntax({'language':alias,'source':snippet},data)
   except Exception as e:row['syntax_check']={'passed':False,'diagnostics':str(e),'program_executed':False}
   if alias in ('python','python3','py') and row['syntax_check'].get('passed'):
    from .restricted_test import run_restricted
    row['restricted_test']=run_restricted({'source':snippet,'language':'python'})
   tested=True
  else:row['syntax_check']={'passed':None,'method':'No distinctive supported syntax candidate, or this batch already used its one test slot.','program_executed':False}
  rows.append(row)
 return {'results':rows,'sources':len(sources),'next_cursor':cursor+count,'windows':count,'maximum_characters':count*width,'programs_executed':0,'policy':'Recognition, at most one parser / compile check and a bounded Python-subset test per batch. No host program, batch command or PowerShell script runs.'}
