"""Optional worker: consumes field bits and sends a changing numerical signal back."""
import time,math,socket
from atelier_bus import Client
bus=Client('Feedback oscillator')
try:
    while True:
        try:
            field=bus.receive()
            bit_level=sum(field['bits'])/96
            signal=math.sin(field['ticks']*.035)*.6+(bit_level-.5)*.8
            bus.signal(signal)
            print(f'{signal:.6f}',flush=True)
            time.sleep(.1)
        except (socket.timeout,OSError): time.sleep(.5)
finally:
    bus.close()
