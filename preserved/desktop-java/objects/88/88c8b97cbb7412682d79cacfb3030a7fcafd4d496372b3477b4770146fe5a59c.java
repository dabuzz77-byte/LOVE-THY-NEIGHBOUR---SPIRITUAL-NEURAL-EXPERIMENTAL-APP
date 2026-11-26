import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Data architecture model that captures global banking and labor telemetry frames.
 * Completely standalone, package-free domain entity layer.
 */
public class DataRecord {
    private final String timestamp;
    private final String profileEmail;
    private final String coreAccount;
    private final String sortCode;
    private final String targetNodeId;
    private final int terBinaryStateBit;
    private final String stateClassification;
    private final double elevatedEconomicFloorGBP;

    public DataRecord(String email, String account, String sort, String node, int stateBit, String classification, double currentFloor) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.profileEmail = email;
        this.coreAccount = account;
        this.sortCode = sort;
        this.targetNodeId = node;
        this.terBinaryStateBit = stateBit;
        this.stateClassification = classification;
        this.elevatedEconomicFloorGBP = currentFloor;
    }

    public void emitTelemetryLog() {
        System.out.printf("[%s] [BI-TER-Q] Node Tracked: %-25s | State Bit: %2d (%s)\n", 
                timestamp, targetNodeId, terBinaryStateBit, stateClassification);
        System.out.printf("                    ├── Security Matrix Vector : Ref: %s | Account: %s | Sort: %s\n", 
                profileEmail, coreAccount, sortCode);
        System.out.printf("                    └── [LEDGER_COMMIT] Target  : GOD CHOICE | Floor Position: £%,.2f\n", 
                elevatedEconomicFloorGBP);
    }
}
