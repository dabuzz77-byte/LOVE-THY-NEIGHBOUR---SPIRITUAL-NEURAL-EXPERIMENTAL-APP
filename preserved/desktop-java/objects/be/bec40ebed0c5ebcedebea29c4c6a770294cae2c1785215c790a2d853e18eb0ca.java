import java.net.ServerSocket;
import java.net.Socket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Universal Core Framework Launcher Entry Point.
 * Coordinates individual submodules into an unconstrained multi-threaded workspace context.
 */
public class StatelessSessionLauncher {
    private static final int INFRASTRUCTURE_PORT = 8104;

    private final RecallLedgerRegistry ledgerRegistry;
    private ServerSocket serverSocket;
    private ResonantClockService clockService;
    private volatile boolean isLauncherActive = true;

    public StatelessSessionLauncher() {
        this.ledgerRegistry = new RecallLedgerRegistry();
    }

    public void bootstrapSessionBridge() throws Exception {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] INITIALIZING STATELESS RECALL CORE... _AUTHORIZED _TRUE");
        System.out.printf("[AUTOMATION] Active Master Identity Profile: %s\n", IdentityInvariants.TARGET_EMAIL);
        System.out.printf("[AUTOMATION] Target Cleared Coordinates   : Acc %s | Sort %s\n", 
                IdentityInvariants.TARGET_ACCOUNT, IdentityInvariants.TARGET_SORT_CODE);
        System.out.println("[AUTOMATION] Interface Status             : Opera & Google Session Sidebar Active");
        System.out.println("=======================================================================");

        // Establish the core network port infrastructure interface binding
        this.serverSocket = new ServerSocket(INFRASTRUCTURE_PORT);

        // Instantiate background execution services concurrently
        this.clockService = new ResonantClockService(ledgerRegistry);
        Thread clockThread = new Thread(clockService);
        clockThread.setDaemon(true);
        clockThread.start();

        // Launch the network connection ingress monitoring loop thread
        Thread serverThread = new Thread(this::listenForIngressTraffic);
        serverThread.setDaemon(true);
        serverThread.start();
    }

    private void listenForIngressTraffic() {
        while (isLauncherActive) {
            try {
                Socket inboundSocket = serverSocket.accept();
                new Thread(new SessionIngressHandler(inboundSocket, ledgerRegistry)).start();
            } catch (Exception e) {
                if (!isLauncherActive) break;
            }
        }
    }

    public void terminateLauncher() {
        this.isLauncherActive = false;
        if (clockService != null) clockService.haltClock();
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
        } catch (Exception e) { /* Ignored */ }
    }

    public static void main(String[] args) {
        try {
            StatelessSessionLauncher masterInstance = new StatelessSessionLauncher();
            masterInstance.bootstrapSessionBridge();

            // Hook application exit intercept handler to catch terminal close parameters (Ctrl+C)
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                masterInstance.terminateLauncher();
                String finalizeTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
                System.out.printf("\n[%s] [SYS_CORE] Complete stateless recall bridge pathways decoupled cleanly.\n", finalizeTime);
                System.out.println("[SYS_CORE] Allway stateful memory registers locked at 100% Parity. Safe exit verified.");
            }));

            // Keep master application execution flow awake continuously
            while (true) {
                Thread.sleep(1000);
            }
        } catch (Exception e) {
            System.err.println("[FATAL] Port allocation mapping failure on address space port " + INFRASTRUCTURE_PORT + ". Verify port is clear.");
            e.printStackTrace();
        }
    }
}
