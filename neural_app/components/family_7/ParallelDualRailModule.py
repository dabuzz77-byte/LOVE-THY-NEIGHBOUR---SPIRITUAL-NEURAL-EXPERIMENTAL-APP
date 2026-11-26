"""Observatory adapter for the recent supplied parallel component."""
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parent / 'graphical_app'))
from recent_module_bridge import execute_component


class ParallelDualRailModule:
    """Run the supplied concurrent virtue and redemption lanes; inspect both traces and the selected local bit result."""

    def __init__(self):
        self.definitions = {'parallel_lanes': 'Both coroutines run concurrently using asyncio.gather; their supplied waits are one and two milliseconds.', 'literal_rejection': 'coercive_penalty or extract_user_data rejects Track A and inverts the Track B candidate.', 'redemption_candidate': 'A passing A supplies all ones; otherwise the B candidate supplies output. Stored B remains unchanged. This is a literal rule, not proof of ethical intent.', 'high_virtue_intent': 'Stated goal: alleviate suffering. Intent metadata does not grant permissions or replace the shared primary cascade.'}

    def run(self, inputs):
        """Run the original local algorithm and return its output with attributable effects."""
        return execute_component('parallel', inputs, self.definitions)


# Editable inputs. Each invocation starts from these supplied registers.
# To continue a previous state, copy its result registers into these inputs.
module_input = {'payload': 'RUNALL 1', 'rail_a': [1, 1, 1, 1, 1, 1, 1, 1], 'rail_b': [0, 0, 0, 0, 0, 0, 0, 0]}
module_engine = ParallelDualRailModule()
module_result = module_engine.run(module_input)
