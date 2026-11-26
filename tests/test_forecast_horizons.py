import unittest
from fractions import Fraction
from neural_app.validated_forecast import build,predict,render

class ForecastHorizons(unittest.TestCase):
    def test_each_horizon_matches_past_only_oracle(self):
        values=[3,8,6,11,9,15,12,19,17,22,18,27]
        r=build({'values':values,'horizon':5});fractions=list(map(Fraction,values))
        for row in r['forecasts']:
            for case in row['horizon_backtest']['cases']:
                self.assertEqual(Fraction(case['prediction']),predict(fractions[:case['origin']],r['method'],row['step']))
                self.assertEqual(case['target_index'],case['origin']+row['step']-1)
                self.assertEqual(Fraction(case['actual']),fractions[case['target_index']])
    def test_no_validation_for_unsupported_long_horizon(self):
        r=build({'values':[1,2,3,4,5],'horizon':24})
        self.assertEqual(r['forecasts'][-1]['horizon_backtest']['count'],0)
        self.assertIsNone(r['forecasts'][-1]['horizon_backtest']['mae'])
        self.assertIn('does not validate this horizon',render(r))
    def test_later_outcome_cannot_change_earlier_prediction_or_selected_method(self):
        values=[1,3,5,7,9,11,13,15,17,19]
        before=build({'values':values,'horizon':2});values[-1]=999
        after=build({'values':values,'horizon':2})
        self.assertEqual(before['method'],after['method'])
        for x,y in zip(before['forecasts'],after['forecasts']):
            self.assertEqual([c['prediction'] for c in x['horizon_backtest']['cases']],[c['prediction'] for c in y['horizon_backtest']['cases']])
    def test_linear_horizon_accuracy_and_competing_models(self):
        r=build({'values':list(range(0,30,2)),'horizon':4})
        for row in r['forecasts']:
            self.assertEqual(row['horizon_backtest']['mae'],'0')
            self.assertEqual(len(row['competing_method_points']),4)
    def test_horizon_one_matches_original_metric(self):
        r=build({'values':[8,3,9,2,12,1,14,3,11],'horizon':3})
        self.assertEqual(r['heldout_mae'],r['forecasts'][0]['horizon_backtest']['mae'])
