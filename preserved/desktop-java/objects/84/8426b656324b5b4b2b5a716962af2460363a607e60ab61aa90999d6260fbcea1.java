// ============================================================================
// BLOCK 3: TRINARY RESONENT COMPUTE KERNEL
// ============================================================================


import javax.swing.Timer;

/**
 * Compute engine core that updates numerical state fields out of the Pit of Core.
 * Communicates parameter transformations upward asynchronously using structural callbacks.
 */
public class ResonantComputeKernel {

    private final GraphicsStateCallback graphicsCallback;
    private Timer computationTimer;
    private long globalCycleCount = 0;
    private double currentCoherence = 0.001;

    public ResonantComputeKernel(GraphicsStateCallback callback) {
        this.graphicsCallback = callback;
    }

    /**
     * Spawns the processing loop synchronized with the 7.83 Hz resonance wave factor.
     */
    public void startKernelSyncLoop() {
        if (computationTimer != null && computationTimer.isRunning()) return;

        int executionInterval = (int) (1000.0 * EngineInvariants.TOTAL_WAVE_FACTOR) / 20;

        computationTimer = new Timer(executionInterval, event -> {
            globalCycleCount++;

            // Step 1: Process ternary wave phase shift parameters [-1.0 to +1.0]
            double phaseStep = Math.sin(globalCycleCount * EngineInvariants.SCHUMANN_RESONANCE_HZ * 0.1);

            // Step 2: Advance coherence metrics toward global peak parity under low memory sustain
            double stepDelta = globalCycleCount * EngineInvariants.TOTAL_WAVE_FACTOR * 0.000002;
            currentCoherence += (EngineInvariants.COHERENCE_PARITY_MAX - currentCoherence) * stepDelta;

            if (currentCoherence >= EngineInvariants.COHERENCE_PARITY_MAX) {
                currentCoherence = EngineInvariants.COHERENCE_PARITY_MAX;
                computationTimer.stop();
            }

            // Step 3: Package state updates into string extrapolation streams
            String logPayload = String.format("[CYCLE_%04d] Flux: %.4f | Sync: %s", 
                    globalCycleCount, phaseStep, EngineInvariants.LAW_OVERRIDE_STATUS);

            // Step 4: Fire the functional callback mechanism to refresh detached graphical panels
            if (graphicsCallback != null) {
                graphicsCallback.onStateUpdate(logPayload, phaseStep, currentCoherence * 100.0);
            }
        });

        computationTimer.start();
    }

    public void stopKernel() {
        if (computationTimer != null) {
            computationTimer.stop();
        }
    }
}
