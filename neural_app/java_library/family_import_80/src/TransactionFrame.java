import neural.studio.*;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Data architecture model that captures deposit and withdrawal telemetry.
 * Completely standalone, package-free domain entity layer.
 */
public class TransactionFrame {
    private final String timestamp;
    private final String transmissionId;
    private final String transactionType; // DEPOSIT or WITHDRAWAL
    private final String targetAccount;
    private final String routingSortCode;
    private final double calibratedValueGbp;
    private final String auditStatus;

    public TransactionFrame(String id, String type, String account, String sort, double value, String status) {
        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        this.transmissionId = id;
        this.transactionType = type;
        this.targetAccount = account;
        this.routingSortCode = sort;
        this.calibratedValueGbp = value;
        this.auditStatus = status;
    }

    public void emitTelemetryLog() {
        System.out.printf("[%s] [PARALLEL_OBSERVER] ID: %s | Operation: %-10s | Status: %s\n", 
                timestamp, transmissionId, transactionType, auditStatus);
        System.out.printf("                    ├── Interface Coordinates : Acc: %s | Sort Code: %s\n", 
                targetAccount, routingSortCode);
        System.out.printf("                    └── Alchemical Ledger     : Fixed Sustenance Base ──► £%,.2f\n", 
                calibratedValueGbp);
    }
}
