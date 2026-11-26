"""Source-labelled periodic study, bounded numerical experiments and shared feedback."""
import copy,json,math,time,threading
from pathlib import Path
from .action_ethics import study_frame
H=6.62607015e-34;C=299792458.;EV=1.602176634e-19;HBAR=H/(2*math.pi)
SOURCES=[{'title':'CIAAW abridged standard atomic weights 2024','url':'https://ciaaw.org/abridged-atomic-weights.htm'},{'title':'NIST evaluated atomic properties','url':'https://www.nist.gov/pml/periodic-table-elements'},{'title':'NIST Atomic Spectra Database','url':'https://physics.nist.gov/PhysRefData/ASD/Html/levelshelp.html'},{'title':'NIST electron configurations','url':'https://math.nist.gov/DFTdata/atomdata/configuration.html'}]
TOPICS=['atomic structure precision spectroscopy quantum electrodynamics','quantum vacuum zero point energy experimental constraints','many electron atoms density functional theory relativistic corrections','isotope shifts atomic clocks quantum measurement']
FORMULAS=[{'name':'Charge accounting','equation':'Q = (Z − N_e)e','status':'Established charge accounting; neutral atom uses N_e = Z.'},{'name':'Photon conversion','equation':'E = hf; λ = c/f','status':'Established; requires a specified transition energy.'},{'name':'Hydrogenic energy','equation':'E_n ≈ −13.605693 Z²/n² eV','status':'Nonrelativistic, infinite-nuclear-mass one-electron approximation. Not a neutral multi-electron spectrum.'},{'name':'Hydrogenic radius scale','equation':'r_n ≈ a₀ n²/Z','status':'Bohr-model scale for a one-electron ion, not an orbital trajectory.'},{'name':'Oscillator zero-point energy','equation':'E₀ = ½ℏω = ½hf','status':'Quantum harmonic oscillator model; frequency must be specified. Not an extractable-energy claim.'},{'name':'Many-electron Hamiltonian','equation':'H = Σᵢ[pᵢ²/(2mₑ) − Ze²/(4πε₀rᵢ)] + Σᵢ<ⱼ e²/(4πε₀rᵢⱼ)','status':'Nonrelativistic fixed-nucleus Coulomb model. Catalogue entry; no many-body solver implemented.'},{'name':'Further research','equation':'Reduced-mass, fine/hyperfine, relativistic, QED and nuclear corrections; correlation and DFT','status':'Research topics requiring specified models, uncertainties and independent comparison.'}]
def calculate(z,n=1,frequency_hz=7.83):
 if type(z)is not int or not 1<=z<=118:raise ValueError('Atomic number must be 1–118')
 if type(n)is not int or not 1<=n<=20:raise ValueError('Level n must be 1–20')
 if type(frequency_hz) not in (int,float) or not math.isfinite(frequency_hz) or not 0<frequency_hz<=1e25:raise ValueError('Frequency must be finite and positive, up to 1e25 Hz')
 energy=-13.605693*z*z/(n*n);transition=13.605693*z*z*(1/(n*n)-1/((n+1)**2));freq=transition*EV/H
 return {'z':z,'n':n,'electrons_in_model':1,'ion_charge_e':z-1,'level_energy_ev':energy,'radius_scale_m':5.29177210903e-11*n*n/z,'next_level_transition_ev':transition,'transition_frequency_hz':freq,'transition_wavelength_m':C/freq,'oscillator_frequency_hz':frequency_hz,'oscillator_zero_point_j':.5*H*frequency_hz,'checks':{'finite':all(math.isfinite(v) for v in (energy,transition,freq)), 'photon_roundtrip_relative_error':abs((H*freq/EV)-transition)/transition},'model_scope':'One-electron ion approximation; high-Z relativistic corrections omitted. Oscillator frequency is an independent model input.'}
