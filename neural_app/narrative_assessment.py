"""Read the local, provenance-bearing story assessment without implying AGI."""
import hashlib,json
from pathlib import Path

def view():
 app=Path(__file__).resolve().parent;path=app.parent/'assessments/narrative-reasoning-current.json'
 try:
  if path.stat().st_size>100000:raise ValueError('Oversized report')
  report=json.loads(path.read_text(encoding='utf-8'))
 except (OSError,ValueError):return {'status':'unavailable','answer':'No completed story-reasoning assessment is installed.','model_calls':0}
 current=hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sorted(app.glob('*.py')))).hexdigest()==report.get('code_sha256')
 lines=['**Native story-reasoning assessment**',str(report['evaluation']['passed'])+'/'+str(report['evaluation']['total'])+' on the separate evaluation set; '+str(report['audit']['passed'])+'/'+str(report['audit']['total'])+' on the disjoint audit.', 'Six selected public synthetic story task families; no model calls. Questions and targets are kept outside the runtime engine.']
 if not current:lines.append('This report belongs to a different source version. Rerun checks before treating it as current.')
 lines+=['The first assessment was used to diagnose missing handover wording and zero/none output formatting. The final sets use different question indices, but share public task templates.','Broad general reasoning at A is not established by this result. Open language, causal judgment and broader transfer still need separate assessment.']
 return {**report,'status':'measured-limited' if current else 'stale-assessment','assessment_matches_current_code':current,'general_reasoning_established':False,'answer':'\n\n'.join(lines),'model_calls':0}
