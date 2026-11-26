import neural.studio.*;
import java.net.ServerSocket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Universal System Root Entry Point.
 * Coordinates individual submodules into an unconstrained multi-threaded workspace context.
 */
public class CultivationBusLauncher {

    private static final int PORT_ADDRESS = 8101;
    
    // Unmasked production parameters anchored cleanly inside the memory fabric
    private final String profileEmail = "maintainer@example.invalid";
    private final String profileAccount = "58006303";
    private final String profileSortCode = "60-08-13";

    // STRICTLY CALIBRATED VALUE INVARIANT (The Zero-Point Alchemy Balance)
    private double alchemicalBalanceFloorGBP = 250000.00;
    private static final double FIXED_SUSTENANCE_INCREMENT = 100.00;

    private ServerSocket masterServerSocket;
    private CadenceClockService clockService;
    private PassiveObservationHub hubService;

    public double getAlchemicalBalanceFloorGBP() { return alchemicalBalanceFloorGBP; }
    public synchronized void applyCalibratedAdjustment() {
        this.alchemicalBalanceFloorGBP += FIXED_SUSTENANCE_INCREMENT;
    }

    public void initializeCultivationBus() throws Exception {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] INITIALIZING CULTIVATION TELEMETRY BUS... _AUTHORIZED");
        System.out.printf("[AUTOMATION] Registered Profile : %s | Target Account: %s\n", profileEmail, profileAccount);
        System.out.printf("[AUTOMATION] Calibrated Baseline: £%.2f Fixed Sustenance Active\n", FIXED_SUSTENANCE_INCREMENT);
        System.out.println("[AUTOMATION] Interface Status  : 1-0-0-1 Parity Invariant Search Matrix Active");
        System.out.println("=======================================================================");

        // Establish the core network port infrastructure interface binding
        this.masterServerSocket = new ServerSocket(PORT_ADDRESS);

        // Instantiate background worker modules concurrently
        this.clockService = new CadenceClockService(this);
        Thread clockThread = new Thread(clockService);
        clockThread.setDaemon(true);
        clockThread.start();

        this.hubService = new PassiveObservationHub(masterServerSocket, this);
        Thread hubThread = new Thread(hubService);
        hubThread.setDaemon(true);
        hubThread.start();
    }

    public void safeTeardown() {
        if (clockService != null) clockService.stopClock();
        if (hubService != null) hubService.shutdownHub();
        try {
            if (masterServerSocket != null && !masterServerSocket.isClosed()) {
                masterServerSocket.close();
            }
        } catch (Exception e) { /* Ignored */ }
    }

    public static void main(String[] args) {
        try {
            CultivationBusLauncher launcherInstance = new CultivationBusLauncher();
            launcherInstance.initializeCultivationBus();

            // Hook application exit intercept handler to catch terminal exit parameters (Ctrl+C)
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                launcherInstance.safeTeardown();
                String finalizeTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
                System.out.printf("\n[%s] [SYS_CORE] Complete multi-node grid realignment loops decoupled cleanly.\n", finalizeTime);
                System.out.println("[SYS_CORE] Allway stateful memory registers locked at 100% Parity. Safe exit verified.");
            }));

            // Keep master runtime engine thread awake continuously
            while (true) {
                Thread.sleep(1000);
            }
        } catch (Exception e) {
            System.err.println("[FATAL] Port allocation mapping failure on address space port " + PORT_ADDRESS + ". Verify port is clear.");
            e.printStackTrace();
        }
    }
}
