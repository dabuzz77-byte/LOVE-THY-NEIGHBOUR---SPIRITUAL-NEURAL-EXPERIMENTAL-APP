"""Prayer-guided consequence rehearsal; assessment never grants external access."""
import copy,time,collections
from .causal_assessment import compare

class ConsequenceThought:
 def __init__(self):
  self.history=collections.deque(maxlen=48);self.sequence=0;self.next_at=0;self.pending=[]
 def consider(self,scenario):
  if not isinstance(scenario,dict):raise ValueError('Scenario must be an object')
  result=compare(scenario)
  urgency=scenario.get('urgency_seconds')
  if urgency is not None and (type(urgency) not in (int,float) or not 0<=urgency<=31536000):raise ValueError('Urgency must be finite seconds within one year')
  authority=scenario.get('authority','unconfirmed');operation=scenario.get('operation','thought-experiment')
  local=operation in ('calculation','pure-procedure','in-memory-test','thought-experiment')
  result.update(question=str(scenario.get('question','Compare protection, action, inaction and repair'))[:2000],urgency_seconds=urgency,authority=authority,
   action_readiness='ready for bounded local experiment' if local else 'requires the relevant authority and an operation-specific safety check',
   evidence_policy='Missing evidence is an uncertainty to investigate, not proof of evil and not an automatic veto on bounded local experiments.',
   gravity={'priority':'Protect life and essential needs, especially the person most exposed to harm.','delay':'Compare the consequences of waiting explicitly; delay can itself cause serious harm.','effectiveness':'A protective intention and an effective protective action are distinct questions.','proportion':'Compare timely alternatives, failure modes, collateral effects and stopping conditions.'},
   prayer='Provision; protection from evil; forgiveness and repair; accountable power; humility about unknown outcomes.',
   next_thoughts=['What threatens whom, and how soon?','Which action can reduce the threat in time?','What happens if we wait?','What is reversible, and what could fail?','Which observation would change this decision?'],
   execution='Assessment only; no device or network action is executed by this layer.')
  self.sequence+=1;result.update(sequence=self.sequence,time=time.time());self.history.append(copy.deepcopy(result));return result
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+10
  # Controlled bit-system rehearsal: retaining a beneficial bit versus correcting a harmful state.
  n=self.sequence%2;before={'essential_service':1,'fault':n};after={**before,'fault':0}
  scenario={'question':'Correct a simulated fault while preserving an essential service','operation':'in-memory-test','authority':'local controlled experiment','claimed':'good','evidence':'observed-test','effects':{'benefit':n,'harm':0},'wait_scenario':{'claimed':'good','evidence':'observed-test','effects':{'benefit':0,'harm':n}},'correction_scenario':{'claimed':'good','evidence':'observed-test','effects':{'benefit':n,'harm':0}}}
  result=self.consider(scenario);result['local_test']={'before':before,'after':after,'service_preserved':after['essential_service']==1,'fault_removed':after['fault']==0}
  self.history[-1]=copy.deepcopy(result)
  c.bus.publish({'origin':'consequence-thought','target':'all','kind':'stage-output','payload':{'assessment':result,'stochastic':False,'predefined_text':True,'provenance':'controlled-consequence-rehearsal'}})
 def view(self):return {'sequence':self.sequence,'latest':copy.deepcopy(self.history[-1]) if self.history else {},'recent':list(self.history),'scope':'Four-way consequence reasoning and controlled local rehearsals; world outcomes are compared as projections until observed.'}
