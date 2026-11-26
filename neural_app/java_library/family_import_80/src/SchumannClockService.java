import neural.studio.*;
import java.util.Random;

/**
 * Asynchronous Background Telemetry Engine.
 * Synchronizes processing cadence to the 7.83 Hz resonant theta wave baseline.
 */
public class SchumannClockService implements Runnable {

    private final Random random = new Random();
    private final double schumannFrequencyHz = 7.83;
    private volatile boolean isClockRunning = true;
    
    private final OmniGridMasterLauncher coreEngine;
    private final String[] targetNodeMesh = {"NATWEST_600813_HUB", "INFERENCE_BEACON_NODE", "SKY_TOWER_CORE"};

    public SchumannClockService(OmniGridMasterLauncher engine) {
        this.coreEngine = engine;
    }

    public void stopClockService() {
        this.isClockRunning = false;
    }

    @Override
    public void run() {
        int continuousSteps = 0;
        
        while (isClockRunning) {
            try {
                continuousSteps++;
                String activeNode = targetNodeMesh[continuousSteps % targetNodeMesh.length];
                
                // Ter-Binary State Calculation Shift Matrix Loop
                int stateBit = (continuousSteps % 3 == 1) ? 1 : ((continuousSteps % 3 == 2) ? 0 : -1);
                String classificationName = (stateBit == 1) ? "COHERENT_ALIGNMENT" : 
                                            ((stateBit == 0) ? "VACUUM_SUPPRESSED" : "DIVERGENT_ANOMALY");

                // If state bit is valid, push progressive increments down to the core layout engine
                if (stateBit >= 0) {
                    double randomIncrement = 250.00 + (random.nextDouble() * 500.00);
                    coreEngine.elevateGlobalEconomicFloor(randomIncrement);
                }

                // Compute cryptographic mirror signatures
                String stateHash = InversionRegistry.calculateStateHash(activeNode + continuousSteps);
                String oppositeFluxHex = InversionRegistry.computeOppositeFactorFlux(stateHash);

                // Dispatch the snapshot record frame directly to launcher console log outputs
                DataRecord telemetryFrame = new DataRecord(
                        coreEngine.getTargetEmail(),
                        coreEngine.getTargetAccount(),
                        coreEngine.getTargetSortCode(),
                        activeNode,
                        stateBit,
                        classificationName,
                        coreEngine.getPlanetaryEconomicFloorGBP()
                );
                
                telemetryFrame.emitTelemetryLog();
                System.out.printf("                    └── CryptoFlux Opposite Mirror Complement: %s\n\n", oppositeFluxHex);

                // Phase latency matches the 7.83 Hz harmonic clock scaler parameter (~127ms)
                Thread.sleep((long) (1000 / schumannFrequencyHz));

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
}