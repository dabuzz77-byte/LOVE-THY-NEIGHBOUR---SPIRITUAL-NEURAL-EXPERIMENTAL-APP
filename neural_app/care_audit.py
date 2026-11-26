"""Measured care-plan explanation and same-input budget counterfactual."""
from .care_plan import plan


def audit_care(body, result):
    budget = result['budget']
    extra = min(.25, max(0., 16. - budget))
    alternative = plan({**body, 'budget': budget + extra})
    return {
        'method': 'Same needs, urgency and protection; change only available budget.',
        'stages': [
            {'stage': 'Explicit need', 'total_need': result['total_need'], 'nodes': len(result['nodes'])},
            {'stage': 'Constraints', 'budget': budget, 'protection_preserved': all(n['protection_after'] == n['protection'] for n in result['nodes'])},
            {'stage': 'Allocation', 'allocated': result['allocated'], 'coverage': result['coverage']},
            {'stage': 'Remaining need', 'unmet_need': result['unmet_need'], 'unallocated_budget': result['unallocated_budget']},
        ],
        'budget_counterfactual': {
            'additional_budget': extra,
            'alternative_budget': alternative['budget'],
            'additional_allocation': max(0., alternative['allocated'] - result['allocated']),
            'unmet_need_after': alternative['unmet_need'],
            'coverage_after': alternative['coverage'],
            'node_changes': [
                {'id': n['id'], 'label': n['label'], 'allocation_before': n['allocated'],
                 'allocation_after': a['allocated'], 'protection_after': a['protection_after']}
                for n, a in zip(result['nodes'], alternative['nodes'])
            ],
        },
        'scope': 'Illustrative allocation comparison only. The alternative is not executed as a separate job, training example or aid delivery.',
    }
