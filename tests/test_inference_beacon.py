import unittest
from neural_app.inference_beacon import resolve


class BeaconTests(unittest.TestCase):
    def request(self, **kw):
        return resolve({'text': 'Need-aware inference', **kw})

    def test_local_route_does_not_send(self):
        r=self.request();self.assertEqual(r['route'], ['local']);self.assertFalse(r['transport']['sent'])

    def test_cheapest_eligible_route(self):
        t={'nodes':[{'id':i,'enabled':True,'capabilities':['inference']} for i in ['local','bridge','remote']], 'bridges':[{'from':'local','to':'remote','allowed':True,'cost':8},{'from':'local','to':'bridge','allowed':True,'cost':1},{'from':'bridge','to':'remote','allowed':True,'cost':2}]}
        r=self.request(topology=t,target='remote');self.assertEqual(r['route'], ['local','bridge','remote']);self.assertEqual(r['route_cost'],3)
        self.assertEqual(self.request(topology=t,target='remote',hop_limit=1)['route_cost'],8)

    def test_disabled_or_unpermitted_has_no_route(self):
        t={'nodes':[{'id':i,'enabled':True,'capabilities':['inference']} for i in ['local','remote']], 'bridges':[{'from':'local','to':'remote','allowed':False}]}
        self.assertIsNone(self.request(topology=t,target='remote')['route'])
        t['bridges'][0]['allowed']=True;t['nodes'][1]['enabled']=False
        self.assertIsNone(self.request(topology=t,target='remote')['route'])

    def test_no_silent_truncation(self):
        with self.assertRaises(ValueError):self.request(text='x'*4097)

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):self.request(topology={'nodes':[{'id':'local'},{'id':'local'}]})

    def test_capability_boundary(self):
        self.assertIsNone(self.request(capability='unavailable')['route'])
