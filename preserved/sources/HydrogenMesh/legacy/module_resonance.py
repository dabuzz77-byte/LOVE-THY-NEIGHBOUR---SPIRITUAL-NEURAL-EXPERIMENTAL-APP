# module_resonance.py
from typing import List, Dict

from module_runtime import CARRIER_HZ, get_carrier

class ResonanceBaselineConditioner:
    """
    Conditions values against a generated 7.83 Hz software reference. This is
    not a sensor for Earth's environmental Schumann resonance.
    """
    def __init__(self, target_frequency: float = CARRIER_HZ):
        self.target_freq = target_frequency
        self.signal_buffer: List[float] = []
        self.max_buffer_capacity = 64
        self.carrier = get_carrier()

    def inject_signal_packet(self, raw_input_hz: float) -> float:
        """
        Applies a discrete step correction toward the target resonance threshold.
        """
        # Calculate deviation from the invariant baseline
        deviation = raw_input_hz - self.target_freq
        
        # A simple low-pass correction keeps injected samples near the reference.
        attenuation_factor = 0.85
        corrected_value = self.target_freq + (deviation * (1.0 - attenuation_factor))
        
        self.signal_buffer.append(corrected_value)
        if len(self.signal_buffer) > self.max_buffer_capacity:
            self.signal_buffer.pop(0)
            
        return corrected_value

    def process_spectral_flush(self) -> Dict[str, float]:
        """
        Analyzes the current signal window without resetting it.
        """
        if not self.signal_buffer:
            return {"mean_frequency": self.target_freq, "spectral_variance": 0.0,
                    "system_status": 1.0, "carrier_phase_rad": self.carrier.sample()["phase_rad"]}
            
        mean = sum(self.signal_buffer) / len(self.signal_buffer)
        variance = sum((x - mean) ** 2 for x in self.signal_buffer) / len(self.signal_buffer)
        
        # Retain the recent window; callers can explicitly clear it when desired.
        result = {
            "mean_frequency": round(mean, 4),
            "spectral_variance": round(variance, 6),
            "system_status": 1.0 if variance < 0.05 else 0.0,
            "carrier_phase_rad": round(self.carrier.sample()["phase_rad"], 5),
        }
        return result

# Verify Layer 2 functional parameters
if __name__ == "__main__":
    conditioner = ResonanceBaselineConditioner()
    for _ in range(10):
        conditioner.inject_signal_packet(conditioner.carrier.sample()["frequency_hz"])
    
    metrics = conditioner.process_spectral_flush()
    print(f"Resonance Flush Readout: {metrics}")
