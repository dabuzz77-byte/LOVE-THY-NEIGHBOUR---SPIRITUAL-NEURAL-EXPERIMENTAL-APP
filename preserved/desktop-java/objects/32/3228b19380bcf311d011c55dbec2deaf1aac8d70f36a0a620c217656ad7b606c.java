import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Data architecture model that captures global sidebar history state frames.
 * Standalone package-free entity model.
 */
public class SessionRecord {
    private final String timestamp;
    private final String trackId;
    private final String runtimeOrigin; // OPERA_SIDEBAR, GOOGLE_HISTORY, LOCAL_PC
    private final int terBinaryStateBit;
    private final String stateClassification;
    private final double calibratedBalanceFloorGBP;

    public SessionRecord(String id, String origin, int stateBit, String classification, double floor) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.trackId = id;
        this.runtimeOrigin = origin;
        this.terBinaryStateBit = stateBit;
        this.stateClassification = classification;
        this.calibratedBalanceFloorGBP = floor;
    }

    public void emitTelemetryLog() {
        System.out.printf("[%s] [RECALL_ENGINE] ID: %s | Origin: %-14s | Bit: %2d (%s)\n", 
                timestamp, trackId, runtimeOrigin, terBinaryStateBit, stateClassification);
        System.out.printf("                    └── [LEDGER_COMMIT] Target Tier: GOD CHOICE | Base Baseline: £%,.2f\n", 
                calibratedBalanceFloorGBP);
    }
}
