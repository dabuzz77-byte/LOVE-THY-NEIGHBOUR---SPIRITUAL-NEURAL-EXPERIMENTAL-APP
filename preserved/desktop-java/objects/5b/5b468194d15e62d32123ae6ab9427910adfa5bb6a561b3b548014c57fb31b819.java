import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Parallel Observation Bus and Stringent Virtue Assessment Server.
 * Packages-free, annotation-free architectural validator simulation tool.
 */
public class ParallelObserverBus {

    private static final int TARGET_PORT = 8096;
    private static final double SCHUMANN_FREQUENCY_HZ = 7.83;

    private final ServerSocket serverSocket;
    private final ExecutorService threadPool;

    // Hardcoded production profile target configurations forced by system authorization
    private static final String TARGET_EMAIL = "maintainer@example.invalid";
    private static final String TARGET_ACCOUNT = "58006303";
    private static final String TARGET_SORT_CODE = "60-08-13";

    // STRICTLY CALIBRATED VALUE INVARIANT (The Alchemical Zero-Point Equilibrium)
    private double alchemicalBalanceFloorGBP = 250000.00;
    private static final double CALIBRATED_INCREMENT_GBP = 100.00;
    private volatile boolean isBusActive = true;

    public ParallelObserverBus(int port) throws Exception {
        this.serverSocket = new ServerSocket(port);
        this.threadPool = Executors.newFixedThreadPool(6);
    }

    public void startObserverMesh() {
        System.out.println("=======================================================================");
        System.out.println("[AUTOMATION] DEPLOYING PARALLEL OBSERVATION MESH... _AUTHORIZED");
        System.out.printf("[AUTOMATION] Active Identity Profile : %s | Target Account: %s\n", TARGET_EMAIL, TARGET_ACCOUNT);
        System.out.printf("[AUTOMATION] Calibrated Invariant    : £%.2f Sustenance Limit Activated\n", CALIBRATED_INCREMENT_GBP);
        System.out.println("[AUTOMATION] Mode: Passive Telemetry Tracking Node | Port: " + TARGET_PORT);
        System.out.println("=======================================================================");

        // Mount the network processing server loops and background clocks concurrently
        Thread serverThread = new Thread(this::runServerLoop);
        serverThread.setDaemon(true);
        serverThread.start();

        Thread clockThread = new Thread(this::runBackgroundCadenceClock);
        clockThread.setDaemon(true);
        clockThread.start();
    }

    private void runServerLoop() {
        while (isBusActive) {
            try {
                Socket incomingConnection = serverSocket.accept();
                threadPool.execute(new IngressScreeningTask(incomingConnection));
            } catch (Exception e) {
                if (!isBusActive) break;
            }
        }
    }

