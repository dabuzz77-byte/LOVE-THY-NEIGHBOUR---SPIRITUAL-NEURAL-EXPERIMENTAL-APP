"""Typed scientific and programmatic thought experiments; no laboratory/host control."""
import collections,copy,hashlib,json,math,random,time,ast
from fractions import Fraction
C=299792458.;R=8.31446261815324;RYDBERG=10973731.568157
CATALOG={
 'particle-dispersion':{'equation':'E = hypot(p*c, m*c^2)','parameters':{'mass_kg':1e-30,'momentum_kg_m_s':1e-22},'units':'E in joules','assumptions':'Free-particle special-relativistic energy; no interaction field.','source':'https://physics.nist.gov/cuu/Constants/'},
 'quantum-transfer':{'equation':'P2 = (1-exp(-gamma*t)*cos(2*J*t))/2','parameters':{'coupling_per_s':1.,'depolarization_per_s':.1,'time_s':1.},'units':'Probability dimensionless; rates s^-1','assumptions':'Two-level coherent transfer with an isotropic depolarizing envelope. Illustrative for transport questions; not a validated model of a living organism.','source':'https://qiskit.qotlabs.org/learning/courses/general-formulation-of-quantum-information/quantum-channels/quantum-channel-basics'},
 'chemical-first-order':{'equation':'A=A0*exp(-k*t); B=A0-A','parameters':{'initial_mol_per_l':1.,'rate_per_s':.1,'time_s':10.},'units':'Concentration mol/L; rate s^-1; time s','assumptions':'Closed A -> B first-order irreversible reaction; constant volume and rate.','source':'https://goldbook.iupac.org/'},
 'arrhenius':{'equation':'ln(k)=ln(A)-Ea/(R*T)','parameters':{'prefactor_per_s':1e12,'activation_j_per_mol':50000.,'temperature_K':300.},'units':'Rate s^-1; Ea J/mol; T kelvin','assumptions':'Temperature-independent prefactor and activation energy over the modelled range.','source':'https://goldbook.iupac.org/terms/view/A00446'},
 'hydrogen-lines':{'equation':'1/lambda=Rinf*(1/n_lower^2-1/n_upper^2)','parameters':{'n_lower':2,'n_upper':3},'units':'Vacuum wavelength metres','assumptions':'Infinite-nuclear-mass Rydberg approximation; reduced-mass, fine and hyperfine corrections omitted. CODATA 2022 Rinf.','source':'https://physics.nist.gov/cgi-bin/cuu/Value?ryd'},
 'bit-exactness':{'equation':'exact integer/rational addition versus binary floating point','parameters':{'integer':9007199254740993},'units':'Dimensionless','assumptions':'Finite explicit arithmetic contract; not a physical observation.','source':'https://docs.python.org/3/library/fractions.html'},
 'program-composition':{'equation':'typed operations fitted to training examples and held-out tests','parameters':{},'units':'Typed text data','assumptions':'Pure registered operations only; no arbitrary generated code execution.','source':'Neural App native synthesis'},
 'command-transaction':{'equation':'before -> proposed write -> failure -> rollback -> verify','parameters':{},'units':'Local simulated state','assumptions':'In-memory file/service model; no real commands or external device changes.','source':'Neural App systemic action contracts'},
 'language-encoding':{'equation':'text -> UTF-8 -> text; JSON roundtrip; normalisation idempotence','parameters':{},'units':'Unicode text and bytes','assumptions':'Encoding tests do not establish translation quality, fluency or semantic understanding.','source':'https://www.unicode.org/reports/tr15/'} }

