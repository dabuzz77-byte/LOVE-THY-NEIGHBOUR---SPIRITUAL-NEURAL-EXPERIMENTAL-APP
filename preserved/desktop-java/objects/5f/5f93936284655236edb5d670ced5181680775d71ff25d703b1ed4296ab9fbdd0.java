package engine.clock;

import engine.core.SubstrateContract;
import engine.model.TelemetryModel;
import java.util.Random;

public class SchumannClockLoop implements Runnable {
    private final TelemetryModel model;
    private final Runnable renderCallback;
    private boolean running = true;
    private final Random rand = new Random();
    private int localCycles = 0;

    public SchumannClockLoop(TelemetryModel model, Runnable renderCallback) {
        this.model = model;
        this.renderCallback = renderCallback;
    }

    @Override
    public void run() {
        SubstrateContract.enforceSanity();
        long interval = (long) (1000.0 / SubstrateContract.SCHUMANN_BASE_HZ);
        
        while (running) {
            try {
                localCycles++;
                double elapsed = localCycles * (interval / 1000.0);
                double jitter = (rand.nextDouble() * 0.1) - 0.05;
                double activeFreq = SubstrateContract.SCHUMANN_BASE_HZ + jitter;
                double flux = Math.sin(2 * Math.PI * activeFreq * elapsed);
                
                double targetDebt = model.getAlgorithmicDebtTar() + 0.015 * Math.abs(flux);
                if (flux < -0.4) targetDebt *= 0.08; // Clear out system variables

                double score = 0.95 + (0.04 * flux) + (rand.nextDouble() * 0.005);
                
                model.updateState(flux, activeFreq, targetDebt, Math.min(score, 1.0), localCycles);
                renderCallback.run();
                
                Thread.sleep(interval);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
    
    public void terminate() { this.running = false; }
}
