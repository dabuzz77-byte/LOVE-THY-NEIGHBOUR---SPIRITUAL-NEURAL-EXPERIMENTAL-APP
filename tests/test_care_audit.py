import unittest
from neural_app.care_plan import plan
from neural_app.care_audit import audit_care


class CareAuditTests(unittest.TestCase):
    def test_extra_budget_reduces_unmet_need_without_mutating_input(self):
        body = {'budget': .2, 'nodes': [{'label': 'Need', 'need': 1., 'urgency': 1., 'protection': .7}]}
        baseline = plan(body)
        audit = audit_care(body, baseline)
        change = audit['budget_counterfactual']
        self.assertAlmostEqual(change['additional_allocation'], .25)
        self.assertAlmostEqual(change['unmet_need_after'], .55)
        self.assertEqual(change['node_changes'][0]['protection_after'], .7)
        self.assertEqual(body['budget'], .2)
        self.assertAlmostEqual(baseline['allocated'], .2)

    def test_satisfied_need_has_no_invented_benefit(self):
        body = {'budget': 1., 'nodes': [{'need': .1, 'urgency': 0., 'protection': 0.}]}
        change = audit_care(body, plan(body))['budget_counterfactual']
        self.assertEqual(change['additional_allocation'], 0.)
        self.assertEqual(change['unmet_need_after'], 0.)

    def test_budget_ceiling_has_no_extra_budget(self):
        body = {'budget': 16.}
        change = audit_care(body, plan(body))['budget_counterfactual']
        self.assertEqual(change['additional_budget'], 0.)
        self.assertEqual(change['additional_allocation'], 0.)
