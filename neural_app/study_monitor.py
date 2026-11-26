"""Read-only stream projections of the six study spheres, without extra workers."""
LANES=[('choice-study','Choice study'),('action-study','Action study'),('consequence-study','Consequence study'),('choice-action-consequence','Combined choice/action/consequence'),('mind-improvement','Mind improvement'),('source-study','Net discovery and inference')]
def view(c):
 frames=c.choice_action_study.view();frames['mind-improvement']=c.mind_improvement.sphere();frames['source-study']=c.source_study.sphere(c)
 banks=[];overview=[]
 for ident,title in LANES:
  frame=frames.get(ident,{});records=frame.get('thought_trace',[]);overview.append({'sphere':title,'cycle':frame.get('sequence',0),'records':len(records)})
  lanes=[{'id':'state','label':'State and coverage','value':{'cycle':frame.get('sequence',0),'captured_sources':frame.get('retained_sources',0),'records':len(records),'scope':frame.get('scope')}},{'id':'recent','label':'Current study records','value':records[-3:]},{'id':'tests','label':'Checks and experiment context','value':frame.get('experiments',frame.get('app_law',{}))},{'id':'network','label':'Source discovery status','value':frame.get('network_intake',{}).get('discovery',{})},{'id':'budget','label':'Rate and processing budget','value':frame.get('rate_control',c.active_thought.view()['policy'])},{'id':'provenance','label':'Source lineage','value':[{'source':r.get('source',r.get('url')),'event':r.get('event',r.get('parent_event')),'kind':r.get('kind')} for r in records[-8:]]}]
  banks.append({'id':ident,'label':title,'lanes':lanes})
 return {'sequence':sum(row['cycle'] for row in overview),'lanes':[{'id':row['sphere'],'label':row['sphere'],'value':row} for row in overview],'streams':banks,'scope':'Read-only views of shared processing; no separate model workers.'}
