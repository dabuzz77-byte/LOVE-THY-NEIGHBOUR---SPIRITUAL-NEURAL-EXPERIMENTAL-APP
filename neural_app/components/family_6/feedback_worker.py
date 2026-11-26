"""Optional worker: consumes field bits and sends a changing numerical signal back."""
import time
import math
import socket
from .atelier_bus import Client
bus = Client('Feedback oscillator')
try:
    while True:
        try:
            field = bus.receive()
            bit_level = sum(field['bits']) / 96
            signal = math.sin(field['ticks'] * 0.035) * 0.6 + (bit_level - 0.5) * 0.8
            bus.signal(signal)
            print(f'{signal:.6f}', flush=True)
            time.sleep(0.1)
        except (socket.timeout, OSError):
            time.sleep(0.5)
finally:
    bus.close()
