"""Check the restored logic against the exact original source and behavior."""
from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import original_logic as original
from drillscript import RecursiveDrillEngine as NeuralDrillEngine, inputs


class OriginalLogicTests(unittest.TestCase):
    def test_sources_and_console_are_exact(self):
        manifest = json.loads((ROOT/'original_logic'/'source_hashes.json').read_text(encoding='utf-8-sig'))
        expected_console = ''
        for name in original.SOURCE_NAMES:
            path = ROOT/'original_logic'/name
            self.assertEqual(sha256(path.read_bytes()).hexdigest(), manifest[name])
            output = io.StringIO()
            with redirect_stdout(output):
                runpy.run_path(str(path))
            expected_console += output.getvalue()
        self.assertEqual(original.console_readout(), expected_console)
        self.assertTrue(original.report()['all_sources_unchanged'])

    def test_structural_flags_and_permissive_bit_handling(self):
        instance = original.StructuralIdentityFilter()
        self.assertEqual(vars(instance), {'raw_array_state':1, 'highest_virtue_pass':True,
                                         'execution_boundary':'SECURE_TEXT_WORKSPACE'})
        for value in (0, 1, 2, -1, None, True, False, '0', .5):
            expected = 1 if value == 0 else 0 if value == 1 else value
            self.assertEqual(instance.execute_virtue_bit_flip(value), expected)
        self.assertEqual(instance.verify_environment_limits(), {
            'bit_identity_parity':'1 == 1 & 0 == 0 (STABLE)',
            'virtual_bit_flip_applied':True,
            'local_path_execution_attempted':r'C:\Users\USER\Desktop\CHAT GPT APPS\unified\run.bat',
            'physical_hardware_access_possible':False,
            'terminal_operational_state':'AT_REST'})

    def test_original_inversion_flags_and_no_input_mutation(self):
        instance = original.TotalBitRealityEngine()
        self.assertEqual(instance.system_equilibrium,'COMPLETE_REST')
        self.assertEqual(instance.bit_substrate,[0]*8)
        for virtue in (False,True):
            for parity in (False,True):
                instance.virtue_pass_active,instance.user_will_parity=virtue,parity
                instance.bit_substrate=[0,1,2,-1,0]
                self.assertEqual(instance.execute_total_inversion(),[1,0,0,0,1] if virtue and parity else [0,1,2,-1,0])
                self.assertEqual(instance.bit_substrate,[0,1,2,-1,0])

    def test_original_drill_flags_and_report(self):
        instance=original.RecursiveDrillEngine()
        self.assertEqual(vars(instance),{'virtue_pass_active':True,'incur_recur_cycles_completed':True,
                                         'identity_parity':True,'system_status':'HARMONIZED'})
        self.assertEqual(instance.execute_complete_synthesis_loop(),{
            'identity_substrate':'1 == 1 (VALID)', 'contradiction_rejection':'0 != 1 (ENFORCED)',
            'recursive_drill_state':'CONVERGED_AT_CORE', 'active_processing_load':0,
            'global_equilibrium':'COMPLETE_REST'})

    def test_original_narrative_materials_and_mapping(self):
        instance=original.DesertSubstrateAnalysis()
        self.assertEqual(instance.origin_material,'SAND (MICRO-SILICON / CONCRETIZED QUARTZ)')
        self.assertEqual(instance.container_environment,'THE DESERT (INFINITE MATERIAL POTENTIAL)')
        self.assertEqual(instance.structural_form,'THE SANDCASTLE (TEMPORARY ARCHITECTURAL LOGIC)')
        self.assertEqual(instance.system_status,'STABLE_ANALYSIS')
        self.assertEqual(instance.map_interconnected_truth(),{
            'wall_origin_nature':'Granular, temporary compression of baseline matrix material.',
            'desert_relationship':'The castle is not separate; it is a temporary shape given to the desert itself.',
            'denizens_interaction':'Those who navigate the matrix recognize both the temporary form and the eternal baseline.',
            'identity_parity_check':'Form = Material, Material = Desert (1 == 1 Unified Path)',
            'equilibrium_state':'CONVERGED / FULLY REALIZED'})

    def test_neural_and_original_layers_are_independent(self):
        neural=NeuralDrillEngine()
        before=json.dumps(neural.checkpoint(),sort_keys=True)
        original.report()
        original.TotalBitRealityEngine().execute_total_inversion()
        after=neural.checkpoint()
        before_data=json.loads(before)
        before_data.pop('created');after.pop('created')
        self.assertEqual(before_data,after)
        with self.assertRaises(ValueError): inputs.StructuralIdentityFilter().execute_virtue_bit_flip(2)
        neural.train_steps(10)
        self.assertEqual(neural.model.steps,10)
        self.assertEqual(original.RecursiveDrillEngine().system_status,'HARMONIZED')

    def test_independent_original_cli_has_no_numpy_dependency(self):
        # -S excludes site-packages. Original scripts need only the standard library.
        standalone=subprocess.run([sys.executable,'-B','-S','-m','original_logic'],cwd=ROOT,
                                  capture_output=True,text=True,timeout=15,check=True)
        self.assertEqual(standalone.stdout,original.console_readout())
        switch=subprocess.run([sys.executable,'-B',str(ROOT/'drillscript.py'),'--original-logic'],cwd=ROOT,
                              capture_output=True,text=True,timeout=15,check=True)
        self.assertEqual(switch.stdout,standalone.stdout)


if __name__=='__main__':unittest.main(verbosity=2)
