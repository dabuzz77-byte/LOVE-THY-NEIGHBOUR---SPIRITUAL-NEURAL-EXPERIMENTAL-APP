"""Command effects and checks; this module never executes commands."""
import re
COMMANDS={
 'Get-ChildItem':('List directory entries','read','Compare returned paths with requested directory'),
 'Get-Content':('Read file content','read','Check file identity/hash and returned bytes'),
 'Set-Content':('Replace file content','write','Read back and compare expected content'),
 'Copy-Item':('Copy files','write','Compare source/destination hashes'),
 'Move-Item':('Move or rename paths','write','Check destination and original path state'),
 'Remove-Item':('Delete paths','destructive','Verify exact target and resulting absence; recovery requires backup'),
 'Get-Process':('List processes','read','Match process identifiers and observation time'),
 'Stop-Process':('Terminate a process','process-change','Check exact process exited'),
 'Get-Service':('Read service status','read','Check service identity and returned state'),
 'Restart-Service':('Restart a service','administrator-may-be-required','Observe stopped/running transition and service health'),
 'Get-NetTCPConnection':('Read TCP connection records','read','Compare addresses, ports, process IDs and time'),
 'Test-NetConnection':('Test network reachability','network-read','Check DNS/TCP response and timeout independently'),
 'Invoke-WebRequest':('Send an HTTP request','network','Check status, origin, response and request method; remote writes depend on method'),
 'Invoke-RestMethod':('Send HTTP request and parse response','network','Validate method, destination, status and response schema'),
 'Start-Process':('Start a program','process-change','Check returned PID, exit code and intended effects'),
 'netsh':('Inspect or change network configuration depending on arguments','administrator-may-be-required','Compare configuration before/after and connectivity'),
 'reg':('Query or change registry depending on subcommand','administrator-may-be-required','Verify exact key/value and retain recovery data'),
 'sc':('Inspect or control services depending on subcommand','administrator-may-be-required','Check service state and health'),
 'ping':('Send reachability probes','network-read','Check actual replies and measured latency; no reply is not proof of absence'),
 'ipconfig':('Inspect or change adapter/DHCP state depending on flags','network','Check selected flags and actual adapter state'),
 'curl':('Send network requests','network','Check destination, method, HTTP status and body; flags determine effects'),
 'ssh':('Run an authenticated remote session/command','remote-access','Verify host identity, credentials, returned status and remote outcome'),
 'sudo':('Request elevated execution on supported systems','administrator-required','OS authorization plus exact underlying command/result'),
 'chmod':('Change file permission bits','permission-change','Compare permission state before/after'),
 'systemctl':('Inspect or manage system services','administrator-may-be-required','Check subcommand, service identity and actual state')}
def view():
 from .language_formats import formats
 from .native_scripts import FORMATS
 rows=formats()
 return {'language_formats':{'count':len(rows),'names':[r['name'] for r in rows],'meaning':'Lexical recognition from the existing Pygments catalog; not complete language semantics'},'script_templates':list(FORMATS),'commands':[{'command':k,'effect':v[0],'access':v[1],'verification':v[2]} for k,v in COMMANDS.items()],'execution':'Existing reviewed command tools and actual OS permissions; no kernel/root bypass','scope':'Command-family definitions; arguments, pipelines and target state can change effects'}
def inspect(text):
 found=[]
 for name,(effect,access,check) in COMMANDS.items():
  if re.search(r'(?<![\w-])'+re.escape(name)+r'(?![\w-])',text,re.I):found.append({'command':name,'expected_effect':effect,'required_access':access,'check':check,'status':'static recognition; not executed'})
 return {'commands':found,'unresolved':not bool(found),'scope':'Static command-family matches; not a proof of complete script behaviour'}
