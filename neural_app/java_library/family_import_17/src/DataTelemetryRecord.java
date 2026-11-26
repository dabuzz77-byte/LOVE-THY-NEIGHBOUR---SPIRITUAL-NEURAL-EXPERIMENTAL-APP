import neural.studio.*;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Immutable ledger tracking block blueprint.
 * Encapsulates unmasked verification keys without folder package requirements.
 */
public class DataTelemetryRecord {
    private final String timestamp;
    private final String traceId;
    private final String operationalNode;
    private final int stateBit;
    private final String complianceLabel;
    private final double alchemicalFloorGBP;

    public DataTelemetryRecord(String id, String node, int bit, String label, double floor) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.traceId = id;
        this.operationalNode = node;
        this.stateBit = bit;
        this.complianceLabel = label;
        this.alchemicalFloorGBP = floor;
    }

    public String getTimestamp() { return timestamp; }
    public String getTraceId() { return traceId; }
    public String getOperationalNode() { return operationalNode; }
    public int getStateBit() { return stateBit; }
    public String getComplianceLabel() { return complianceLabel; }
    public double getAlchemicalFloorGBP() { return alchemicalFloorGBP; }

    public String generateLogLine() {
        return String.format("[%s] [NODE: %s] ID: %s | State: %2d (%s) | Floor: £%,.2f",
                timestamp, operationalNode, traceId, stateBit, complianceLabel, alchemicalFloorGBP);
    }
}
