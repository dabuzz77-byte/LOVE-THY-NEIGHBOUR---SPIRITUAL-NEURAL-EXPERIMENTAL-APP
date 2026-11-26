"""Conversational transfer and noncommitting experiments on verified data work."""
import copy,json,re

def respond(text,work):
    key=text.strip().casefold().rstrip('?.!')
    explaining=key in ('explain my last data task','explain the data steps','what did you do to the data') or key=='explain that' and work.state.get('focus_kind')=='workflow'
    match=re.fullmatch(r'(same task with|repeat last data workflow with|what if the input were|compare the same task with):\s*([\s\S]+)',text.strip(),re.I)
    edit=re.fullmatch(r'replace data step (\d+) with:\s*(.+)',text.strip(),re.I)
    if not match and not edit and not explaining:return None
    from .native_work import digest,parse_steps,read_value
    from .reasoning_engine import pipeline
    from .workflow_contracts import equivalent
    workflow=work.state.get('workflow');receipts=work.state.get('receipts',[])
    if not workflow or not receipts:return {'status':'needs-input','answer':'Complete a data workflow first; there is no recorded data procedure to reuse.','model_calls':0}
    receipt=receipts[-1]
    if receipt.get('input_sha256')!=digest(workflow['input']) or receipt.get('output_sha256')!=digest(workflow['output']) or receipt.get('steps')!=workflow['steps']:raise ValueError('Retained workflow no longer matches its checked receipt')
    baseline=pipeline(copy.deepcopy(workflow['input']),copy.deepcopy(workflow['steps']))
    if not equivalent(baseline['result'],workflow['output']):raise ValueError('Replayed baseline differs from its retained result')
    if explaining:
        lines=['Rechecked the saved pure-data operations against their receipt. No saved result was changed.'];details=[];before=copy.deepcopy(workflow['input'])
        for step,row in zip(workflow['steps'],baseline['trace']):
            after=row['result'];description=step['op']
            if step['op']=='filter':description='Keep '+('field '+step['field']+' ' if step.get('field') is not None else 'values ')+step.get('relation','equal')+' '+json.dumps(step['value'],ensure_ascii=False)
            elif step['op']=='field':description='Extract field '+step['name']
            elif step['op']=='group':description='Group by '+step['field']+' and calculate '+step.get('aggregate','count')+(' of '+step['value_field'] if step.get('value_field') else '')
            elif step['op']=='sort':description='Sort '+('by '+step['field']+' ' if step.get('field') else '')+('descending' if step.get('descending') else 'ascending')
            details.append({'step':row['step'],'description':description,'input_count':len(before) if isinstance(before,(list,str,dict)) else None,'output_count':len(after) if isinstance(after,(list,str,dict)) else None,'output':copy.deepcopy(after),'independent_check':row['independent_check']})
            lines.append(str(row['step'])+'. '+description+' → '+json.dumps(after,ensure_ascii=False)[:600]);before=after
        return {'status':'complete','answer':'\n\n'.join(lines),'data_explanation':details,'saved_state_changed':False,'model_calls':0}
    steps=copy.deepcopy(workflow['steps']);value=copy.deepcopy(workflow['input'])
    if edit:
        index=int(edit[1])-1;replacement=parse_steps(edit[2])
        if not 0<=index<len(steps) or not replacement or len(replacement)!=1:raise ValueError('Replace one existing data step with exactly one supported pure-data operation')
        steps[index]=replacement[0];mode='commit'
    else:
        value=read_value(match[2]);mode='compare' if match[1].casefold().startswith(('what if','compare')) else 'commit'
    result=pipeline(copy.deepcopy(value),steps)
    report={'baseline_input':copy.deepcopy(workflow['input']),'baseline_output':copy.deepcopy(workflow['output']),'candidate_input':copy.deepcopy(value),'candidate_output':copy.deepcopy(result['result']),'steps':steps,'output_changed':not equivalent(workflow['output'],result['result']),'hypothetical':mode=='compare','model_calls':0}
    if mode=='compare':return {'status':'complete','answer':'Noncommitting data experiment:\n'+json.dumps(report,ensure_ascii=False,indent=2),'workflow_comparison':report,'committed':False,'model_calls':0}
    return {**work.commit(text,result['result'],steps,result),'workflow_comparison':report,'committed':True,'model_calls':0}
