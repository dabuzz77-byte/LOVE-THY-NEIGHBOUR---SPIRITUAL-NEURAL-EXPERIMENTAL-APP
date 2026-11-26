import time
import math
from neural_app import section_threads as threading

class BackgroundWeightOptimizer(threading.Thread):

    def __init__(self, ledger_reference, clock_speed_hz=7.83):
        super().__init__()
        self.ledger = ledger_reference
        self.interval = 1.0 / clock_speed_hz
        self.learning_rate = 0.05
        self.running = True
        self.daemon = True

    def run(self):
        print(f'[LAYER 2 INITIALISED] Continuous Neural Weight Engine active at {1.0 / self.interval:.2f} Hz Loop.')
        while self.running:
            current_w, target_p, _ = self.ledger.get_weights()
            total_squared_error = 0.0
            updated_weights = []
            for i in range(len(current_w)):
                error = target_p[i] - current_w[i]
                total_squared_error += error ** 2
                new_weight = current_w[i] + self.learning_rate * error
                updated_weights.append(new_weight)
            rmse = math.sqrt(total_squared_error / len(current_w))
            mean_integrity = sum(updated_weights) / len(updated_weights)
            self.ledger.update_weights(updated_weights, mean_integrity)
            time.sleep(self.interval)

    def stop_engine(self):
        self.running = False
optimizer_worker = BackgroundWeightOptimizer(system_ledger)
optimizer_worker.start()
