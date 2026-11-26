"""Small test-driven mutation proposals, never automatic file replacement."""
import ast,copy,difflib,json,time,itertools
from .function_testing import test_function,isolated_source
from .workflow_contracts import equivalent

def repair(body):
 source=body.get('source');name=body.get('function');cases=body.get('cases')
 max_edits=body.get('max_edits',2)
 if type(max_edits)is not int or max_edits not in (1,2):raise ValueError('Choose one or two local edits per repair candidate')
 if not isinstance(cases,list) or not 3<=len(cases)<=16:raise ValueError('Supply 3 to 16 cases, reserving the last as a distinct validation example')
 baseline=test_function(body)
 if baseline.get('status') in ('invalid-syntax','unsupported-source'):return {'status':'source-not-testable','baseline':baseline,'source_changed':False,'host_access':False}
 if any(equivalent(cases[-1].get('args'),case.get('args')) for case in cases[:-1]):raise ValueError('Final validation arguments must differ from training arguments')
 if baseline['all_passed']:return {'status':'already-passing','baseline':baseline,'source_changed':False,'host_access':False}
 tree=ast.parse(source);nodes=list(ast.walk(tree));edits=[];known={'abs','len','min','max','sum','int','float','str','bool','sorted','range','isinstance'}
 selected_names={n.name for n in ast.parse(isolated_source(source,name)).body if isinstance(n,ast.FunctionDef)};allowed={id(child) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in selected_names for child in ast.walk(node)}
 known.update(n.name for n in nodes if isinstance(n,ast.FunctionDef));known.update(n.arg for n in nodes if isinstance(n,ast.arg) and id(n) in allowed);known.update(n.id for n in nodes if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store) and id(n) in allowed)
 for index,node in enumerate(nodes):
  if id(node) not in allowed:continue
  if isinstance(node,ast.BinOp):
   replacement={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.Mult:ast.Div,ast.Div:ast.Mult}.get(type(node.op))
   if replacement:edits.append((index,'op',replacement(),'arithmetic operator '+type(node.op).__name__+' → '+replacement.__name__))
  if isinstance(node,ast.Compare) and len(node.ops)==1:
   replacement={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}.get(type(node.ops[0]))
   if replacement:edits.append((index,'ops',[replacement()],'comparison boundary change'))
  if isinstance(node,ast.Constant) and type(node.value) is int and abs(node.value)<=1000000:
   for delta in (-1,1):edits.append((index,'value',node.value+delta,'integer boundary '+str(node.value)+' → '+str(node.value+delta)))
  if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load) and node.id not in known:
   for word in difflib.get_close_matches(node.id,sorted(known),n=2,cutoff=.72):edits.append((index,'id',word,'local name '+node.id+' → '+word))
 patches=[];raw=source.encode('utf-8');raw_lines=raw.splitlines(keepends=True)
 for index,field,value,reason in edits[:40]:
  original=nodes[index];candidate=copy.deepcopy(original);setattr(candidate,field,value);replacement=ast.unparse(ast.fix_missing_locations(candidate))
  if not isinstance(original,ast.Name):replacement='('+replacement+')'
  start=sum(map(len,raw_lines[:original.lineno-1]))+original.col_offset;end=sum(map(len,raw_lines[:original.end_lineno-1]))+original.end_col_offset
  patches.append({'start':start,'end':end,'replacement':replacement.encode('utf-8'),'reason':reason})
 singles=((p,) for p in patches);pairs=itertools.combinations(patches,2) if max_edits==2 else ()
 attempts=[];started=time.monotonic();seen=set()
 for changes in itertools.chain(singles,pairs):
  if len(attempts)>=160 or time.monotonic()-started>3:break
  ordered=sorted(changes,key=lambda p:p['start'])
  if any(a['end']>b['start'] for a,b in zip(ordered,ordered[1:])):continue
  proposed=raw
  for change in reversed(ordered):proposed=proposed[:change['start']]+change['replacement']+proposed[change['end']:]
  if proposed in seen:continue
  seen.add(proposed);proposed=proposed.decode('utf-8');reason='; '.join(p['reason'] for p in ordered)
  selected=test_function({**body,'source':proposed,'cases':cases[:-1]});attempts.append({'reason':reason,'edit_count':len(changes),'passed':selected['passed'],'total':selected['total']})
  if not selected['all_passed']:continue
  validation=test_function({**body,'source':proposed,'cases':cases[-1:]})
  if not validation['all_passed']:return {'status':'validation-failed','baseline':baseline,'attempts':attempts,'validation':validation,'source_changed':False,'scope':'Selected repair rejected; final example is not reused to select another repair','host_access':False}
  return {'status':'validated-proposal','source':proposed,'reason':reason,'edit_count':len(changes),'baseline':baseline,'training':selected,'validation':validation,'attempts':attempts,'diff':'\n'.join(difflib.unified_diff(source.splitlines(),proposed.splitlines(),fromfile='original',tofile='proposed',lineterm='')),'source_changed':False,'scope':'A bounded one- or two-edit candidate passed supplied training cases and one separate validation case; not a proof for all inputs','host_access':False}
 return {'status':'no-validated-repair','baseline':baseline,'attempts':attempts,'source_changed':False,'scope':'No validated local repair found within 160 candidates and the cooperative time budget; larger changes remain unsupported','host_access':False}
