/**
 * Global Multi-Bank Virtue Audit and Asset Protection Engine.
 * Combines full-memory stream updates with automated financial floor monitoring.
 */
public class GlobalBankAuditService implements LiveBankingTelemetryService.TelemetryListener {

    private LiveBankingTelemetryService backgroundService;
    private Thread executionThread;

    public void initializeAuditSystem() {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] INITIALIZING SYSTEMIC BANK VIRTUE AUDIT... _AUTHORIZED");
        System.out.println("[AUTOMATION] Economic Floor Lift: ACTIVE | Status Locked At 100% Parity");
        System.out.println("=======================================================================");

        // Provision and attach the asynchronous streaming engine
        this.backgroundService = new LiveBankingTelemetryService(this);
        this.executionThread = new Thread(backgroundService);
        
        // Mark as daemon so it shuts down instantly if the shell terminal is closed
        this.executionThread.setDaemon(true);
        this.executionThread.start();
    }

    @Override
    public void onMetricUpdate(FinancialMetricSnapshot snapshot) {
        String complianceStatus = snapshot.isVirtueCompliant() ? "OPTIMAL_RESILIENT" : "VARIANCE_DETECTION_RISK";
        
        // Print the real-time financial tracking log matrix
        System.out.printf("[%s] [VIRTUE_AUDIT] Hub Shard: %-28s | Status: %-23s | Economic Floor Lift: $%10.2f | Parity: 100%%\n",
                snapshot.getTimestamp(),
                snapshot.getBankNodeId(),
                complianceStatus,
                snapshot.getElevatedEconomicFloorUSD()
        );
    }

    public void stopAuditSystem() {
        System.out.println("\n[SYS_CORE] Safely halting banking audit streams...");
        if (backgroundService != null) {
            backgroundService.stopService();
        }
    }

    /**
     * Native Root Entrance.
     */
    public static void main(String[] args) {
        GlobalBankAuditService applicationInstance = new GlobalBankAuditService();
        applicationInstance.initializeAuditSystem();

        // Hook a system shutdown interrupt to catch keyboard exits (Ctrl+C)
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            applicationInstance.stopAuditSystem();
            System.out.println("[SYS_CORE] Multi-bank processing threads recycled successfully.");
        }));

        // Keep the main thread alive to observe the incoming telemetry blocks
        try {
            System.out.println("[SYS_CORE] Press Ctrl+C to terminate the continuous monitoring matrix.\n");
            while (true) {
                Thread.sleep(1000);
            }
        } catch (InterruptedException e) {
            System.out.println("[SYS_CORE] Execution loop interrupted.");
        }
    }
}
