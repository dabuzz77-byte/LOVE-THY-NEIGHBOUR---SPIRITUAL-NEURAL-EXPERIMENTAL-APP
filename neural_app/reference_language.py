"""Conservative reference interpretations with explicit ambiguity and rule limits."""
import re

def solve(text,parse_options,make_result):
 parsed=parse_options(text)
 if not parsed:return None
 body,choices=parsed;sentence=re.search(r'\bSentence:\s*(.+)',body)
 if not sentence:return None
 sentence=sentence[1].strip().rstrip('.');ambiguous=[letter for letter,claim in choices if claim.casefold()=='ambiguous']
 if len(ambiguous)!=1:return None
 match=re.fullmatch(r'The (.+?) (?:called|contacted|approached|showed|handed|gave) the (.+?)(?: an? .+?)? and (?:asked|told|instructed) (?:him|her|them) (?:to|for) .+',sentence,re.I)
 if match:
  actor,recipient=match[1],match[2];selected=[letter for letter,claim in choices if re.fullmatch(r'(?:Asked|Told|Instructed) (?:the )?'+re.escape(recipient),claim,re.I)]
  if len(selected)==1:return make_result('reference-interpretation','('+selected[0]+')',{'actor':actor,'recipient':recipient,'rule':'Coordinated subject with non-reflexive request object; the named recipient is the supported local antecedent.'},'Rule-based interpretation of a closed sentence pattern, without inferring gender from names or occupations; other discourse patterns remain unresolved.')
 match=re.fullmatch(r'The (.+?) (?:disliked|liked|admired|avoided) the (.+?) because (?:he|she|they) (?:is|was|were|are) .+',sentence,re.I)
 if not match:match=re.fullmatch(r'(.+?) (?:plans to meet|met|will meet|visited) (.+?) at (?:his|her|their) .+',sentence,re.I)
 if match:return make_result('reference-ambiguity','('+ambiguous[0]+')',{'candidate_antecedents':[match[1],match[2]],'missing_information':'No explicit referent distinguishes the two local readings in this supported pattern.'},'Both local readings remain available under the stated finite reference rules; actual author intent is not inferred.')
 if re.search(r'\b(he|she|they|him|her|them|his|their)\b',sentence,re.I):return {'status':'needs-clarification','answer':'The native parser cannot settle the pronoun reference. Choose a stated interpretation with “interpretation A” (or another label), or clarify the wording.\n'+'\n'.join('('+letter+') '+claim for letter,claim in choices),'reasoning_family':'reference-interpretation','source_sentence':sentence,'candidate_interpretations':[claim for _,claim in choices],'candidate_options':[{'label':letter,'text':claim} for letter,claim in choices],'model_calls':0}
 return None

def clarify(text,record):
 match=re.fullmatch(r'(?:actually[, ]+|please )?(?:use )?interpretation\s+\(?([A-Z])\)?[.!]?',text.strip(),re.I)
 if not match or not record or record.get('reasoning_family')!='reference-interpretation' or not record.get('candidate_options'):return None
 label=match[1].upper();selected=next((r for r in record['candidate_options'] if r['label']==label),None)
 if selected is None:return {**record,'status':'needs-clarification','answer':'Choose one of the labels from the retained reference question.','model_calls':0}
 before=record.get('user_selected_interpretation');history=(record.get('clarification_history',[])+[{'before':before,'after':selected,'source':'explicit-user-clarification'}])[-8:]
 return {**record,'status':'user-clarified','answer':'Using your clarification: '+selected['text']+'.\n\nOriginal sentence: '+record['source_sentence']+'\nThis is your selected reading, not an independently established fact.','user_selected_interpretation':selected,'answer_source':'explicit-user-clarification','clarification_history':history,'model_calls':0}
