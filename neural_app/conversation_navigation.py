"""Explicit topic navigation and answer repair over recorded native results."""
import copy,re

def respond(text,state):
    key=text.strip().casefold().rstrip('?.!')
    if key=='resume app readings' or state.get('focus_kind')=='app-reading-answer' and key in ('why','explain that','why is this verified','explain result plainly','what are you thinking','what is your thought process','explain your reasoning'):
        from .native_reading_knowledge import respond as reading_knowledge
        return reading_knowledge(text,state)
    if key in ('research and forecast assessment','native upgrade report'):
        import hashlib,json
        from pathlib import Path
        folder=Path(__file__).resolve().parent
        path=folder.parent/'assessments/native-c-area-upgrade.json'
        if not path.exists():return {'status':'not-measured','answer':'No current upgrade assessment is installed.','model_calls':0}
        report=json.loads(path.read_text(encoding='utf-8'))
        current=all((folder/name).is_file() and hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest for name,digest in report['code_sha256'].items())
        return {'status':'measured-limited' if current else 'stale-assessment','answer':f"Native research/conversation/forecast upgrade: {report['passed']}/{report['tests']} scoped tests passed.\n\n"+report['scope']+'\n\n'+report['reason']+('' if current else '\nThis report belongs to an older code version.'),'assessment':report,'assessment_matches_current_code':current,'model_calls':0}
    if key in ('resume research','back to research','switch back to research'):
        report=state.get('evidence_report')
        if not report:return {'status':'needs-input','answer':'No research topic is retained. Start with research brief: QUESTION and one or more Source passages.','model_calls':0}
        from .evidence_workbench import render
        state['focus_kind']='evidence-research'
        return {'status':report['status'],'answer':render(report),'research':copy.deepcopy(report),'model_calls':0}
    if key in ('resume comparison','back to comparison','resume decision'):
        current=state.get('practical_decision')
        if not current:return {'status':'needs-input','answer':'No practical comparison is retained. Supply named options with costs or times and a question.','model_calls':0}
        from .practical_decisions import render
        state['focus_kind']='practical-decision'
        return {'status':current['report']['status'],'answer':render(current['report']),'model_calls':0}
    if key in ('resume reading','back to reading','resume summary'):
        current=state.get('reading_dialogue')
        if not current:return {'status':'needs-input','answer':'No document discussion is retained. Supply summarise this: followed by your text.','model_calls':0}
        state['focus_kind']='reading-dialogue'
        return {'status':'complete','answer':'Retained source sentences:\n\n'+'\n\n'.join('['+str(r['sentence'])+'] '+r['text'] for r in current['report']['extracts']),'model_calls':0}
    if key in ('resume forecast','back to forecast','switch back to forecasting'):
        report=state.get('validated_forecast')
        if not report:return {'status':'needs-input','answer':'No forecast is retained. Supply forecast: followed by a numeric JSON list.','model_calls':0}
        from .validated_forecast import render
        state['focus_kind']='validated-forecast'
        return {'status':'forecast','answer':render(report),'forecast':copy.deepcopy(report),'model_calls':0}
    if key in ('new topic','start a new topic'):
        if state.get('open_reasoning'):
            state['open_reasoning_history']=(state.get('open_reasoning_history',[])+[copy.deepcopy(state.pop('open_reasoning'))])[-3:]
        state['focus_kind']='none'
        # Retain resumable work, but prevent the previous topic consuming the next request.
        return {'status':'needs-input','answer':'Ready for a new question or task. Earlier research and forecasts remain available with “resume research” or “resume forecast”.','model_calls':0}
    if key in ('list conversation topics','what topics can i resume'):
        topics=[]
        if state.get('evidence_report'):topics.append('Research: '+state['evidence_report']['question']+' — say “resume research”.')
        if state.get('validated_forecast'):topics.append('Forecast: '+state['validated_forecast']['label']+' — say “resume forecast”.')
        if state.get('practical_decision'):topics.append('Comparison: '+str(state['practical_decision']['model']['question'])+' — say “resume comparison”.')
        if state.get('reading_dialogue'):topics.append('Document discussion — say “resume reading”.')
        if state.get('concept_conversation'):topics.append('Concept discussion — say “resume discussion”.')
        if state.get('app_reading_answer'):topics.append('App readings: '+state['app_reading_answer']['question']+' — say “resume app readings”.')
        if state.get('open_reasoning'):topics.append('Reasoning: '+state['open_reasoning']['question']+' — say “open reasoning status”.')
        return {'status':'complete','answer':'\n\n'.join(topics) if topics else 'No resumable reasoning topic has been recorded yet.','model_calls':0}
    if key in ('why','why is that','explain that','what do you mean','what do you mean by that'):
        if state.get('focus_kind')=='evidence-research':
            from .evidence_workbench import render
            report=state['evidence_report'];deduction=report.get('deduction') or {}
            lines=[render(report),'The source references identify the exact supplied passages. Matching words rank passages; parsed facts and explicit universal rules support only the displayed conditional deductions.']
            if deduction.get('source_rules'):lines+=['Rules used or available:']+['['+r['source']+'] '+r['text'] for r in deduction['source_rules']]
            return {'status':report['status'],'answer':'\n\n'.join(lines),'model_calls':0}
        if state.get('focus_kind')=='validated-forecast':
            from .validated_forecast import render
            report=state['validated_forecast']
            return {'status':'complete','answer':render(report)+'\n\nThe method was selected using earlier forecast errors. Later observations were reserved for evaluation. An extrapolation can still fail when the generating process changes.','model_calls':0}
    return None
