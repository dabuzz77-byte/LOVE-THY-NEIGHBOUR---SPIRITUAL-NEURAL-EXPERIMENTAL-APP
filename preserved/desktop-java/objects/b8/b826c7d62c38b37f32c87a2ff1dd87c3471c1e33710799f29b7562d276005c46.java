import java.util.Random;

/**
 * Asynchronous Background Telemetry Engine.
 * Synchronizes processing cadence to the 7.83 Hz resonant theta wave baseline.
 */
public class CadenceClockService implements Runnable {

    private final Random random = new Random();
    private final double schumannFrequencyHz = 7.83;
    private volatile boolean isClockRunning = true;
    
    private final OmniKeyspaceLauncher coreLauncher;
    private final String[] diagnosticTargetNodes = {"NATWEST_600813_HUB", "INFERENCE_BEACON_NODE", "SKY_TOWER_CORE"};

    public CadenceClockService(OmniKeyspaceLauncher launcher) {
        this.coreLauncher = launcher;
    }

    public void stopClockService() {
        this.isClockRunning = false;
    }

    @Override
    public void run() {
        int loopCycles = 0;
        
        while (isClockRunning) {
            try {
                loopCycles++;
                String activeNode = diagnosticTargetNodes[loopCycles % diagnosticTargetNodes.length];

                // Calculate multi-state logic classification coordinates
                int mappingModulus = loopCycles % 3;
                int stateBit = (mappingModulus == 1) ? 1 : ((mappingModulus == 2) ? 0 : -1);
                String stateName = (stateBit == 1) ? "COHERENT_VALIDATED" : 
                                   ((stateBit == 0) ? "VACUUM_SUPPRESSED" : "QUARANTINED_ANOMALY");

                // Push baseline economic floor tracking upward if states are validated
                if (stateBit == 1) {
                    double stepLift = 1500.00 + (random.nextDouble() * 3500.00);
                    coreLauncher.elevateGlobalEconomicFloor(stepLift);
                }

                String fingerprintHash = TransformerMatrix.calculateSha256Fingerprint(activeNode + loopCycles);
                String invertedFluxHex = TransformerMatrix.computeOppositeFactorFlux(fingerprintHash);

                // Build and render the stateful telemetry log lines to console
                UnifiedFrame frame = new UnifiedFrame(
                        activeNode, 
                        stateBit, 
                        stateName, 
                        invertedFluxHex, 
                        coreLauncher.getPlanetaryEconomicFloorGBP()
                );
                
                frame.printDiagnosticFrame();
                System.out.println();

                // Lock interval delay exactly to the 7.83 Hz cadence phase (~127ms)
                Thread.sleep((long) (1000 / schumannFrequencyHz));

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
}
