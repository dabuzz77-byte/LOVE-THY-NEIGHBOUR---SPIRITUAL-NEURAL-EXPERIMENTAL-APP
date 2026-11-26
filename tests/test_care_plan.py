import tempfile,time,unittest,json,ssl,threading
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from neural_app.care_plan import plan
from neural_app.runtime import Runtime

class CarePlanTests(unittest.TestCase):
 def test_budget_conservation_and_protection(self):
  for budget in [0,.05,1,1.5,4,16]:
   result=plan({'budget':budget});self.assertLessEqual(result['allocated'],budget+1e-10)
   self.assertAlmostEqual(result['allocated']+result['unallocated_budget'],budget)
   for row in result['nodes']:
    self.assertLessEqual(row['allocated'],row['need']+1e-10);self.assertEqual(row['protection'],row['protection_after']);self.assertTrue(0<=row['priority']<=1)
 def test_all_needs_met_when_budget_sufficient(self):
  value=plan({'budget':16});self.assertAlmostEqual(value['unmet_need'],0);self.assertAlmostEqual(value['coverage'],1)
 def test_finite_at_zero_protection_and_zero_need(self):
  value=plan({'nodes':[{'label':'zero protection','need':1,'urgency':1,'protection':0}], 'budget':.5});self.assertEqual(value['nodes'][0]['priority'],1);self.assertEqual(value['allocated'],.5)
  value=plan({'nodes':[{'label':'no unmet need','need':0,'urgency':1,'protection':0}]});self.assertEqual(value['coverage'],0);self.assertEqual(value['allocated'],0)
 def test_labels_do_not_change_allocation(self):
  a={'label':'A','need':.8,'urgency':.9,'protection':.1};b={**a,'label':'A different belief or species'}
  self.assertEqual(plan({'nodes':[a]})['nodes'][0]['allocated'],plan({'nodes':[b]})['nodes'][0]['allocated'])
 def test_invalid_numbers_rejected(self):
  for value in [-1,float('inf'),float('nan'),True]:
   with self.assertRaises(ValueError):plan({'budget':value})
  with self.assertRaises(ValueError):plan({'nodes':[{'label':'bad','need':1.1}]})
 def test_care_plan_changes_working_bits_and_resumes_model(self):
  with tempfile.TemporaryDirectory() as folder:
   r=Runtime(folder,start=False)
   try:
    low=r.engine('care',{'budget':0});high=r.engine('care',{'budget':4});self.assertNotEqual(low['causal']['working_bits'],high['causal']['working_bits'])
    self.assertEqual(low['causal']['input_bits'],high['causal']['input_bits']);self.assertEqual(high['classifier']['input_basis'],'care plan working bits')
    ident=r.record('care',{'budget':4},high,1);r.feedback({'receipt':ident,'target':1});self.assertEqual(r.causal.reviews,1);r.checkpoint();expected=r.get_model().state()
   finally:r.close()
   n=Runtime(folder,start=False)
   try:self.assertEqual(n.get_model().state(),expected);self.assertEqual(n.causal.reviews,1)
   finally:n.close()

class DeviceCompanionTests(unittest.TestCase):
 def test_invitation_is_hashed_and_revocable(self):
  with tempfile.TemporaryDirectory() as folder:
   r=Runtime(folder,start=False)
   try:
    h=r.device_hub;invite=h.invite('Private nickname');self.assertFalse(h.info()['running']);self.assertNotIn(invite['key'],h.path.read_text());ident,item=h.authenticate(invite['key']);self.assertFalse(item['send']);h.revoke(ident)
    with self.assertRaises(PermissionError):h.authenticate(invite['key'])
   finally:r.close()
 def test_tls_permissions_private_signal_and_own_job(self):
  with tempfile.TemporaryDirectory() as folder:
   r=Runtime(folder);h=r.device_hub
   try:
    h.start(0,lan=False);base='https://127.0.0.1:'+str(h.port);context=ssl.create_default_context(cafile=str(h.folder/'gateway-cert.pem'));context.check_hostname=False
    def request(path,key,body=None):
     data=json.dumps(body).encode() if body is not None else None
     req=Request(base+path,data=data,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Origin':base})
     return json.loads(urlopen(req,context=context,timeout=10).read())
    recv=h.invite('Receive');send=h.invite('Send',True)
    signal=request('/signal',recv['key']);self.assertFalse(signal['can_send']);self.assertNotIn('source_sha256',signal['signal'])
    with self.assertRaises(HTTPError) as caught:request('/bits',recv['key'],{'bits':'01'*32})
    self.assertEqual(caught.exception.code,403)
    job=request('/bits',send['key'],{'bits':'01'*32});deadline=time.monotonic()+10
    while time.monotonic()<deadline:
     result=request('/result?id='+job['id'],send['key'])
     if result['status']=='complete':break
     time.sleep(.2)
    self.assertEqual(result['status'],'complete');self.assertGreater(result['changed_bits'],0)
    with self.assertRaises(HTTPError) as caught:request('/result?id='+job['id'],recv['key'])
    self.assertEqual(caught.exception.code,403)
    self.assertTrue(request('/leave',send['key'],{})['invitation_revoked'])
    with self.assertRaises(HTTPError):request('/signal',send['key'])
   finally:r.close()
