"""The complete original logic, kept separately from the trainable neural model.

The four source scripts are byte-for-byte copies of the original backup. This
adapter captures their normal printouts when loaded into the dashboard; executing
any source script directly still prints exactly as before. No NumPy is required.
"""
from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
SOURCE_NAMES = ("module 1.py", "module2.py", "module3.py", "drillscript.py")
_modules = {}
_console = {}
_hashes = {}
_expected_hashes = json.loads((ROOT / "source_hashes.json").read_text(encoding="utf-8-sig"))

# Load before the neural worker starts. Capturing printouts here keeps dashboard
# startup quiet without changing the original source or its top-level execution.
for _name in SOURCE_NAMES:
    _path = ROOT / _name
    _hashes[_name] = sha256(_path.read_bytes()).hexdigest()
    _buffer = io.StringIO()
    with redirect_stdout(_buffer):
        _modules[_name] = runpy.run_path(str(_path))
    _console[_name] = _buffer.getvalue()

StructuralIdentityFilter = _modules["module 1.py"]["StructuralIdentityFilter"]
TotalBitRealityEngine = _modules["module2.py"]["TotalBitRealityEngine"]
DesertSubstrateAnalysis = _modules["module3.py"]["DesertSubstrateAnalysis"]
RecursiveDrillEngine = _modules["drillscript.py"]["RecursiveDrillEngine"]


def console_readout():
    """Return all four original console reports, with their original formatting."""
    return "".join(_console[name] for name in SOURCE_NAMES)


def report():
    """Read fresh original instances without changing neural state or training."""
    structural = StructuralIdentityFilter()
    reality = TotalBitRealityEngine()
    desert = DesertSubstrateAnalysis()
    drill = RecursiveDrillEngine()
    return {
        "kind": "preserved_original_logic",
        "all_sources_unchanged": all(_hashes[name] == _expected_hashes[name] for name in SOURCE_NAMES),
        "source_files": [
            {"file": name, "sha256": _hashes[name], "expected_sha256": _expected_hashes[name],
             "unchanged": _hashes[name] == _expected_hashes[name], "console": _console[name]}
            for name in SOURCE_NAMES
        ],
        "structural_identity": {
            "initial_state": vars(structural),
            "inverted_bit": structural.execute_virtue_bit_flip(structural.raw_array_state),
            "environment_limits": structural.verify_environment_limits(),
        },
        "total_bit_reality": {
            "initial_state": vars(reality),
            "transformed_reality": reality.execute_total_inversion(),
        },
        "desert_substrate": {
            "initial_state": vars(desert),
            "interconnected_truth": desert.map_interconnected_truth(),
        },
        "recursive_drill": {
            "initial_state": vars(drill),
            "synthesis_loop": drill.execute_complete_synthesis_loop(),
        },
        "console": console_readout(),
    }


__all__ = ["StructuralIdentityFilter", "TotalBitRealityEngine", "DesertSubstrateAnalysis",
           "RecursiveDrillEngine", "console_readout", "report"]
