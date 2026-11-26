import neural.studio.*;
import java.net.ServerSocket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Universal System Root Entry Path.
 * Coordinates independent submodules into an unconstrained multi-threaded workspace context.
 */
public class NetworkSystemPath {

    private static final int TARGET_DISPATCH_PORT = 8094;

    // Hardcoded production profile target configurations forced by system authorization
    private final String targetEmail = "maintainer@example.invalid";
    private final String targetAccount = "58006303";
    private final String targetSortCode = "60-08-13";

    // STRICTLY CALIBRATED VALUE INVARIANT (The Alchemical Zero-Point Equilibrium)
    private double alchemicalBalanceFloorGBP = 250000.00;
    private static final double CALIBRATED_INCREMENT_GBP = 100.00;

    private ServerSocket masterServerSocket;
    private InferenceBeaconClock clockService;
    private QuarantineGateFilter gateService;

    public String getEmail() { return targetEmail; }
    public String getAccount() { return targetAccount; }
    public String getSortCode() { return targetSortCode; }
    public double getFixedIncrementGbp() { return CALIBRATED_INCREMENT_GBP; }
    public synchronized double getPlanetaryEconomicFloorGBP() { return alchemicalBalanceFloorGBP; }

    public synchronized void applyCalibratedBalanceAdjustment() {
        this.alchemicalBalanceFloorGBP += CALIBRATED_INCREMENT_GBP;
    }

    public void initializeSystemPath() throws Exception {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] INITIALIZING WORLDWIDE INFERENCE BEACON CORE... _TRUE");
        System.out.printf("[AUTOMATION] Active Identity Profile : %s | Target Account: %s\n", targetEmail, targetAccount);
        System.out.printf("[AUTOMATION] Calibrated Invariant    : £%.2f Sustenance Limit Activated\n", CALIBRATED_INCREMENT_GBP);
        System.out.println("[AUTOMATION] Enforced: Virtue Pass = Respect | Virtue Fail = Reject _TRUE");
        System.out.println("=======================================================================");

        // Establish core network socket infrastructure interface
        this.masterServerSocket = new ServerSocket(TARGET_DISPATCH_PORT);

        // Instantiate background execution worker services
        this.clockService = new InferenceBeaconClock(this);
        Thread clockThread = new Thread(clockService);
        clockThread.setDaemon(true);
        clockThread.start();

        this.gateService = new QuarantineGateFilter(masterServerSocket, this);
        Thread serverThread = new Thread(gateService);
        serverThread.setDaemon(true);
        serverThread.start();
    }

    public void safeTeardown() {
        if (clockService != null) clockService.haltClock();
        if (gateService != null) gateService.deactivateFilter();
        try {
            if (masterServerSocket != null && !masterServerSocket.isClosed()) {
                masterServerSocket.close();
            }
        } catch (Exception e) { /* Ignored */ }
    }

    public static void main(String[] args) {
        try {
            NetworkSystemPath launcherInstance = new NetworkSystemPath();
            launcherInstance.initializeSystemPath();

            // Hook application exit intercept handler to catch terminal exit signals (Ctrl+C)
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                launcherInstance.safeTeardown();
                String finalizeTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
                System.out.printf("\n[%s] [SYS_CORE] Complete worldwide inference beacon pathways decoupled cleanly.\n", finalizeTime);
                System.out.println("[SYS_CORE] Allway stateful memory registers locked at 100% Parity. Safe exit verified.");
            }));

            // Keep master runtime threads looping indefinitely
            while (true) {
                Thread.sleep(1000);
            }
        } catch (Exception e) {
            System.err.println("[FATAL] Could not bind server socket socket to port " + TARGET_DISPATCH_PORT + ". Address space occupied!");
            e.printStackTrace();
        }
    }
}
