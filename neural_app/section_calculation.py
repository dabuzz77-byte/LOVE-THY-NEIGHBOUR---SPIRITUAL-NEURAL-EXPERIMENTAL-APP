"""Shared bounded arithmetic service for every registered section and captured path."""
import ast,math,time
from .branch_reasoning import arithmetic,equivalent
from .native_skills import calculate
from .native_workbench import CHAIN
def run(body,circuit):
 expression=str(body.get('expression',''))
 if not expression or len(expression)>2048:raise ValueError('Provide a calculation up to 2048 characters')
 stage=str(body.get('stage','all'))
 if stage!='all' and stage not in circuit.element_thinking.layers:raise ValueError('Choose an Intelligence Engine section')
 values=dict(body.get('variables',{}));source=body.get('source');path=body.get('path');lineage={'source':source,'path':path,'stage':stage}
 if source:
  with circuit.lock:row=circuit.sources.get(source)
  if not row:raise ValueError('Captured source is unavailable')
  fact=next((f for f in row['facts'] if f['path']==path),None)
  if fact is None:raise ValueError('Captured source path is unavailable')
  values['value']=fact['value'];lineage['parent_event']=row['parent_event']
 elif 'value' not in values:
  with circuit.lock:chosen=circuit.generation_selector.last.get(stage)
  if chosen:values['value']=chosen['value'];lineage.update(selected_source=chosen['source'],selection=chosen['selection'])
 for name,value in values.items():
  if not isinstance(name,str) or not name.isidentifier() or type(value) not in (int,float) or not math.isfinite(value) or abs(value)>=1e12:raise ValueError('Bind finite numeric variables below 1e12')
 tree=ast.parse(expression,mode='eval')
 if len(list(ast.walk(tree)))>64:raise ValueError('Calculation is too large')
 class Bind(ast.NodeTransformer):
  def visit_Name(self,node):
   if node.id not in values:raise ValueError('Missing numeric variable: '+node.id)
   return ast.copy_location(ast.Constant(values[node.id]),node)
 resolved=ast.unparse(Bind().visit(tree));actual=calculate(resolved);expected=arithmetic(resolved);verified=equivalent(actual,expected)
 result={'stage':stage,'expression':expression,'resolved_expression':resolved,'variables':values,'result':actual,'verified':verified,'lineage':lineage,'chain_context':CHAIN,'time':time.time(),'scope':'Native arithmetic on explicit/captured numeric inputs; chain is guiding context, not an invented numeric measurement'}
 with circuit.lock:circuit.action_definitions.record('native/calculate',resolved,actual,verified,stage,stage=stage)
 circuit.bus.publish({'origin':'section-calculation','target':'all','kind':'stage-output','payload':{'calculation_result':result,'text':str(actual),'stochastic':False,'provenance':'verified-native-calculation','bridge_direction':'all'}})
 return result
