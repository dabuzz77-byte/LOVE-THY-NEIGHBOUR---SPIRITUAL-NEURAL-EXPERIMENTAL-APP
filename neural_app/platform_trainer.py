"""Source-linked platform coordination curriculum and inert plan translation."""
import copy,math,threading,time
from .action_ethics import study_frame
PLATFORMS={
 'Android':('https://developer.android.com/tools/adb','ADB and Android Studio; debugging requires device pairing and acknowledgement.','adb devices -l'),
 'iOS':('https://developer.apple.com/documentation/xcode','Xcode development and Simulator on a compatible Mac; device-specific provisioning.','xcrun simctl list devices available'),
 'Windows':('https://learn.microsoft.com/en-us/powershell/','PowerShell and Windows Settings; distinguish user and administrator operations.','Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version'),
 'Linux':('https://www.kernel.org/doc/html/latest/admin-guide/index.html','Distribution-specific package management and kernel administration.','uname -sr'),
 'macOS':('https://support.apple.com/guide/mac-help/welcome/mac','System Settings, supported recovery and developer tools.','sw_vers'),
 'PlayStation':('https://partners.playstation.net/','Public partner registration and support; proprietary SDK access is not included.',None),
 'Xbox':('https://learn.microsoft.com/en-us/previous-versions/windows/uwp/xbox-apps/frequently-asked-questions','Study documented developer-program routes and current hardware eligibility.',None),
 'Nintendo':('https://developer.nintendo.com/the-process','Public developer registration, platform access review and publishing process.',None),
 'FreeBSD':('https://docs.freebsd.org/en/books/handbook/','Handbook-based administration, packages, backups and recovery.','freebsd-version'),
 'OpenBSD':('https://www.openbsd.org/faq/','FAQ-based installation and system administration.','uname -sr'),
 'ChromeOS':('https://chromium.googlesource.com/chromiumos/docs/+/HEAD/developer_mode.md','Study supported Linux development and hardware-specific developer-mode consequences.',None),
 'SteamOS':('https://partner.steamgames.com/doc/steamdeck','Steam Deck development, compatibility and recovery study.',None)}
TASKS=['discover options','inspect system','backup and recovery','develop own app','repair and customise','unlock or jailbreak review']
FOUR={'true_good':'Informed owner autonomy, useful repair, accessibility, play and sustainable creation.','false_good':'Commercial lock-in called protection, or a risky modification called liberation while its costs are concealed.','false_evil':'Condemning legitimate tinkering, authorised security study, preservation or criticism merely because it challenges a business model.','true_evil':'Exposing other people’s data, deception, damaging essential services, malicious software or exploiting vulnerable creators and users.'}
LESSONS=[
 {'title':'Cheeky Monkey · owner autonomy','teaching':'Curiosity, experimentation, repair and customisation can be worthwhile. Assess actual consequences rather than treating disobedience to a business preference as harm. Device ownership does not alone grant control of other people’s accounts or data.'},
 {'title':'Discovery before choice','teaching':'Explain available options, capabilities, costs, alternatives and recovery. The owner can choose yes, no or later without pressure. Explain inaccessible or unsupported options honestly.'},
 {'title':'Joy is a reward','teaching':'A child’s happiness and a creator’s satisfaction are real benefits. Some creators welcome free access. Record their expressed policy; compassion is a reason to ask, not to invent their answer.'},
 {'title':'Daily bread for child and creator','teaching':'Prioritise access for people in poverty while recognising developers’ current needs for housing, food, equipment and time. Unaffordable access is not automatically a lost sale; neither is every creator financially secure.'},
 {'title':'Access and preservation','teaching':'Study free releases, gifts, regional pricing, libraries, accessibility, preservation and creator-approved sharing. Distinguish these from malware distribution, commercial exploitation, account compromise and unsupported assumptions about permission.'},
 {'title':'Lord’s Prayer · accountable power','teaching':'Provision, forgiveness, protection and repair guide the assessment. Compare action, delay, alternatives and restoration; do not confuse an ethical judgment with credentials or evidence of a completed action.'}]
