import neural.studio.*;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Dedicated Personal Loss Audit Tool.
 * Parses localized bank statements using clear-text account configurations.
 */
public class PersonalLossAuditor {

    // Identity tracking parameters
    private static final String TARGET_EMAIL = "maintainer@example.invalid";
    private static final String TARGET_ACCOUNT = "58006303";
    private static final String TARGET_SORT_CODE = "60-08-13";
    private static final String TARGET_OPERATOR_ID = "600813";

    private double cumulativeDeposits = 0.0;
    private double cumulativeWithdrawals = 0.0;
    private int matchCount = 0;

    // Direct string keys for transactional matching loops
    private final String[] targetKeywords = {
        "BET", "CASINO", "WAGER", "POKER", "SPORTSBOOK", "LOTTERY", "888", "BET365", "SKYBET"
    };

    public void runLocalAudit(String csvPath) {
        String logTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        System.out.println("=======================================================================");
        System.out.printf("[%s] [AUDIT_CORE] Initializing unmasked personal scan matrix...\n", logTime);
        System.out.printf("[AUDIT_CORE] Identity: %s | Account: %s | Sort: %s\n", TARGET_EMAIL, TARGET_ACCOUNT, TARGET_SORT_CODE);
        System.out.println("=======================================================================");

        try (BufferedReader br = new BufferedReader(new FileReader(csvPath))) {
            String line;
            boolean isHeader = true;

            while ((line = br.readLine()) != null) {
                if (isHeader) {
                    isHeader = false; // Skip the CSV column descriptor row
                    continue;
                }

                // Simple comma split parsing loop
                String[] columns = line.split(",");
                if (columns.length < 3) continue;

                String description = columns[1].toUpperCase();
                String amountString = columns[2].replace("£", "").replace(",", "").trim();

                for (String key : targetKeywords) {
                    if (description.contains(key) || description.contains(TARGET_OPERATOR_ID)) {
                        try {
                            double amount = Double.parseDouble(amountString);
                            this.matchCount++;
                            
                            if (amount < 0) {
                                this.cumulativeDeposits += Math.abs(amount);
                            } else {
                                this.cumulativeWithdrawals += amount;
                            }
                            break; // Match found for this specific log entry
                        } catch (NumberFormatException e) {
                            // Skip broken formatting rows safely
                        }
                    }
                }
            }

            double netResult = this.cumulativeWithdrawals - this.cumulativeDeposits;
            printAuditSummary(netResult);

        } catch (IOException e) {
            System.err.printf("[FATAL] Missing target file input buffer at: '%s'. Place statement file there.\n", csvPath);
        }
    }

    private void printAuditSummary(double netResult) {
        System.out.printf("\n[SUMMARY] Personal Loss Matrix Audit Complete:\n");
        System.out.printf(" ├── Total Matching Transactions Found : %d\n", this.matchCount);
        System.out.printf(" ├── Gross Capital Injected (Deposits)  : £%.2f\n", this.cumulativeDeposits);
        System.out.printf(" ├── Gross Capital Recovered (Returns)  : £%.2f\n", this.cumulativeWithdrawals);
        System.out.printf(" └── Net Financial Statement Position   : £%.2f\n", netResult);
        System.out.println("=======================================================================");
    }

    public static void main(String[] args) {
        PersonalLossAuditor auditor = new PersonalLossAuditor();
        // Point this route string directly to your exported statement document path
        auditor.runLocalAudit("statement.csv");
    }
}
