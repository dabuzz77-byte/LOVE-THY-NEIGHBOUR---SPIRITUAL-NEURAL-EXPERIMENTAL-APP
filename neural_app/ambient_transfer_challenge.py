"""Source-seeded unfamiliar numerical tasks, separate from reference physics."""
import hashlib,math,random
from .ambient_noisy_learning import controlled_fit

def challenge(raw,serial=0):
 if not raw:return {'status':'waiting-for-generated-input'}
 digest=hashlib.sha256(bytes(raw[:256])+str(serial).encode()).hexdigest()
 rng=random.Random(int(digest[:16],16))
 # Only the environment sees these parameters; the learner receives observations.
 coefficient=math.exp(rng.uniform(-1,2));p=rng.uniform(-2.3,2.3);q=rng.uniform(-2.3,2.3)
 def environment(x,z):return coefficient*x**p*z**q
 training=[(x,z,environment(x,z)*math.exp(rng.uniform(-.01,.01))) for x in (.7,1.3,2.6,4.1) for z in (.8,1.7,3.2)]
 validation=[(x,z,environment(x,z)) for x,z in ((.9,2.1),(1.9,.6),(3.3,2.7),(5.2,4.3))]
 result=controlled_fit(training,validation)
 transfer=[]
 if result['status']=='heldout-supported':
  model=result['model']
  for x,z in ((6.1,1.1),(2.2,5.7),(7.3,6.4),(1.1,7.1)):
   predicted=model['coefficient']*x**model['powers'][0]*z**model['powers'][1];observed=environment(x,z)
   error=abs(math.log(predicted/observed));transfer.append({'inputs':[x,z],'predicted':predicted,'observed':observed,'absolute_log_error':error,'passed':error<.08})
 from .ambient_family_selection import select,investigate,expand_family
 # A separate mixed-family task; its family label is not passed to selection.
 affine=bool(serial%2)
 def mixed(x,z):return coefficient+.8*x+1.7*z if affine else environment(x,z)
 train=[(x,z,mixed(x,z)) for x in (.7,1.3,2.6,4.1) for z in (.8,1.7,3.2)]
 choose=[(x,z,mixed(x,z)) for x,z in ((.9,2.1),(1.9,.6),(3.3,2.7),(5.2,4.3))]
 test=[(x,z,mixed(x,z)) for x,z in ((6.1,1.1),(2.2,5.7),(7.3,6.4),(1.1,7.1))]
 mixed_result=select(train,choose,test)
 def unknown(x,z):return 2+x*x+3*z*z
 unsupported=select([(x,z,unknown(x,z)) for x in (1,2,3,4) for z in (1,2,3)],[(x,z,unknown(x,z)) for x,z in ((.5,4),(5,.5),(6,4),(4,6))],[(x,z,unknown(x,z)) for x,z in ((7,2),(8,3),(9,4),(10,5))])
 active_investigation=investigate([(x,z,unknown(x,z)) for x in (1,2,3,4) for z in (1,2,3)],[(x,z,unknown(x,z)) for x,z in ((.5,4),(5,.5),(6,4),(4,6))],[(x,z,unknown(x,z)) for x,z in ((7,2),(8,3),(9,4),(10,5))],unknown,budget=2)
 expanded=expand_family([(x,z,unknown(x,z)) for x in (1,2,3,4) for z in (1,2,3)],[(x,z,unknown(x,z)) for x,z in ((.5,4),(5,.5),(6,4),(4,6))],[(x,z,unknown(x,z)) for x,z in ((7,2),(8,3),(9,4),(10,5))])
 def beyond(x,z):return 3+x**3+z**3
 unresolved=expand_family([(x,z,beyond(x,z)) for x in (1,2,3,4) for z in (1,2,3)],[(x,z,beyond(x,z)) for x,z in ((.5,4),(5,.5),(6,4),(4,6))],[(x,z,beyond(x,z)) for x,z in ((7,2),(8,3),(9,4),(10,5))])
 summary={'supported_family':expanded.get('result',{}).get('selected_model',{}).get('family') if expanded.get('result',{}).get('selected_model') else None,'expansion_verified':expanded.get('result',{}).get('status')=='reserved-test-supported','remaining_unknown':unresolved.get('result',{}).get('status')!='reserved-test-supported','next_question':'Seek an explanation for the higher-order trial; current families are insufficient','scope':'Synthetic numerical trials, not evidence of a cosmic signal'}
 from .ambient_source_ablation import compare,budget_comparison
 ablation=compare(raw,serial)
 return {'budget_comparison':budget_comparison(raw,serial),'source_ablation':ablation,'learning_summary':summary,'higher_order_trial':unresolved,'family_expansion':expanded,'active_family_investigation':active_investigation,'unsupported_family_trial':unsupported,'family_selection':mixed_result,'status':'unfamiliar-task-transfer-supported'  if transfer and all(r['passed'] for r in transfer) else 'not-supported','task_digest':digest,'fit':result,'reserved_transfer':transfer,'target_parameters_supplied_to_learner':False,'model_calls':0,'scope':'Generated power-product task family with continuous exponents; not independent general intelligence or physical zero-point evidence'}
