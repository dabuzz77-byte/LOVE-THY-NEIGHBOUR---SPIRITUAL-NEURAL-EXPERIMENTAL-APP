import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from neural_app.native_work import NativeWork
from neural_app.table_work import respond

class ExactExport(unittest.TestCase):
    def test_native_chat_work_entrypoint_reaches_natural_table_question(self):
        w=NativeWork();w.handle('study table: [{"Team":"A","Value":0.1},{"Team":"A","Value":0.2}]')
        self.assertEqual(w.handle('What is the average of Value where Team equals "A"?')['table_result']['exact_result'],'3/20')
    def test_natural_filtered_question_and_followup_export(self):
        w=NativeWork();respond('study table: [{"Team":"A","Value":0.1},{"Team":"A","Value":0.2},{"Team":"B","Value":99},{"Team":"A","Value":null}]',w)
        r=respond('What is the average of Value where Team equals "A", excluding missing values?',w)
        self.assertEqual(r['table_result']['exact_result'],'3/20');self.assertEqual(r['table_result']['source_rows'],[1,2])
        self.assertEqual(respond('how many rows where Team equals "A"?',w)['table_result']['exact_result'],'3')
    def test_unknown_qualification_not_removed(self):
        from neural_app.table_work import conversational_query
        self.assertIsNone(conversational_query('what is the average of Value where Team equals "A" probably'))
    def test_all_aggregates_export_filter_and_exact_values(self):
        rows=[{'team':'A','value':.1},{'team':'A','value':.2},{'team':'B','value':99},{'team':'A','value':None}]
        for op in ('count','sum','mean','minimum','maximum'):
            w=NativeWork();respond('study table: '+json.dumps(rows),w)
            query={'select':op,'where':{'field':'team','equals':'A'},'missing':'exclude'}
            if op!='count':query['field']='value'
            original=respond('table query: '+json.dumps(query),w)['table_result']
            code=respond('write exact Python for table query',w)
            with tempfile.TemporaryDirectory() as folder:
                p=Path(folder)/'query.py'
                p.write_text(code['code']['source']+'\nimport json\nprint(json.dumps(query_table('+repr(rows)+','+repr(query)+')))\n',encoding='utf-8')
                result=subprocess.run([sys.executable,'-I',str(p)],capture_output=True,text=True,check=True,timeout=5)
            actual=json.loads(result.stdout)
            self.assertEqual(actual,{k:original[k] for k in ('exact_result','source_rows','excluded_rows')})
            self.assertEqual(code['code_input'],rows)
    def test_fresh_rows_use_same_filter_and_exact_mean(self):
        from neural_app.exact_table_export import query_table
        query={'select':'mean','field':'v','where':{'field':'group','equals':'A'}}
        self.assertEqual(query_table([{'group':'A','v':.3},{'group':'B','v':100},{'group':'A','v':.6}],query)['exact_result'],'9/20')
    def test_type_strict_filters_and_missing_errors(self):
        from neural_app.exact_table_export import query_table
        self.assertEqual(query_table([{'g':True},{'g':1}],{'select':'count','where':{'field':'g','equals':1}})['source_rows'],[2])
        with self.assertRaises(ValueError):query_table([{'v':None}],{'select':'sum','field':'v'})
    def test_tampered_result_is_not_exported(self):
        w=NativeWork();respond('study table: [{"v":2}]',w);respond('table query: {"select":"sum","field":"v"}',w)
        w.state['table_result']['exact_result']='100'
        with self.assertRaises(ValueError):respond('write exact Python for table query',w)
