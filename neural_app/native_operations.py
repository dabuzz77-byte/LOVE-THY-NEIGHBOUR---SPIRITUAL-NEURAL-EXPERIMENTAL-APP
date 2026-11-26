"""Shared pure-work operation contracts for execution, plans and introspection."""
import json,math

OPERATIONS={name:{} for name in ('strip','lower','upper','reverse','lines','words','json','csv','unique','count','sum','mean','median','minimum','maximum','numbers','frequencies')}
OPERATIONS.update({'take':{'required':['count']},'replace':{'required':['old','new']},'field':{'required':['name']},'sort':{'optional':['field','descending']},'join':{'optional':['separator']},'filter':{'required':['value'],'optional':['field','relation']},'scale':{'required':['value']},'add':{'required':['value']},'divide':{'required':['value']},'group':{'required':['field'],'optional':['aggregate','value_field']}})

def validate_steps(steps,allow_empty=False):
 if not isinstance(steps,list) or not (0 if allow_empty else 1)<=len(steps)<=12:raise ValueError('Use '+('0' if allow_empty else '1')+' to 12 transformation steps')
 if len(json.dumps(steps,allow_nan=False))>32768:raise ValueError('Operation parameters exceed 32 KB')
 for index,step in enumerate(steps):
  if not isinstance(step,dict) or not isinstance(step.get('op'),str) or step['op'] not in OPERATIONS:raise ValueError('Unknown native operation at step '+str(index+1))
  op=step['op']
  if any(key not in step for key in OPERATIONS[op].get('required',[])):raise ValueError('Missing required parameter for '+op+' at step '+str(index+1))
  if op in ('scale','add','divide') and (type(step['value']) not in (int,float) or abs(step['value'])>1e100 or not math.isfinite(step['value'])):raise ValueError(op+' needs a finite numeric value')
  if op=='take' and (type(step['count'])is not int or not 0<=step['count']<=512):raise ValueError('Take needs a count from 0 to 512')
  if op=='replace' and (not isinstance(step['old'],str) or not step['old'] or not isinstance(step['new'],str)):raise ValueError('Replace needs nonempty old text and replacement text')
  if op=='field' and not isinstance(step['name'],str):raise ValueError('Field requires a name')
  if op=='sort' and 'descending' in step and type(step['descending'])is not bool:raise ValueError('Sort descending must be a boolean')
  if op in ('sort','filter') and step.get('field') is not None and not isinstance(step['field'],str):raise ValueError('Field names must be text')
  if op=='filter' and step.get('relation','equal') not in ('equal','greater','less','at_least','at_most','contains'):raise ValueError('Unknown filter relation')
  if op=='group' and (not isinstance(step['field'],str) or step.get('aggregate','count') not in ('count','sum','mean','minimum','maximum') or step.get('aggregate','count')!='count' and not isinstance(step.get('value_field'),str)):raise ValueError('Group needs a field, supported aggregate and numeric value_field except for count')
 return True

def catalogue():return {'operations':[{"op":key,**value} for key,value in OPERATIONS.items()],'scope':'Pure bounded data transformations; runtime data types and independent result checks still apply.','model_calls':0}
