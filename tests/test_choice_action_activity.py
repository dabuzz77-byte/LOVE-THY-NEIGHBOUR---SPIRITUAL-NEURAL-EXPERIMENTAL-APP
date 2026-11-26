import copy,threading,types,unittest
from neural_app.choice_action_study import ChoiceActionStudy

class Bus:
    def __init__(self):self.events=[]
    def publish(self,event):self.events.append(copy.deepcopy(event))

def circuit(count=1,facts=1):
    sources={str(i):{'source':str(i),'digest':'d0','parent_event':1,'facts':[{'path':['v',j],'value':i+j} for j in range(facts)]} for i in range(count)}
    return types.SimpleNamespace(lock=threading.RLock(),sources=sources,goal='study',bus=Bus())

class StudyActivity(unittest.TestCase):
    def tick(self,s,c):s.next_at=0;s.tick(c)
    def test_bounded_batch_and_fair_source_coverage(self):
        c=circuit(100);s=ChoiceActionStudy();covered=set()
        for _ in range(5):
            self.tick(s,c);rows=s.view('action-study')['thought_trace'];self.assertLessEqual(len(rows),32)
            covered.update(r['source'] for r in rows)
        self.assertEqual(len(covered),100);self.assertEqual(s.processed,100)
    def test_unchanged_data_is_not_counted_as_new_work(self):
        c=circuit();s=ChoiceActionStudy();self.tick(s,c);sequence=s.sequence;events=len(c.bus.events)
        self.tick(s,c);self.assertEqual(s.sequence,sequence);self.assertEqual(len(c.bus.events),events)
    def test_all_fact_paths_are_eventually_studied(self):
        c=circuit(2,5);s=ChoiceActionStudy()
        for _ in range(7):self.tick(s,c)
        self.assertEqual(s.processed,10)
    def test_actual_local_profiles_and_prediction_checks(self):
        c=circuit();s=ChoiceActionStudy()
        for index,value in enumerate((2,4,7)):
            c.sources['0'].update(digest=str(index),parent_event=index,facts=[{'path':['v'],'value':value}]);self.tick(s,c)
        row=s.view('action-study')['thought_trace'][0]['executed_local_derivative']
        self.assertEqual(row['prediction_check']['predicted'],6);self.assertEqual(row['prediction_check']['absolute_error'],1)
        self.assertTrue(c.bus.events[-1]['payload']['processing_receipt'])
        self.assertEqual(s.view('consequence-study')['thought_trace'][0]['local_observation'],row)
    def test_mission_and_continuous_activity_coexist(self):
        c=circuit();mission={'name':'task','created':1,'sequence':0,'status':'running','phase':'compare','trace':[],'choices':[],'committed':False}
        c.whole_mind_study=types.SimpleNamespace(native_dialogue=types.SimpleNamespace(lock=threading.RLock(),work=types.SimpleNamespace(state={'sphere_mission':mission})))
        s=ChoiceActionStudy();self.tick(s,c);frame=s.view('choice-study')
        self.assertTrue(frame['role_task']);self.assertTrue(any(p['source']=='0' for p in frame['particles']))
        self.assertTrue(any(p['source']=='sphere-mission' for p in frame['particles']))
    def test_no_mutation_of_source_payload_and_no_self_echo(self):
        c=circuit();c.sources['echo']={'source':'choice-action-study','digest':'x','facts':[{'path':['x'],'value':3}]};before=copy.deepcopy(c.sources)
        s=ChoiceActionStudy();self.tick(s,c);self.assertEqual(c.sources,before);self.assertEqual(s.processed,1)
    def test_no_sources_is_a_valid_idle_state(self):
        s=ChoiceActionStudy();self.tick(s,circuit(0));self.assertEqual(s.processed,0)
