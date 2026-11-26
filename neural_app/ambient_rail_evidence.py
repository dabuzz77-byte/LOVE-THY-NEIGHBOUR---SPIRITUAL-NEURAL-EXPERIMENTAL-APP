"""Group representation observations without inventing a causal comparison."""
def compare_rails(checks):
 groups={}
 for source,check in checks.items():
  conditions=check.get('conditions') or {};rail=conditions.get('rail');parent=conditions.get('source')
  if rail not in ('ordered-source','random-sample','chain-transformed') or not isinstance(parent,str):continue
  groups.setdefault(parent,{})[rail]={'source':source,'capture_tick':conditions.get('capture_tick'),'status':check['status'],'heldout_gain_bits_per_byte':check.get('gain_bits_per_byte'),'adaptive_prediction':check.get('adaptive_prediction'),'temporal_prediction':check.get('temporal_prediction')}
 result=[]
 for parent,rails in list(groups.items())[-8:]:
  ticks={r['capture_tick'] for r in rails.values()};paired=len(rails)==3 and len(ticks)==1 and None not in ticks
  temporal={name:(row.get('temporal_prediction') or {}) for name,row in rails.items()}
  ready=paired and all(v.get('prior_captures',0)>=2 for v in temporal.values())
  gains={name:v.get('relative_error_reduction') for name,v in temporal.items()}
  useful=lambda name:gains.get(name) is not None and gains[name]>.05
  assessment='await-matched-fresh-captures' if not ready else 'source-pattern-predictable' if useful('ordered-source') else 'predictability-only-in-transformed-rail' if useful('chain-transformed') else 'no-confirmed-temporal-gain'
  result.append({'source':parent,'status':'matched-capture' if paired else 'waiting-for-matched-rails','rails':rails,'representation_assessment':{'status':assessment,'own_target_error_reductions':gains,'same_prediction_target':False,'scope':'Each rail predicts its own representation. These scores cannot establish that transformation improves prediction of the original source; that requires a shared-target experiment.'},'scope':'Different representations of a named software source. A transformation can introduce predictable structure; its gain alone is not evidence of information in the original source or a physical origin.'})
 return result
