import copy,json,random,unittest
from neural_app.native_work import NativeWork,parse_steps
from neural_app.native_task_batch import code_request
from neural_app.semantic_steps import parse

class SemanticSteps(unittest.TestCase):
    def test_central_engine_uses_same_semantic_parser(self):
        from neural_app.reasoning_engine import ReasoningEngine
        e=ReasoningEngine({},lambda:None)
        self.assertEqual(e.handle('remove repeated values: [2,1,2]')['value'],[2,1])
        self.assertEqual(e.handle('same task with: [4,3,4]')['value'],[4,3])
    def test_case_sensitive_field_and_value_slots_are_preserved(self):
        step=parse('keep rows where City equals "Paris"')
        self.assertEqual(step,{'op':'filter','field':'City','relation':'equal','value':'Paris'})
    def test_unknown_qualifiers_and_invalid_values_are_not_dropped(self):
        for text in ('keep only numbers above 4 approximately','keep only numbers above true','keep rows where price is at most 20 safely','keep rows where price is at most "twenty"'):
            self.assertIsNone(parse(text))
    def test_table_filter_extract_aggregate_composition(self):
        w=NativeWork();r=w.handle('keep rows where Price is at most 20 then pick the Price column then add up all values: [{"Price":10},{"Price":30},{"Price":5}]')
        self.assertEqual(r['value'],15)
    def test_quoted_instruction_like_value_remains_data(self):
        steps=parse_steps('keep rows where City equals "Paris and then sort"')
        self.assertEqual(len(steps),1);self.assertEqual(steps[0]['value'],'Paris and then sort')
    def test_work_and_python_transfer_over_new_values_and_fields(self):
        rng=random.Random(61729)
        for index in range(32):
            field=rng.choice(['Amount','cost','score']);threshold=rng.randint(-10,30)
            values=[rng.randint(-20,50) for _ in range(8)];rows=[{field:v} for v in values]
            request=f'keep rows where {field} is at most {threshold} then pick the {field} column then add up all values: '+json.dumps(rows)
            expected=sum(v for v in values if v<=threshold)
            if not any(v<=threshold for v in values):continue
            with self.subTest(index=index):
                self.assertEqual(NativeWork().handle(request)['value'],expected)
                self.assertEqual(code_request(request,NativeWork())['value'],expected)
    def test_unsupported_clause_does_not_partially_commit(self):
        w=NativeWork();w.handle('sum: [3,4]');before=copy.deepcopy(w.state['last'])
        result=w.handle('remove repeated values then make everyone happy: [1,1]')
        self.assertTrue(result is None or result.get('status')!='complete');self.assertEqual(w.state['last'],before)
    def test_group_measurement_and_key_are_separate_slots(self):
        w=NativeWork();r=w.handle('average score for each City: [{"score":10,"City":"A"},{"score":30,"City":"A"}]')
        self.assertEqual(r['value'],[{'key':'A','value':20,'count':2}])
