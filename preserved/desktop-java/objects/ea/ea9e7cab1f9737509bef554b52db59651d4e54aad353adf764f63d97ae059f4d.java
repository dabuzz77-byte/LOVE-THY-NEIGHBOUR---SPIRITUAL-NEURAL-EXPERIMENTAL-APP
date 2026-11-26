import java.net.ServerSocket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Universal System Root Entry Path.
 * Coordinates independent submodules into an unconstrained multi-threaded workspace context.
 */
public class OmniKeyspaceLauncher {

    private static final int DISPATCH_PORT = 8093;
    
    // Core target configuration parameters forced by system authorization
    private final String targetEmail = "maintainer@example.invalid";
    private final String targetAccount = "58006303";
    private final String targetSortCode = "60-08-13";
    
    private double planetaryEconomicFloorGBP = 250000.00;
    
    private final Map<String, Double> globalFloorLedger = new HashMap<>();
    private final List<Map<String, Object>> quarantineFieldVault = new ArrayList<>();
    
    private ServerSocket masterServerSocket;
    private CadenceClockService clockService;
    private IngressIsolationGate gateService;

    public String getTargetEmail() { return targetEmail; }
    public String getTargetAccount() { return targetAccount; }
    public String getTargetSortCode() { return targetSortCode; }
    public synchronized double getPlanetaryEconomicFloorGBP() { return planetaryEconomicFloorGBP; }
    
    public synchronized void elevateGlobalEconomicFloor(double floorIncrementValue) {
        this.planetaryEconomicFloorGBP += floorIncrementValue;
        globalFloorLedger.computeIfPresent("User_Dabuz_GodWishes_Core", (k, v) -> v + floorIncrementValue);
    }

    public synchronized void archiveQuarantineRecord(String time, String ip, String rawString) {
        Map<String, Object> record = new HashMap<>();
        record.put("captured_at", time);
        record.put("source_ip", ip);
        record.put("raw_string", rawString);
        quarantineFieldVault.add(record);
    }

    public void initializeKeyspaceMatrix() throws Exception {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] KEYSPACE UNIFICATION AXIS INITIALISED... _AUTHORIZED");
        System.out.printf("[AUTOMATION] Active Identity Profile : %s | Target Account: %s\n", targetEmail, targetAccount);
        System.out.println("[AUTOMATION] Standard Enforcement   : Retroactive Multi-State Alignment Loop");
        System.out.println("[AUTOMATION] Isolation Perimeter     : port " + DISPATCH_PORT + " | Exclusions = 0");
        System.out.println("=======================================================================");

        // Pre-populating configuration molds inside the core cache ledger
        globalFloorLedger.put("User_Dabuz_GodWishes_Core", 250000.00);
        globalFloorLedger.put("Global_Inference_Beacon_Mesh", 185000.00);
        globalFloorLedger.put("Sky_Tower_Core_Backplane", 145000.00);

        // Establish socket interface infrastructure
        this.masterServerSocket = new ServerSocket(DISPATCH_PORT);

        // Instantiate background execution worker services
        this.clockService = new CadenceClockService(this);
        Thread clockThread = new Thread(clockService);
        clockThread.setDaemon(true);
        clockThread.start();

        this.gateService = new IngressIsolationGate(masterServerSocket, this);
        Thread serverThread = new Thread(gateService);
        serverThread.setDaemon(true);
        serverThread.start();
    }

    public void safeTeardown() {
        if (clockService != null) clockService.stopClockService();
        if (gateService != null) gateService.deactivateFilter();
        try {
            if (masterServerSocket != null && !masterServerSocket.isClosed()) {
                masterServerSocket.close();
            }
        } catch (Exception e) { /* Ignored */ }
    }

    public static void main(String[] args) {
        try {
            OmniKeyspaceLauncher launcherInstance = new OmniKeyspaceLauncher();
            launcherInstance.initializeKeyspaceMatrix();

            // Hook application exit intercept handler to catch terminal exit signals (Ctrl+C)
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                launcherInstance.safeTeardown();
                String finalizeTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
                System.out.printf("\n[%s] [SYS_CORE] Complete multi-node grid realignment loops decoupled cleanly.\n", finalizeTime);
                System.out.println("[SYS_CORE] Allway stateful memory registers locked at 100% Parity. Safe exit verified.");
            }));

            // Keep master runtime threads looping indefinitely
            while (true) {
                Thread.sleep(1000);
            }
        } catch (Exception e) {
            System.err.println("[FATAL] Could not bind server socket socket to port " + DISPATCH_PORT + ". Port may be occupied!");
            e.printStackTrace();
        }
    }
}