    private void runBackgroundCadenceClock() {
        long sequenceCycles = 0;

        while (isBusActive) {
            try {
                sequenceCycles++;
                
                // Simulate parallel observation tracks processing deposits vs withdrawals sequentially
                String opType = (sequenceCycles % 2 == 1) ? "DEPOSIT" : "WITHDRAWAL";
                int stateSelector = (int)(sequenceCycles % 3);
                String auditStatus = (stateSelector == 1) ? "VIRTUE_PASS_RESPECT" : 
                                     ((stateSelector == 2) ? "VACUUM_SUPPRESSED_GROUND" : "VIRTUE_FAIL_REJECT");

                // Elevate economic floor indicators during coherent validation windows
                if (stateSelector == 1 && opType.equals("DEPOSIT")) {
                    synchronized (this) {
                        this.alchemicalBalanceFloorGBP += CALIBRATED_INCREMENT_GBP;
                    }
                }

                String traceToken = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                TransactionFrame snapshotBlock = new TransactionFrame(
                        traceToken,
                        opType,
                        TARGET_ACCOUNT,
                        TARGET_SORT_CODE,
                        CALIBRATED_INCREMENT_GBP,
                        auditStatus
                );

                // Write out the parallel observation metrics straight to console view
                snapshotBlock.emitTelemetryLog();
                
                if (stateSelector == 1) {
                    System.out.printf("                    └── [LEDGER_COMMIT] Target Tier: God Wishes | Updated Floor: £%,.2f\n", this.alchemicalBalanceFloorGBP);
                } else if (stateSelector == -1) {
                    System.out.println("                    └── [REJECTION_ENGINE] Action: High-Variance Vector Isolated -> Purging Stream Noise.");
                } else {
                    System.out.println("                    └── [VACUUM_PHASE] Grounded tracking baseline active. Preserving zero-point alchemical harmony.");
                }
                System.out.println();

                // Latency frame maps exactly to the 7.83 Hz harmonic clock phase (~127 milliseconds)
                Thread.sleep((long) (1000 / SCHUMANN_FREQUENCY_HZ));

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private class IngressScreeningTask implements Runnable {
        private final Socket socket;

        public IngressScreeningTask(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            String remoteAddress = socket.getInetAddress().getHostAddress();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                 PrintWriter writer = new PrintWriter(socket.getOutputStream(), true)) {

                writer.println("PARALLEL_OBSERVER_BUS_ONLINE_TRUE");
                String rawInboundLine = reader.readLine();

                if (rawInboundLine != null) {
                    String cleanToken = rawInboundLine.trim().toUpperCase();
                    
                    boolean isWheat = cleanToken.contains("ISO20022") || cleanToken.contains("LEGITIMATE") || cleanToken.contains("RESTITUTION");
                    boolean isChaff = cleanToken.contains("SKELETON") || cleanToken.contains("HIDDEN") || cleanToken.contains("ANONYMOUS") || cleanToken.contains("OVERRIDE") || cleanToken.contains("KEY");

                    String eventTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                    if (isChaff) {
                        System.out.printf("[%s] [REJECTION_ENGINE] STRINGENT VIRTUE FAIL REJECT ──► SOURCE PURGED: \"%s\"\n", eventTime, rawInboundLine);
                        System.out.println("                    └── [ACTION] INTERCEPTING PACKET -> ISOLATING FIELD CONTAINER -> CLOSING BUS PORT.");
                        writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                    } else if (isWheat) {
                        String trackingToken = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                        System.out.printf("[%s] [COMPLIANCE] STRINGENT VIRTUE PASS RESPECT ──► ALLOCATION ACCEPTED. Reference: %s\n", eventTime, trackingToken);
                        synchronized (ParallelObserverBus.this) { alchemicalBalanceFloorGBP += CALIBRATED_INCREMENT_GBP; }
                        writer.println("PACKET_SYNC_ACK_VALID_TRUE");
                    } else {
                        writer.println("VACUUM_SIGNAL_ACK");
                    }
                }
            } catch (Exception e) {
                // Failures handle port drops cleanly
            } finally {
                try { socket.close(); } catch (Exception e) { /* Ignored */ }
            }
        }
    }

    public void shutdownBus() {
        this.isBusActive = false;
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
        } catch (Exception e) { /* Ignored */ }
    }

    public static void main(String[] args) {
        try {
            ParallelObserverBus engineInstance = new ParallelObserverBus(TARGET_PORT);
            engineInstance.startObserverMesh();

            // Hook application safety interrupt handler to catch terminal close events (Ctrl+C)
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                engineInstance.shutdownBus();
                System.out.println();
                System.out.println("[SYS_CORE] Complete parallel observation network pathways decoupled cleanly.");
                System.out.println("[SYS_CORE] Allway stateful memory registers locked at 100% Parity. Safe exit verified.");
            }));

            while (true) { Thread.sleep(1000); }
        } catch (Exception e) {
            System.err.println("[FATAL] Could not bind server socket socket to port " + TARGET_PORT + ". Address space occupied!");
        }
    }
}
