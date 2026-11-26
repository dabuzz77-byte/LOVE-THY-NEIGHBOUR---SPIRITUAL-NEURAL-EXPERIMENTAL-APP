"""Local defensive posture and source-backed security study. No remote probing."""
import copy,json,os,subprocess,threading,time
SOURCES=[('NIST security framework','https://www.nist.gov/cyberframework'),('Microsoft Defender status','https://learn.microsoft.com/powershell/module/defender/get-mpcomputerstatus'),('Microsoft detected threats','https://learn.microsoft.com/powershell/module/defender/get-mpthreatdetection'),('CISA critical infrastructure goals','https://www.cisa.gov/cross-sector-cybersecurity-performance-goals'),('OWASP testing guide','https://owasp.org/www-project-web-security-testing-guide/')]
SECTORS={'Finance':'Protect payments, benefits, wages and confidential records; practise recovery on synthetic accounts.','Government':'Protect public services, citizen privacy and accountable access; use documented disclosure channels.','Energy':'Preserve physical safety and continuous supply; study segmentation and recovery without probing operational equipment.','Personal system':'Check protection status, review detections, maintain backups and inspect unexpected permissions.'}
FOUR_WAY={'true_good':'Effective protection, informed access, recovery and authorized research.','false_good':'Surveillance or disruption presented as protection; also ignoring a real threat behind reassuring labels.','false_evil':'Mistaking legitimate owner customization, criticism or consented research for malicious conduct.','true_evil':'Credential theft, spyware, coercive control, sabotage and wrongful exposure.'}
def evaluate(observation):
 if observation.get('confirmed_malicious') is True:return {'decision':'block-and-review','reason':'Confirmed threat indicator; preserve evidence and recovery options.'}
 if observation.get('owner_permission') is True and observation.get('known_behaviour') is True:return {'decision':'allow-with-monitoring','reason':'Explicit permission and understood behaviour; no malware verdict inferred from intent.'}
 return {'decision':'review','reason':'Insufficient evidence to classify; do not label a person evil.'}
class SystemShield:
 def __init__(self):self.lock=threading.RLock();self.next_at=0;self.busy=False;self.cycle=0;self.latest={'status':'not checked'};self.study={}
 def tick(self,c):
  now=time.monotonic()
  if self.busy or now<self.next_at:return
  self.next_at=now+300;self.busy=True
  threading.Thread(target=self.inspect,args=(c,),daemon=True,name='local-shield-status').start()
 def inspect(self,c=None):
  result={'status':'unavailable','checked':time.time(),'scope':'Local Defender posture and aggregate detection count; no private file paths or network destinations collected.'}
  try:
   if os.name!='nt':raise RuntimeError('Windows Defender checks apply only to Windows')
   queries={
    'defender':"Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled,BehaviorMonitorEnabled,AntivirusSignatureLastUpdated | ConvertTo-Json -Compress",
    'firewall':"@(Get-NetFirewallProfile | Select-Object Name,Enabled) | ConvertTo-Json -Compress",
    'detection_history':"[pscustomobject]@{Count=@(Get-MpThreatDetection).Count} | ConvertTo-Json -Compress"}
   checks={}
   for name,command in queries.items():
    try:
     r=subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',"$ErrorActionPreference='Stop'; "+command],capture_output=True,text=True,timeout=12,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
     if r.returncode:raise RuntimeError('Unavailable or permission denied')
     checks[name]={'status':'measured','value':json.loads(r.stdout)}
    except Exception as e:checks[name]={'status':'unavailable','reason':str(e)[:120]}
   count=sum(x['status']=='measured' for x in checks.values())
   result.update(status='measured' if count==len(checks) else 'partial' if count else 'unavailable',checks=checks)
   result['interpretation']='Independent checks preserve available evidence when another check fails. Detection history is not a count of active infections. No clean-system verdict is inferred.' 
  except Exception as e:result['error']=str(e)[:180]
  with self.lock:
   self.cycle+=1;self.latest=result;self.busy=False;sector=list(SECTORS)[(self.cycle-1)%len(SECTORS)];self.study={'sector':sector,'objective':SECTORS[sector],'hypothesis':'Reduce harmful access while preserving essential services and legitimate owner choice.','test':'Use synthetic assets; compare protection, false positives, service continuity and recovery.','four_way':FOUR_WAY,'verdict':'Study proposal, not an intrusion authorization.'}
  if c:c.bus.publish({'origin':'system-shield','target':'all','kind':'stage-output','payload':{'cycle':self.cycle,'measured':result['status']=='measured','processing_receipt':False,'provenance':'local-protection-status','stochastic':False}})
 def view(self):
  with self.lock:return copy.deepcopy({'cycle':self.cycle,'busy':self.busy,'refresh_seconds':300,'latest':self.latest,'study':self.study,'sectors':SECTORS,'four_way':FOUR_WAY,'sources':[{'title':t,'url':u} for t,u in SOURCES],'policy':'Allow permitted, understood activity; block confirmed threats through existing security controls; review uncertainty. No person is classified by religion or belief.','capability':'Read-only monitoring and study; Windows Security remains the malware protection provider. No automatic deletion, quarantine or remote scanning.'})
