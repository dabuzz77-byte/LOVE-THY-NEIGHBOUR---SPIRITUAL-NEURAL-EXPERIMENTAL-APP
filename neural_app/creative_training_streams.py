"""Six factual projections of each creative trainer's current practice state."""
def streams(c,kind):
 services={'document':c.document_trainer,'art':c.art_trainer,'music':c.music_trainer,'game':c.game_trainer}
 if kind not in services:raise ValueError('Unknown trainer')
 service=services[kind]
 # Avoid rescanning plugins or duplicating full inventories on stream polls.
 sequence=service.sequence;latest=dict(service.latest)
 from .free_learning import resources
 courses=resources(kind)
 selected=courses[sequence%len(courses)] if courses else {}
 rows=[('Task',{'trainer':kind,'practice_cycle':sequence,'exercise':latest.get('type',latest.get('test','Waiting for first practice'))}),('Concepts',{'free_learning':selected,'basis':{'document':'OpenDocument structure and editorial review','art':'Transforms and scene construction','music':'Sequencing, synthesis and PCM representation','game':'Gameplay rules and finite level state'}[kind]}),('Construction',latest),('Checks',{'passed':latest.get('passed'),'test':latest.get('test'),'cycle':sequence}),('Revision',{'next':'Investigate a failed check; otherwise vary the next bounded practice fixture.','status':'No automatic quality improvement claimed from repetition alone.'}),('Retained results',{'completed_cycles':sequence,'latest_observation':latest,'learning_kind':'Native practice and structural/numerical tests; no model weight update'})]
 return {'automatic':True,'practice_status':{'cycle':sequence,'passed':latest.get('passed'),'test':latest.get('test'),'trainer':kind},'resources':courses,'sequence':sequence,'lanes':[{'id':str(i),'label':name,'value':value} for i,(name,value) in enumerate(rows)],'streams':[{'id':'practice-'+str(i),'label':name,'lanes':[{'id':'focus','label':'Focus','value':value},{'id':'observation','label':'Latest practice result','value':latest},{'id':'progress','label':'Cycle and test status','value':{'cycle':sequence,'passed':latest.get('passed'),'origin':'Native bounded exercise; repeated fixtures remain repeated practice'}}]} for i,(name,value) in enumerate(rows)]}
