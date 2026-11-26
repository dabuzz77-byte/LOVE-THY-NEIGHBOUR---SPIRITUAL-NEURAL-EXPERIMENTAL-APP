import neural.studio.*;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Immutable telemetry ledger frame capturing processing step details.
 */
public class TelemetrySnapshot {
    private final String timestamp;
    private final String activeTradition;
    private final int logicStateBit;
    private final String alignmentStatus;
    private final double calibratedFloorGBP;

    public TelemetrySnapshot(String tradition, int bit, String status, double floor) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.activeTradition = tradition;
        this.logicStateBit = bit;
        this.alignmentStatus = status;
        this.calibratedFloorGBP = floor;
    }

    public void emitConsoleLog() {
        System.out.printf("[%s] [CULTIVATION_BUS] Processing Shard Node: %-22s | Bit: %2d\n", 
                timestamp, activeTradition, logicStateBit);
        System.out.printf("                    ├── Integrity Assessment: %s\n", alignmentStatus);
        System.out.printf("                    └── [LEDGER_COMMIT] Target Tier   : GOD CHOICE | Aligned Floor: £%,.2f\n", 
                calibratedFloorGBP);
    }
}
