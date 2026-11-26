"""Active identification inside a finite isolated byte-function environment."""
from collections import Counter
from functools import lru_cache
import hashlib,math
from .ambient_skill_composition import apply_program

@lru_cache(maxsize=512)
def table(program):return bytes(apply_program(program,x) for x in range(256))

def choose_probe(hypotheses,excluded):
 best=None
 for x in range(256):
  if x in excluded:continue
  counts=Counter(values[x] for program,values in hypotheses);n=len(hypotheses)
  entropy=-sum((count/n)*math.log2(count/n) for count in counts.values())
  score=(entropy,-max(counts.values()),-x)
  if best is None or score>best[0]:best=(score,x,len(counts))
 return None if best is None or best[0][0]<=0 else {'input':best[1],'expected_information_bits':best[0][0],'predicted_outcomes':best[2]}

def identify(programs,oracle,initial_points,validation_points,max_queries=4):
 if not initial_points or len(validation_points)<4 or len(set(initial_points))!=len(initial_points) or len(set(validation_points))!=len(validation_points) or set(initial_points)&set(validation_points):return {'status':'invalid-split'}
 if any(type(x)is not int or not 0<=x<256 for x in initial_points+validation_points):return {'status':'invalid-input'}
 examples=[(x,oracle(x)) for x in initial_points];hypotheses=[];seen=set();tested=0
 for candidate in programs:
  if tested>=2048:break
  tested+=1;program=tuple(tuple(rule) for rule in candidate)
  if not all(apply_program(program,x)==y for x,y in examples):continue
  values=table(program)
  if values in seen:continue
  seen.add(values);hypotheses.append((program,values))
 queries=[];excluded=set(initial_points)|set(validation_points)
 for _ in range(max(0,min(8,max_queries))):
  if len(hypotheses)<=1:break
  probe=choose_probe(hypotheses,excluded)
  if probe is None:break
  x=probe['input'];observed=oracle(x);before=len(hypotheses);excluded.add(x);examples.append((x,observed))
  hypotheses=[h for h in hypotheses if h[1][x]==observed]
  queries.append({**probe,'observed_output':observed,'hypotheses_before':before,'hypotheses_after':len(hypotheses)})
 report={'tested_candidates':tested,'queries':queries,'examples':examples,'remaining_behaviours':len(hypotheses),'validation_used_for_selection':False,'scope':'Uniform-over-distinct-behaviours information-gain queries in an isolated registered byte environment. No network or host actions.'}
 if not hypotheses:return {**report,'status':'no-supported-rule'}
 if len(hypotheses)!=1:return {**report,'status':'ambiguous-query-budget'}
 program,values=hypotheses[0];validation=[(x,oracle(x)) for x in validation_points]
 if not all(values[x]==y for x,y in validation):return {**report,'status':'counterexample-found','validation_examples':len(validation)}
 return {**report,'status':'validated-candidate','program':[list(rule) for rule in program],'validation_examples':len(validation),'behaviour_sha256':hashlib.sha256(values).hexdigest(),'active_experiment':True}
