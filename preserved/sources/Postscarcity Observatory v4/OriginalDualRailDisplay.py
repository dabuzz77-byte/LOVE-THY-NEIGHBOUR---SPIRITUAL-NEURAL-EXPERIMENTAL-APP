"""Observatory adapter for the recent supplied original component."""
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parent / 'graphical_app'))
from recent_module_bridge import execute_component


class OriginalDualRailDisplay:
    """Original dual-rail display rules: generated weight selects remain, invert or zero-fill on local bits."""

    def __init__(self):
        self.definitions = {'generated_weight': '(Payload length plus a random integer from 5 to 25) modulo 100; a display value, not an ethical assessment.', 'remain_flip': 'FAIL inverts both rails; PASS retains both; HOLD zero-fills both. corp_greed or weight below 35 takes precedence.', 'display_throughput': 'Generated 9600 to 115200 bps; not network telemetry.', 'high_virtue_intent': 'Stated goal: alleviate suffering. Intent metadata does not grant permissions or replace the shared primary cascade.'}

    def run(self, inputs):
        """Run the original local algorithm and return its output with attributable effects."""
        return execute_component('original', inputs, self.definitions)


# Editable inputs. Each invocation starts from these supplied registers.
# To continue a previous state, copy its result registers into these inputs.
module_input = {'payload': 'RUNALL 1', 'rail_a': [1, 0, 1, 1, 0, 1, 0, 1], 'rail_b': [0, 1, 0, 0, 1, 0, 1, 0], 'random_seed': None}
module_engine = OriginalDualRailDisplay()
module_result = module_engine.run(module_input)
