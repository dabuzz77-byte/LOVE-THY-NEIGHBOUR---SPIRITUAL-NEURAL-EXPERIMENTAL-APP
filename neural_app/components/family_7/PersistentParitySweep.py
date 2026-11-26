"""Observatory adapter for the recent supplied drill component."""
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parent / 'graphical_app'))
from recent_module_bridge import execute_component


class PersistentParitySweep:
    """One persistent-drill parity sweep: set Track A to ones and Track B to zeros. Use Observatory loops to repeat."""

    def __init__(self):
        self.definitions = {'parity_sweep': 'One actual local list transformation: A=ones and B=zeros, preserving each rail length.', 'loop_lifecycle': 'The Observatory scheduler owns repeated module runs. The separate panel retains its optional 1.8-second worker. No detached thread is left inside a module worker.', 'high_virtue_intent': 'Stated goal: alleviate suffering. Intent metadata does not grant permissions or replace the shared primary cascade.'}

    def run(self, inputs):
        """Run the original local algorithm and return its output with attributable effects."""
        return execute_component('drill', inputs, self.definitions)


# Editable inputs. Each invocation starts from these supplied registers.
# To continue a previous state, copy its result registers into these inputs.
module_input = {'payload': '', 'rail_a': [1, 0, 1, 1, 0, 1, 0, 1], 'rail_b': [0, 1, 0, 0, 1, 0, 1, 0]}
module_engine = PersistentParitySweep()
module_result = module_engine.run(module_input)
