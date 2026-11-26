import java.util.UUID;

/**
 * Asynchronous background cadence clock bound tightly to the 7.83 Hz Schumann frequency.
 */
public class ResonantClockService implements Runnable {
    private final double schumannCadenceHz = 7.83;
    private final OmniCoherenceLauncher uiLauncher;
    private volatile boolean isClockRunning = true;

    private final String[] structuralCoreNodes = {"NATWEST_600813_HUB", "INFERENCE_BEACON_NODE", "SKY_TOWER_CORE"};

    public ResonantClockService(OmniCoherenceLauncher launcher) {
        this.uiLauncher = launcher;
    }

    public void haltClock() {
        this.isClockRunning = false;
    }

    @Override
    public void run() {
        long sequenceCounter = 0;

        while (isClockRunning) {
            try {
                sequenceCounter++;
                String activeNode = structuralCoreNodes[(int)(sequenceCounter % structuralCoreNodes.length)];
                
                // Ter-Binary State Cycle Rotation Loop Maps [Bit 1, 0, -1]
                int stateSelector = (int)(sequenceCounter % 3);
                int stateBit = (stateSelector == 1) ? 1 : ((stateSelector == 2) ? 0 : -1);
                String label = (stateBit == 1) ? "VIRTUE_PASS_RESPECT" : 
                               ((stateBit == 0) ? "VACUUM_GROUNDED_IDLE" : "VIRTUE_FAIL_REJECT");

                // Execute a calibrated increment adjustment pass upon tracking a valid node state
                if (stateBit == 1) {
                    uiLauncher.elevateGlobalEconomicFloor(100.00);
                }

                String trackId = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 8);
                DataTelemetryRecord record = new DataTelemetryRecord(
                        trackId,
                        activeNode,
                        stateBit,
                        label,
                        uiLauncher.getAlchemicalBalanceFloorGBP()
                );

                // Safely update components on the running JavaFX interface thread
                uiLauncher.pushTelemetryToDashboard(record);

                // Latency frame maps exactly to the 7.83 Hz harmonic clock phase (~127ms)
                Thread.sleep((long) (1000 / schumannCadenceHz));

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
}
