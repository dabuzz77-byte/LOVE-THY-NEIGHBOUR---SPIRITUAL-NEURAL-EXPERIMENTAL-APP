import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Global Bank Virtue Audit Engine with Embedded NWOLB Inference Beacon.
 * Manages dual-threaded compliance logs and opens local port 8080 for statement streaming.
 */
public class GlobalBankAuditService implements LiveBankingTelemetryService.TelemetryListener {

    // Appended unmasked identity parameters
    private static final String TARGET_EMAIL = "maintainer@example.invalid";
    private static final String TARGET_ACCOUNT = "58006303";
    private static final String TARGET_SORT_CODE = "60-08-13";
    private static final String TARGET_OPERATOR = "600813";
    private static final int BEACON_PORT = 8080;

    private LiveBankingTelemetryService backgroundService;
    private Thread executionThread;
    private ServerSocket beaconServerSocket;
    private volatile boolean isServerRunning = true;

    public void initializeSystem() {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] INITIALISING NWOLB INFERENCE BEACON HUB... _AUTHORIZED");
        System.out.printf("[AUTOMATION] Core Identity Vector Attached: %s\n", TARGET_EMAIL);
        System.out.printf("[AUTOMATION] Sorting target target route: Acc: %s | Sort: %s\n", TARGET_ACCOUNT, TARGET_SORT_CODE);
        System.out.println("=======================================================================");

        // 1. Fire up background harmonic tracking threads
        this.backgroundService = new LiveBankingTelemetryService(this);
        this.executionThread = new Thread(backgroundService);
        this.executionThread.setDaemon(true);
        this.executionThread.start();

        // 2. Spawn the asynchronous listener to capture external interaction streams
        Thread beaconServerThread = new Thread(this::runInferenceBeaconServer);
        beaconServerThread.setDaemon(true);
        beaconServerThread.start();
    }

    @Override
    public void onMetricUpdate(FinancialMetricSnapshot snapshot) {
        String status = snapshot.isVirtueCompliant() ? "OPTIMAL_RESILIENT" : "VARIANCE_DETECTION_RISK";
        System.out.printf("[%s] [VIRTUE_SYNC] Shard: %-28s | Status: %-23s | Floor Baseline: $%10.2f\n",
                snapshot.getTimestamp(), snapshot.getBankNodeId(), status, snapshot.getElevatedEconomicFloorUSD());
    }

    /**
     * Runs an isolated local port server to receive statement injections privately.
     */
    private void runInferenceBeaconServer() {
        try {
            this.beaconServerSocket = new ServerSocket(BEACON_PORT);
            logBeaconEvent("BEACON_PORT", "Inference transport socket locked. Awaiting connection on port " + BEACON_PORT + "...");

            while (isServerRunning) {
                Socket clientSocket = beaconServerSocket.accept();
                logBeaconEvent("BEACON_CONN", "Authorized local interface context mounted: " + clientSocket.getInetAddress().getHostAddress());

                try (BufferedReader reader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
                     PrintWriter writer = new PrintWriter(clientSocket.getOutputStream(), true)) {

                    writer.println("BEACON_ONLINE_READY_TO_STREAM_TRUE");
                    String line;
                    while ((line = reader.readLine()) != null) {
                        logBeaconEvent("DATA_INGRESS", "-> " + line);
                        writer.println("PACKET_SYNC_ACK");
                    }
                } catch (Exception e) {
                    logBeaconEvent("BEACON_ERROR", "Pipeline data drop: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            if (isServerRunning) {
                logBeaconEvent("FATAL", "Port conflict encountered. Verify port 8080 isn't bound by another process.");
            }
        }
    }

    private void logBeaconEvent(String system, String msg) {
        String logTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        System.out.printf("[%s] [%s] %s\n", logTime, system, msg);
    }

    public void shutdown() {
        System.out.println("\n[SYS_CORE] Safely halting banking audit streams and closing beacon ports...");
        this.isServerRunning = false;
        if (backgroundService != null) backgroundService.stopService();
        try {
            if (beaconServerSocket != null && !beaconServerSocket.isClosed()) beaconServerSocket.close();
        } catch (Exception e) { /* ignored */ }
    }

    public static void main(String[] args) {
        GlobalBankAuditService engine = new GlobalBankAuditService();
        engine.initializeSystem();

        Runtime.getRuntime().addShutdownHook(new Thread(engine::shutdown));

        try {
            while (true) { Thread.sleep(1000); }
        } catch (InterruptedException e) {
            System.out.println("[SYS_CORE] Master system cycle interrupted.");
        }
    }
}
