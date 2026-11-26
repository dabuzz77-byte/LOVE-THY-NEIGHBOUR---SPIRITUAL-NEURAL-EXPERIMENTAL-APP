import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Data blueprint tracking alchemical keyspace parameters and balance ledger changes.
 * Completely standalone, package-free domain entity layer.
 */
public class VirtueFrame {
    private final String timestamp;
    private final String nodeIdentifier;
    private final int stateBit;
    private final String stateName;
    private final double resolvedBalanceFloor;

    public VirtueFrame(String node, int bit, String name, double floor) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.nodeIdentifier = node;
        this.stateBit = bit;
        this.stateName = name;
        this.resolvedBalanceFloor = floor;
    }

    public void printDiagnosticFrame() {
        System.out.printf("[%s] [VIRTUE_AUDIT] Node Shard: %-25s | State Bit: %2d (%s)\n", 
                timestamp, nodeIdentifier, stateBit, stateName);
        System.out.printf("                    └── [LEDGER_COMMIT] Target Tier: GOD WISHES | Aligned Floor: £%,.2f\n", 
                resolvedBalanceFloor);
    }
}
