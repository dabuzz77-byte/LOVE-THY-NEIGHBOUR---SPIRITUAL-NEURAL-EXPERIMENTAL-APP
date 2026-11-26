import unittest
from neural_app.outreach_plan import plan_outreach


class OutreachTests(unittest.TestCase):
    def node(self,ident,**extra):return {'id':ident,'need':1.,'urgency':1.,'existing_access':0.,'consent':True,'reachable':True,**extra}

    def test_greater_unmet_need_gets_finite_capacity_first(self):
        nodes=[self.node('well-served',existing_access=1.),self.node('least-access')]
        size=plan_outreach({'nodes':nodes})['packet_bytes']
        r=plan_outreach({'nodes':nodes,'byte_budget':size})
        self.assertEqual(r['priority_order'][0],'least-access')
        self.assertEqual(r['planned_bytes'],size);self.assertEqual(r['sent'],0)
        self.assertEqual(next(n for n in r['nodes'] if n['id']=='well-served')['status'],'DEFERRED_CAPACITY')

    def test_consent_and_connection_are_not_inferred(self):
        r=plan_outreach({'nodes':[self.node('no-consent',consent=False),self.node('offline',reachable=False,offline_handoff=True),self.node('no-route',reachable=False)]})
        states={n['id']:n['status'] for n in r['nodes']}
        self.assertEqual(states['no-consent'],'AWAITING_CONSENT');self.assertEqual(states['no-route'],'AWAITING_CONNECTION');self.assertEqual(states['offline'],'READY_TO_SHARE')

    def test_duplicate_or_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):plan_outreach({'nodes':[self.node('x'),self.node('x')]})
        with self.assertRaises(ValueError):plan_outreach({'nodes':[self.node('x',need=float('nan'))]})
