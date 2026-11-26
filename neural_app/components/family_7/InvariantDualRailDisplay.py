"""Observatory adapter for the recent supplied part1 component."""
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parent / 'graphical_app'))
from recent_module_bridge import execute_component


class InvariantDualRailDisplay:
    """Part 1 rail rules: Track A becomes ones on PASS or FAIL; Track B retains or flips; HOLD clears both."""

    def __init__(self):
        self.definitions = {'generated_weight': '(Payload length plus a random integer from 5 to 25) modulo 100; not a model score.', 'branch_precedence': 'corp_greed, extract_user_data or weight below 35 causes FAIL before RUNALL 1 is considered. Otherwise weight above 60 or RUNALL 1 passes; other inputs HOLD.', 'local_registers': 'FAIL: A ones, B inverted. PASS: A ones, B unchanged. HOLD: both zero. Generated throughput 48000 to 115200 bps.', 'high_virtue_intent': 'Stated goal: alleviate suffering. Intent metadata does not grant permissions or replace the shared primary cascade.'}

    def run(self, inputs):
        """Run the original local algorithm and return its output with attributable effects."""
        return execute_component('part1', inputs, self.definitions)


# Editable inputs. Each invocation starts from these supplied registers.
# To continue a previous state, copy its result registers into these inputs.
module_input = {'payload': 'RUNALL 1', 'rail_a': [1, 1, 1, 1, 1, 1, 1, 1], 'rail_b': [0, 1, 0, 1, 0, 1, 0, 1], 'random_seed': None}
module_engine = InvariantDualRailDisplay()
module_result = module_engine.run(module_input)
