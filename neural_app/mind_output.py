"""Observable processing summaries for a multi-lane terminal; not fabricated narration."""
def snapshot(c):
 investigations=c.investigations.view();experiment=c.experiment_sphere.latest;latest=c.synthesis_sphere.latest;controller=c.self_controller.view();resources=c.adaptive_rail.view()
 sources=[{'source':r['source'],'event':r['parent_event'],'facts':r['facts'][:2]} for r in list(c.sources.values())[-4:]]
 return {'sequence':c.sequence,'lanes':[
 {'id':'goal','label':'Goal','value':{'goal':c.goal}},
 {'id':'selection','label':'Native self-selection','value':controller},
 {'id':'memory','label':'Working observations','value':sources},
 {'id':'candidates','label':'Selected generated values','value':list(c.generation_selector.last.values())[-2:]},
 {'id':'experiments','label':'Experiments / counterexamples','value':list(c.experiment_sphere.history)[-3:]},
 {'id':'transfer','label':'Rules / transfer checks','value':{'rules':c.experiment_sphere.skills,'procedures':investigations.get('learned_procedures',[])[:4]}},
 {'id':'forecast','label':'Prediction and error','value':{'models':c.experiment_sphere.forecast_scores,'errors':list(c.experiment_sphere.errors)[-3:]}},
 {'id':'evidence','label':'Investigations / evidence','value':[{'id':r['id'],'question':r['question'],'status':r['status'],'conclusion':r['conclusion']} for r in investigations['items'][:3]]},
 {'id':'assessment','label':'Prayer / four-way assessment','value':[{'id':r['id'],'assessment':r.get('consequence_assessment',r.get('assessment'))} for r in investigations['items'][:2]]},
 {'id':'symbols','label':'Character potential / selection','value':_symbols()},
 {'id':'resources','label':'CPU / GPU / RAM','value':{'metrics':resources.get('resource_metrics'),'interval':resources.get('adaptive_interval_seconds'),'gpu':resources.get('gpu')}},
 {'id':'health','label':'Verification / errors','value':{'errors':c.errors,'last_error':c.last_error,'receipts':list(c.receipts)[-3:],'synthesis_tests':c.synthesis_sphere.coverage}}],
 'scope':'Recorded native-controller activity, source-linked candidates and verified software results. Repeated snapshots are deduplicated by the display.'}

def _symbols():
 from .symbol_bus import BUS
 state=BUS.view();return {'latest_set':state['set_selection'],'recent_points':state['recent'][-2:]}