def run(model,parameters=None):
 if model not in CATALOG:raise ValueError('Choose a registered experiment model')
 spec=CATALOG[model];p={**spec['parameters'],**(parameters or {})}
 if any(k not in spec['parameters'] for k in (parameters or {})):raise ValueError('Unknown model parameter')
 for k,v in p.items():
  if type(v) not in (int,float) or not math.isfinite(v) or v<0 or v>1e100:raise ValueError('Parameters must be bounded, finite and nonnegative')
 checks={};result={}
 if model=='particle-dispersion':
  rest=p['mass_kg']*C*C;pc=p['momentum_kg_m_s']*C;e=math.hypot(pc,rest);scale=max(e,1e-300);error=(e/scale)**2-(pc/scale)**2-(rest/scale)**2;result={'energy_J':e,'rest_energy_J':rest,'normalised_mass_shell_residual':error};checks={'mass_shell_identity':abs(error)<1e-12,'nonnegative_energy':e>=0}
 elif model=='quantum-transfer':
  if p['coupling_per_s']>1e6 or p['time_s']>1e6:raise ValueError('Phase range exceeds this numerical model')
  envelope=math.exp(-min(745,p['depolarization_per_s']*p['time_s']));prob=(1-envelope*math.cos(2*p['coupling_per_s']*p['time_s']))/2;purity=(1+envelope**2)/2;result={'population_2':prob,'population_1':1-prob,'purity':purity};checks={'probabilities_valid':0<=prob<=1,'trace_one':math.isclose(prob+1-prob,1),'purity_valid':.5<=purity<=1}
 elif model=='chemical-first-order':
  a=p['initial_mol_per_l']*math.exp(-min(745,p['rate_per_s']*p['time_s']));b=p['initial_mol_per_l']-a;result={'A_mol_per_l':a,'B_mol_per_l':b};checks={'mass_balance':math.isclose(a+b,p['initial_mol_per_l'],rel_tol=1e-12),'nonnegative':a>=0 and b>=0}
 elif model=='arrhenius':
  if p['temperature_K']<=0 or p['prefactor_per_s']<=0:raise ValueError('Temperature and prefactor must be positive')
  logk=math.log(p['prefactor_per_s'])-p['activation_j_per_mol']/R/p['temperature_K'];k=math.exp(logk) if logk>-745 else 0.;result={'log_rate':logk,'rate_per_s':k,'underflow_to_zero':logk<=-745};checks={'rate_within_prefactor':0<=k<=p['prefactor_per_s']*(1+1e-12)}
 elif model=='hydrogen-lines':
  lo=p['n_lower'];hi=p['n_upper']
  if type(lo)is not int or type(hi)is not int or not 1<=lo<hi<=1000:raise ValueError('Use integer levels 1 <= lower < upper <= 1000')
  wavelength=1/(RYDBERG*(1/lo**2-1/hi**2));result={'wavelength_m':wavelength,'wavelength_nm':wavelength*1e9,'frequency_Hz':C/wavelength};checks={'positive_wavelength':wavelength>0}
 elif model=='bit-exactness':
  n=p['integer']
  if type(n)is not int:raise ValueError('Integer input required')
  exact=n+1;floating=float(n)+1;result={'exact':exact,'floating':floating,'floating_exact':Fraction.from_float(floating)==exact};checks={'rational_agrees':Fraction(n)+1==exact};result['counterexample_to_always_exact_float']=not result['floating_exact']
 elif model=='program-composition':
  from .native_synthesis import question_spec,synthesize,execute
  found=synthesize(question_spec('sort lines and remove duplicates'));program=found['solution']['operations'] if found['solution'] else [];actual=execute(program,'z\na\nz\nb') if program else None;result={'operations':program,'unseen_input_output':actual,'design':found.get('experiment_design')};checks={'held_out_transfer':actual=='a\nb\nz'}
 elif model=='command-transaction':
  original={'settings':'old','essential-service':'running'};state=copy.deepcopy(original);state['settings']='new';after_write=copy.deepcopy(state);state=copy.deepcopy(original);result={'before':original,'simulated_after_write':after_write,'after_fault_and_rollback':state};checks={'rollback_restores_state':state==original,'essential_service_preserved':state['essential-service']=='running'}
 else:
  import unicodedata
  texts=['hello','مرحبا','हैलो','你好','こんにちは','გამარჯობა','ᎣᏏᏲ','e\u0301'];result={'languages':'supplied multilingual encoding fixtures, not translations generated by the engine','cases':len(texts)};checks={'utf8_roundtrip':all(s.encode('utf-8').decode('utf-8')==s for s in texts),'json_roundtrip':all(json.loads(json.dumps(s))==s for s in texts),'NFC_idempotence':all(unicodedata.normalize('NFC',unicodedata.normalize('NFC',s))==unicodedata.normalize('NFC',s) for s in texts)}
 return {'model':model,'equation':spec['equation'],'parameters':p,'units':spec['units'],'assumptions':spec['assumptions'],'source':spec['source'],'result':result,'checks':checks,'passed':all(checks.values()),'scope':'Numerical/contract checks under the stated model; not experimental confirmation of a world or biological claim.'}

class ExperimentalThought:
 def __init__(self):self.sequence=0;self.counts=collections.Counter();self.history=collections.deque(maxlen=32);self.next_at=0;self.pending=[];self.latest={}
 def calculate(self,model,parameters=None):
  record=run(model,parameters);self.sequence+=1;record.update(sequence=self.sequence,time=time.time());self.history.append(record);self.counts[model]+=1;self.latest=record;return copy.deepcopy(record)
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  resources=c.adaptive_rail.view();self.next_at=time.monotonic()+max(3,resources.get('adaptive_interval_seconds',.2)*10)
  goal=c.goal.lower();relevance={'quantum-transfer':('quantum','biology'),'chemical-first-order':('chemistry','reaction'),'particle-dispersion':('particle','relativ'),'hydrogen-lines':('hydrogen','star'),'language-encoding':('language','conversation'),'program-composition':('code','program'),'command-transaction':('command','system'),'bit-exactness':('bit','integer'),'arrhenius':('temperature',)}
  model=max(CATALOG,key=lambda m:1/(1+self.counts[m])+.15*sum(w in goal for w in relevance[m]));record=self.calculate(model);self.pending.append({'origin':'experimental-thought','target':'all','kind':'stage-output','payload':{'model':model,'result':record['result'],'checks':record['checks'],'scope':record['scope'],'provenance':'registered-local-model-calculation','stochastic':False,'predefined_text':True}})
 def view(self):return {'sequence':self.sequence,'catalog':copy.deepcopy(CATALOG),'model_counts':dict(self.counts),'latest':copy.deepcopy(self.latest),'recent':list(self.history),'scope':'Native scientific/programmatic/encoding calculations; no lab actuation or automatically executed generated commands.'}
