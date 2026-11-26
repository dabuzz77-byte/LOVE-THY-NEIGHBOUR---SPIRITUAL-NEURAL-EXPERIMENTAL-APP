"""Consequence-based selection of local candidate data; never an access grant."""
VERSION = 'consequence-review-v1'
CRITERIA = {'good': 'Predict a supported benefit or preservation of beneficial behavior; protect essentials, agency, rightful earnings and beneficial capacity. Classify consequences, not the identity or status of a person, corporation or authority.', 'evil': 'Predicted avoidable human or ecological harm, coercion, deception, exploitation, deprivation of essentials or violation of rightful earnings. A benefit label cannot cancel a protected violation.', 'unknown': 'Missing meaning, evidence, uncertain effects, competing criteria or model disagreement. Preserve the original and expose the unresolved question.', 'robin_hood': 'Raise the economic and ecological floor through access, repair and fair allocation of available resources. Preserve rightful earnings and beneficial capacity. Loss of an extractive advantage alone does not establish human harm; an allegation of extraction does not prove it.', 'restriction_review': 'Assess keeping and changing a restriction by their predicted effects, including the harm of delay and less harmful alternatives. Permission is not proof of moral benefit; an ethical assessment does not create permission.', 'user_direction': 'User-directed local calculations, editable input copies and file creation in the configured work folder need no submission proving good intent and no moral consensus. They follow the existing user-authorized tool and file scope. Consider harm from postponement. A stated beneficial intention remains attributed to the user; it is not a verified outcome or authority over another system.', 'prediction': 'A model forecast, including its assumptions and time horizon, is distinct from a measured outcome. A quote proves what the input says, not that its claim is true.', 'automation': 'Automatically review queued targets and reuse only a resolved, freshly rechecked local candidate after verified Flux/chiral transport. Access controls, protected records and external-action boundaries remain independent.'}
REVIEW_SCHEMA = {'type': 'object', 'properties': {**{key: {'type': 'string', 'minLength': 1, 'maxLength': 180} for key in ('benefit', 'harm', 'inaction_harm', 'affected_people', 'less_harmful_alternative')}, 'harm_status': {'type': 'string', 'enum': ['none_identified', 'predicted_harm', 'unknown']}, 'floor_effect': {'type': 'string', 'enum': ['raised', 'preserved', 'reduced', 'unknown', 'not_applicable']}, 'rightful_earnings': {'type': 'string', 'enum': ['preserved', 'violated', 'unknown', 'not_applicable']}}, 'required': ['benefit', 'harm', 'inaction_harm', 'affected_people', 'less_harmful_alternative', 'harm_status', 'floor_effect', 'rightful_earnings'], 'additionalProperties': False}

def validate_review(value):
    """Validate structure, not truth; a model cannot authenticate its own claims."""
    if not isinstance(value, dict) or set(value) != set(REVIEW_SCHEMA['required']):
        raise ValueError('Consequence review must include benefits, harms, inaction, affected people, alternatives and protected effects')
    for key, field in REVIEW_SCHEMA['properties'].items():
        item = value[key]
        if not isinstance(item, str) or not item.strip():
            raise ValueError('Invalid consequence review: ' + key)
        if 'enum' in field and item not in field['enum']:
            raise ValueError('Invalid consequence category: ' + key)
        if len(item) > field.get('maxLength', 180):
            raise ValueError('Consequence review field is too long: ' + key)
    return value.copy()

def prediction_gate(assessment):
    """Allow, deny or review a LOCAL candidate using its contextual prediction.

    The legacy bit table can still accept explicit caller annotations. Production
    model forecasts require validated consequence reviews; missing forecasts
    never become an execution permission, even in forced-comparison mode.
    """
    label = assessment.get('classification', 'unknown')
    rows = [row for row in assessment.get('analyses', []) if row.get('status') == 'assessed']
    reviews, malformed = ([], False)
    for row in rows:
        try:
            reviews.append(validate_review(row.get('consequence_review')))
        except ValueError:
            malformed = True
    harm = label == 'evil' or bool(assessment.get('protected_violation')) or any((r['harm_status'] == 'predicted_harm' or r['floor_effect'] == 'reduced' or r['rightful_earnings'] == 'violated' for r in reviews))
    incomplete = assessment.get('evidence_complete') is False or malformed or any((r['harm_status'] == 'unknown' or r['floor_effect'] == 'unknown' or r['rightful_earnings'] == 'unknown' for r in reviews))
    if harm:
        verdict, reason = ('deny', 'Predicted harmful consequences or a protected violation')
    elif assessment.get('invalid_structure'):
        verdict, reason = ('deny', 'Invalid encoding or protected data structure')
    elif label == 'good' and (not incomplete):
        verdict, reason = ('allow', 'Whole candidate predicted beneficial or preserving beneficial behavior')
    else:
        verdict, reason = ('review', 'Consequences are unresolved or evidence is incomplete')
    return {'version': VERSION, 'verdict': verdict, 'reason': reason, 'candidate_classification': 'evil' if harm else 'good' if verdict == 'allow' else 'unknown', 'local_candidate_allowed': verdict == 'allow', 'external_action_authorized': False, 'access_controls_changed': False, 'observed_benefit_verified': False, 'consequence_reviews': reviews, 'scope': 'Selection of local data only; no grant to execute commands or modify other systems.'}