class PeriodicStudy:
 def __init__(self):
  self.elements=json.loads((Path(__file__).resolve().parent.parent/'assets/periodic_elements.json').read_text(encoding='utf-8'));self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.next_research=0;self.next_results=0;self.events=[];self.updates=[];self.research_status={}
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  self.next_at=now+2
  element=self.elements[self.sequence%118];self.sequence+=1;result=calculate(element['z'],1+self.sequence%4)
  record={'sequence':self.sequence,'time':time.time(),'element':element,'calculation':result,'steps':['Select source-labelled element','Specify one-electron model and level','Calculate energy, wavelength and radius scale','Check units, finiteness and photon round trip','Publish bounded numerical feedback'],'ethical_study':study_frame('periodicstudy',self.sequence),'execution':'Local numerical study only','next_check':'Compare model transitions with independently evaluated spectra; do not overwrite measured data with this approximation.'}
  with self.lock:self.events=(self.events+[record])[-48:]
  research=getattr(getattr(c,'software_theory',None),'research',None)
  if research and now>=self.next_research:
   topic=TOPICS[(self.sequence//118)%len(TOPICS)];self.next_research=now+3600
   try:
    receipt=research.request('[recent] '+topic);rows=research.retrieve('atomic quantum spectroscopy')
    with self.lock:self.updates=rows[:12];self.research_status={'scheduled':receipt,'topic':topic,'checked':time.time(),'interval_seconds':3600,'scope':'Periodically requested scholarly metadata; no claim of continuous coverage or verified discovery.'}
   except Exception as e:
    with self.lock:self.research_status={'status':'unavailable','error':str(e)[:160]}
  if research and now>=self.next_results:
   self.next_results=now+60
   try:
    rows=research.retrieve('atomic quantum spectroscopy')
    with self.lock:self.updates=sorted(rows,key=lambda row:str(row.get('published','')),reverse=True)[:12]
   except Exception:pass
  c.bus.publish({'origin':'periodic-study','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'atomic_number':element['z'],'model_energy_ev':result['level_energy_ev'],'photon_check_error':result['checks']['photon_roundtrip_relative_error'],'provenance':'CIAAW-element-and-labelled-hydrogenic-calculation','predefined_text':True,'stochastic':False,'processing_receipt':False}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'elements':self.elements,'events':copy.deepcopy(self.events),'updates':copy.deepcopy(self.updates),'research_status':copy.deepcopy(self.research_status),'sources':SOURCES,'formulas':FORMULAS,'scope':'118 source-labelled element identities and abridged weights; bounded equation catalogue and worked approximations, not all atomic knowledge or a complete quantum solver.'}

 def sphere(self,c):
  with c.lock:sources=copy.deepcopy(list(c.sources.values()));goal=c.goal
  with self.lock:events=copy.deepcopy(self.events[-16:]);updates=copy.deepcopy(self.updates);sequence=self.sequence
  records=[]
  for source in sources:
   facts=source.get('facts',[])
   if facts:
    records.append({'source':source['source'],'parent_event':source.get('parent_event'),'path':facts[sequence%len(facts)].get('path',[]),'observed_value':facts[sequence%len(facts)].get('value'),'hypothesis':'Could this captured feature provide a useful input, constraint or test for the selected atomic model?','test':'Define units and an independent expected result before combining unrelated quantities.','status':'Candidate relevance question; no physical coupling inferred.'})
  for event in events:records.append({'source':'periodic-study','parent_event':event['sequence'],'path':['element',event['element']['symbol']],'calculation':event['calculation'],'hypothesis':'Compare the one-electron approximation with evaluated transitions and study omitted corrections.','test':event['next_check'],'ethical_study':event['ethical_study']})
  for row in updates[:8]:records.append({'source':row.get('source','research'),'parent_event':None,'path':['research',row.get('id')],'publication':row,'hypothesis':'Does this publication supply a relevant measured constraint or independently testable model?','test':'Read accessible primary material, identify assumptions, uncertainty and replication status.'})
  for model in FORMULAS:records.append({'source':'atomic-model-catalogue','parent_event':None,'path':['formula',model['name']],'model':model,'hypothesis':'Specify inputs and applicability; compare with an independent calculation or measurement.','test':model['status']})
  particles=[]
  for i,row in enumerate(records):
   y=1-2*(i+.5)/max(1,len(records));r=math.sqrt(max(0,1-y*y));angle=i*math.pi*(3-math.sqrt(5))
   particles.append({'id':'atomic-theory:'+str(i),'point':[r*math.cos(angle),y,r*math.sin(angle)],'phase':1.,'autonomy':0.,'selected':True,'expression_type':'source-linked-hypothesis','symbol':'?','value_preview':row['hypothesis'][:120],'source':row['source'],'parent_event':row.get('parent_event'),'path':row['path'],'record':row})
  return {'sequence':sequence,'particles':particles,'retained_sources':len(sources),'represented_values':len(records),'received_events':sequence,'goal':goal,'selected_phases':[1.],'thought_trace':records,'represented_forms':['captured values','calculations','research','model definitions','hypotheses'],'scope':'Whole-engine captured source index plus atomic study. Bounded candidate hypotheses and registered capabilities, not all possible knowledge, unobserved system access or external execution.'}