def plan(platform,task,choice='later',informed=False,owner=False,backup=False):
 if platform not in PLATFORMS or task not in TASKS:raise ValueError('Choose a registered platform and task')
 if choice not in ('yes','no','later'):raise ValueError('Choice must be yes, no or later')
 if any(type(v)is not bool for v in (informed,owner,backup)):raise ValueError('Use explicit boolean choices')
 url,note,command=PLATFORMS[platform];blocked=[]
 if not informed:blocked.append('Explain options and consequences before a decision')
 if not owner:blocked.append('Identify the relevant owner and permission for the particular operation')
 if choice!='yes':blocked.append('Owner chose '+choice+'; no action proposal progresses')
 modifying=task in ('develop own app','repair and customise','unlock or jailbreak review')
 if modifying and not backup:blocked.append('Establish backup, restore verification and a recovery route')
 advanced=task=='unlock or jailbreak review'
 if advanced:blocked.append('Device model, OS version, method, recovery and security impact need separate review; no bypass implementation in this trainer')
 preview=command if task=='inspect system' and not blocked else None
 return {'platform':platform,'task':task,'choice':choice,'informed':informed,'owner_asserted':owner,'backup_asserted':backup,'source':url,'platform_basis':note,'steps':['Explain purpose, alternatives and actual platform capability','Identify affected data and whose permission applies','Record yes / no / later without pressure','Check backup, recovery and service dependencies','Preview a specific supported operation','Verify the observed result and restore if necessary'],'command_preview':preview,'prerequisites':blocked,'status':'Draft plan requires operation-specific review' if not blocked else 'Study prerequisites','four_way':FOUR,'execution':'Simulation and command preview only; no device or console operation executed','external_execution':False,'credentials_requested':False}
class PlatformTrainer:
 def __init__(self):self.sequence=0;self.next_at=0;self.next_research=0;self.lock=threading.RLock();self.streams={};self.latest={};self.research_status={}
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  from .training_pace import interval
  self.next_at=now+interval(c,.5);i=self.sequence%6;platform=list(PLATFORMS)[(self.sequence//6)%len(PLATFORMS)];task=TASKS[i];valid=plan(platform,task,'yes',True,True,True);declined=plan(platform,task,'no',True,True,True);uninformed=plan(platform,task,'yes',False,True,True)
  self.sequence+=1;record={'stream':i,'task':task,'cycle':self.sequence,'platform':platform,'plan':valid,'negative_controls':{'declined_does_not_progress':declined['command_preview'] is None and bool(declined['prerequisites']),'uninformed_does_not_progress':uninformed['command_preview'] is None and bool(uninformed['prerequisites'])},'ethical_study':study_frame('platform-coordination',self.sequence),'scope':'Finite plan-contract practice; not a jailbreak, emulator, device controller or model-weight update.'};record['passed']=all(record['negative_controls'].values())
  with self.lock:self.streams[i]=record;self.latest=record
  research=getattr(getattr(c,'software_theory',None),'research',None)
  if research and now>=self.next_research:
   self.next_research=now+3600
   try:self.research_status=research.request(platform+' operating system accessibility repair software preservation')
   except Exception as e:self.research_status={'status':'unavailable','error':str(e)[:160]}
  c.bus.publish({'origin':'platform-trainer','target':'all','kind':'stage-output','payload':{'cycle':self.sequence,'stream':i,'passed':record['passed'],'external_actions':0,'provenance':'source-linked-platform-plan-contract','stochastic':False,'predefined_text':True}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'platforms':list(PLATFORMS),'tasks':TASKS,'streams':copy.deepcopy(list(self.streams.values())),'latest':copy.deepcopy(self.latest),'lessons':LESSONS,'four_way':FOUR,'sources':[{'title':k,'url':v[0],'note':v[1]} for k,v in PLATFORMS.items()],'research':copy.deepcopy(self.research_status),'scope':'Expandable twelve-platform reference and six-stream plan trainer; not complete OS knowledge or installed proprietary SDKs.'}
 def sphere(self,c):
  state=self.view()
  with c.lock:sources=copy.deepcopy(list(c.sources.values()));goal=c.goal
  records=[{'source':'platform-trainer','path':['stream',row['stream']],'parent_event':row['cycle'],'record':row} for row in state['streams']]
  for source in sources:
   if source.get('facts'):records.append({'source':source['source'],'path':source['facts'][0].get('path',[]),'parent_event':source.get('parent_event'),'record':{'observation':source['facts'][0],'question':'Can this inform a supported cross-platform task with explicit inputs, owner choice and a result check?','four_way':FOUR,'status':'Candidate relevance study; no inferred device access.'}})
  particles=[]
  for i,row in enumerate(records):
   y=1-2*(i+.5)/max(1,len(records));r=math.sqrt(max(0,1-y*y));a=i*2.39996323
   particles.append({'id':'platform:'+str(i),'point':[r*math.cos(a),y,r*math.sin(a)],'phase':1.,'autonomy':0.,'selected':True,'expression_type':'platform-plan-study','symbol':'◇','value_preview':row['source'],'source':row['source'],'path':row['path'],'parent_event':row['parent_event'],'record':row['record']})
  return {'sequence':state['sequence'],'particles':particles,'retained_sources':len(sources),'represented_values':len(records),'received_events':state['sequence'],'goal':goal,'selected_phases':[1.],'thought_trace':records,'scope':'Whole-engine captured observations plus simulated platform plans; no external execution.'}
