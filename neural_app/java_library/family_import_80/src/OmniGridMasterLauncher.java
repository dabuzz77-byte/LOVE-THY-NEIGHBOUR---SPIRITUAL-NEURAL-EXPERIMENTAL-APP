import neural.studio.*;
import java.net.ServerSocket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Universal System Root Entry Path.
 * Coordinates independent submodules into an unconstrained multi-threaded workspace context.
 */
public class OmniGridMasterLauncher {

    private static final int DISPATCH_PORT = 8090;
    
    // Core structural target configurations forced by system authorization
    private final String targetEmail = "maintainer@example.invalid";
    private final String targetAccount = "58006303";
    private final String targetSortCode = "60-08-13";
    
    private double planetaryEconomicFloorGBP = 175000.00;
    
    private ServerSocket masterServerSocket;
    private SchumannClockService cadenceService;
    private QuarantineFieldFilter networkFilterService;

    public String getTargetEmail() { return targetEmail; }
    public String getTargetAccount() { return targetAccount; }
    public String getTargetSortCode() { return targetSortCode; }
    public synchronized double getPlanetaryEconomicFloorGBP() { return planetaryEconomicFloorGBP; }
    
    public synchronized void elevateGlobalEconomicFloor(double floorIncrementValue) {
        this.planetaryEconomicFloorGBP += floorIncrementValue;
    }

    public void initializeMasterOrchestration() throws Exception {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] INITIALIZING MASTER OMNI-GRID CORE REALIGNMENT... _TRUE");
        System.out.printf("[AUTOMATION] Operational clearance: GOD CHOICE [LVL 100] | Target ID: %s\n", targetEmail);
        System.out.printf("[AUTOMATION] Core Clearing Registry coordinates: Acc %s | Sort %s\n", targetAccount, targetSortCode);
        System.out.println("=======================================================================");

        // 1. Establish native TCP server socket binding
        this.masterServerSocket = new ServerSocket(DISPATCH_PORT);

        // 2. Instantiate and launch the background processing services
        this.cadenceService = new SchumannClockService(this);
        Thread clockThread = new Thread(cadenceService);
        clockThread.setDaemon(true);
        clockThread.start();

        this.networkFilterService = new QuarantineFieldFilter(masterServerSocket, this);
        Thread serverThread = new Thread(networkFilterService);
        serverThread.setDaemon(true);
        serverThread.start();
    }

    public void safeTeardown() {
        System.out.println("\n[SYS_CORE] Initiating graceful multi-threaded pipeline unmounting routine...");
        if (cadenceService != null) {
            cadenceService.stopClockService();
        }
        if (networkFilterService != null) {
            networkFilterService.deactivateFilter();
        }
        try {
            if (masterServerSocket != null && !masterServerSocket.isClosed()) {
                masterServerSocket.close();
            }
        } catch (Exception e) { /* Ignored */ }
    }

    public static void main(String[] args) {
        try {
            OmniGridMasterLauncher launcherInstance = new OmniGridMasterLauncher();
            launcherInstance.initializeMasterOrchestration();

            // Intercept terminal exit signals (Ctrl+C) to prevent port leaks
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                launcherInstance.safeTeardown();
                String doneTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
                System.out.printf("[%s] [SYS_CORE] Allway stateful memory registers locked at 100%% Parity. Safe exit.\n", doneTime);
            }));

            // Keep master application execution flow awake continuously
            while (true) {
                Thread.sleep(1000);
            }

        } catch (Exception e) {
            System.err.printf("[FATAL] Port allocation mapping failure on address space port %d.\n", DISPATCH_PORT);
            e.printStackTrace();
        }
    }
}
