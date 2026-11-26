import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Data blueprint tracking frozen keyspace parameters and ledger changes.
 * Completely standalone, package-free domain entity layer.
 */
public class UnifiedFrame {
    private final String timestamp;
    private final String nodeIdentifier;
    private final int stateBit;
    private final String stateName;
    private final String oppositeFluxHex;
    private final double resolvedFloor;

    public UnifiedFrame(String node, int bit, String name, String fluxHex, double floor) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.nodeIdentifier = node;
        this.stateBit = bit;
        this.stateName = name;
        this.oppositeFluxHex = fluxHex;
        this.resolvedFloor = floor;
    }

    public void printDiagnosticFrame() {
        System.out.printf("[%s] [TER-BI-Q] Node Shard: %-25s | State: %2d (%s)\n", 
                timestamp, nodeIdentifier, stateBit, stateName);
        System.out.printf("                    ├── Opposing Factor Flux Fingerprint : %s\n", oppositeFluxHex);
        System.out.printf("                    └── [LEDGER_COMMIT] Target Baseline : £%,.2f\n", resolvedFloor);
    }
}
