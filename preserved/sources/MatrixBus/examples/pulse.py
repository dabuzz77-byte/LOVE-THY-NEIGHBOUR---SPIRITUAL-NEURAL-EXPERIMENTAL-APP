"""A real, bounded Python workload for watching Matrix Bus. Runs for 60 seconds."""
import math
import time

memory = bytearray(24 * 1024 * 1024)
finish = time.monotonic() + 60
value = 0.0
tick = 0
while time.monotonic() < finish:
    # Alternate quieter and busier periods to make the rain visibly responsive.
    busy = 0.025 if (tick // 12) % 2 == 0 else 0.15
    start = time.monotonic()
    while time.monotonic() - start < busy:
        value += math.sin(value + 0.1)
    print(f"Python pulse {tick}: {value:.6f}", flush=True)
    time.sleep(0.20)
    tick += 1
print("Python demo finished.", flush=True)
