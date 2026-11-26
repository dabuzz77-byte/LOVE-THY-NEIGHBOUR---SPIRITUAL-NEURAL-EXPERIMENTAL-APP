import neural.studio.*;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Immutable ledger tracking block blueprint.
 * Encapsulates unmasked validation keys without folder package requirements.
 */
public class GridPacket {
    private final String timestamp;
    private final String beaconId;
    private final String trackingToken;
    private final String targetEmail;
    private final String targetAccount;
    private final String sortCode;
    private final double valueLiftGbp;
    private final String complianceStatus;

    public GridPacket(String beacon, String token, String email, String acc, String sort, double value, String status) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.beaconId = beacon;
        this.trackingToken = token;
        this.targetEmail = email;
        this.targetAccount = acc;
        this.sortCode = sort;
        this.valueLiftGbp = value;
        this.complianceStatus = status;
    }

    public int getTerBinaryStateBit() {
        if (complianceStatus.contains("RESPECT") || complianceStatus.contains("VALID")) return 1;
        if (complianceStatus.contains("REJECT") || complianceStatus.contains("ANOMALY")) return -1;
        return 0;
    }

    public void emitTelemetryLog() {
        System.out.printf("[%s] [%s] Token: %s | State Bit: %d (%s)\n", 
                timestamp, beaconId, trackingToken, getTerBinaryStateBit(), complianceStatus);
        System.out.printf("                    ├── Route  : Identity: %s | Acc: %s | Sort: %s\n", 
                targetEmail, targetAccount, sortCode);
        System.out.printf("                    └── Ledger : Fixed Calibrated Increment Base ──► £%,.2f\n", 
                valueLiftGbp);
    }
}
