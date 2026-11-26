"""Compact read-only state for the layered live work display."""
def view(runtime):
    from .infrastructure_lab import process
    flow=runtime.automatic_flow().view();workers=runtime.inference_workers().view();research=runtime.research.view()
    atlas=getattr(runtime,'_source_atlas',None);native=atlas.continuous if atlas else {'enabled':False,'loaded':0,'observations':0}
    books=getattr(runtime,'_four_texts',None)
    return {'automatic':flow,'workers':workers,'research':{'enabled':research['enabled'],'completed':research['completed_topics'],'topics':len(research['queries']),'errors':sum(v.get('processing')=='error' for v in research['topics'].values())},'sources':books.view() if books else {'processed_chunks':0,'total_chunks':0},'google':runtime.google_index.view(),'field':runtime.field.snapshot(),'learning':runtime.learning_view(),'gates':runtime.gates.view(),'resources':runtime.metrics(),'native_modules':dict(native),'infrastructure':process(runtime,{}),'scope':'Measured local work, explicitly configured service exchanges, and separately labelled model scenarios. No worldwide device membership is inferred.'}
