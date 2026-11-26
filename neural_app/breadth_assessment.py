"""Read an attributable, bounded assessment; never manufacture a capability grade."""
import json,hashlib
from pathlib import Path

def view():
 folder=Path(__file__).resolve().parent.parent/'assessments'
 path=folder/'native-breadth-current.json'
 if not path.exists():path=folder/'native-breadth-v1.json'
 if not path.exists():return {'status':'not-measured','answer':'No external reasoning assessment is installed.','general_reasoning_established':False,'model_calls':0}
 if path.stat().st_size>65536:raise ValueError('Reasoning assessment exceeds its size budget')
 report=json.loads(path.read_text(encoding='utf-8'))
 result=report.get('evaluation',{});audit=report.get('audit',{});domains=result.get('domains',{})
 if not isinstance(domains,dict) or not domains or any(type(r.get('passed'))is not int or type(r.get('total'))is not int or not 0<=r['passed']<=r['total'] for r in domains.values()):raise ValueError('Malformed external reasoning assessment')
 if result.get('total')!=sum(r['total'] for r in domains.values()) or result.get('passed')!=sum(r['passed'] for r in domains.values()):raise ValueError('Assessment totals do not match its domain records')
 app=Path(__file__).resolve().parent
 current_hash=hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sorted(app.glob('*.py')))).hexdigest()
 current=report.get('code_sha256')==current_hash
 lines=['**Native reasoning breadth assessment**',str(result['passed'])+'/'+str(result['total'])+' on the frozen external evaluation set.',str(audit.get('passed'))+'/'+str(audit.get('total'))+' on the separate audit set.']
 if report.get('assessment_kind')=='regression-of-previously-evaluated-questions':lines.insert(1,'This is a compatibility rerun on previously evaluated questions, not a fresh held-out assessment of the latest features.')
 lines+=['- '+name.replace('_',' ')+': '+str(row['passed'])+'/'+str(row['total']) for name,row in domains.items()]
 lines+=['Broad general reasoning is not established. These are public, locally administered tests of supported task families; targets were not passed to the app.','Next priority: general language interpretation, causal judgment, ambiguity handling and transfer to unfamiliar task forms.']
 if not current:lines.insert(1,'This assessment belongs to a different code version. Rerun it before treating the figures as current.')
 return {**report,'status':'measured-limited' if current else 'stale-assessment','assessment_matches_current_code':current,'answer':'\n\n'.join(lines),'general_reasoning_established':False,'model_calls':0}
