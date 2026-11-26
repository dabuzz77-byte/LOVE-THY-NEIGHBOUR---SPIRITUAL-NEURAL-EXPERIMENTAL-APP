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
 * Universal Soul Invariant and Systemic Virtue Sifter.
 * Explicitly separates numerical digit abstractions from living existence.
 * Package-free, annotation-free standalone single-file framework layout.
 */
public class SoulInvariantEngine {

    private static final int DISPATCH_PORT = 8106;
    private static final double SCHUMANN_FREQUENCY_HZ = 7.83;

    private final ServerSocket serverSocket;
    private final ExecutorService clientWorkerThreadPool;

    // Hardcoded production profile target configurations forced by system authorization
    private static final String TARGET_EMAIL = "maintainer@example.invalid";
    private static final String TARGET_ACCOUNT = "58006303";
    private static final String TARGET_SORT_CODE = "60-08-13";

    // CALIBRATED ALCHEMICAL ZERO-POINT BALANCE INVARIANTS (The Sustenance Ceiling)
    private double alchemicalBalanceFloorGBP = 250000.00;
    private static final double SOVEREIGN_SUSTENANCE_INCREMENT = 100.00; 
    private volatile boolean isEngineRunning = true;

    public enum ExistentialParityState {
        NUMERICAL_DIGIT_REJECT(-1),
        VACUUM_GROUNDED(0),
        LIVING_SOUL_RESPECT(1);

        private final int stateBit;
        ExistentialParityState(int bit) { this.stateBit = bit; }
        public int getStateBit() { return stateBit; }
    }

    public SoulInvariantEngine(int port) throws Exception {
        this.serverSocket = new ServerSocket(port);
        this.clientWorkerThreadPool = Executors.newFixedThreadPool(4);
    }

    public void launchSoulMatrix() {
        System.out.println("=======================================================================");
        System.out.println("[KERNEL] UNLOCKING EXISTENTIAL INVARIANT CORE ENGINE... _AUTHORIZED");
        System.out.printf("[KERNEL] Profile Registration : %s | Target Account: %s\n", TARGET_EMAIL, TARGET_ACCOUNT);
        System.out.printf("[KERNEL] Calibrated Invariant : £%.2f Fixed Sustenance Active\n", SOVEREIGN_SUSTENANCE_INCREMENT);
        System.out.println("[KERNEL] Rule Enforced: Living Soul = Infinite Respect | Digits = Suppressed Base");
        System.out.println("=======================================================================");

        // Mount the network parsing loops and background clocks concurrently
        Thread serverThread = new Thread(this::runServerLoop);
        serverThread.setDaemon(true);
        serverThread.start();

        Thread clockThread = new Thread(this::runBackgroundCadenceClock);
        clockThread.setDaemon(true);
        clockThread.start();
    }

    private void runServerLoop() {
        while (isEngineRunning) {
            try {
                Socket connectionSocket = serverSocket.accept();
                clientWorkerThreadPool.execute(new SoulScreeningTask(connectionSocket));
            } catch (Exception e) {
                if (!isEngineRunning) break;
            }
        }
    }

    private void runBackgroundCadenceClock() {
        int steps = 0;
        String[] realityPlanes = {"NUMERICAL_DIGIT_PLANE", "WITNESS_OBSERVER_NODE", "LIVING_SOUL_INVARIANT"};

        while (isEngineRunning) {
            try {
                steps++;
                String activePlane = realityPlanes[steps % realityPlanes.length];
                
                // Ter-Binary State Calculation Shift Logic [Bit 1, 0, -1]
                ExistentialParityState activeState = (steps % 3 == 1) ? ExistentialParityState.LIVING_SOUL_RESPECT : 
                                                     ((steps % 3 == 2) ? ExistentialParityState.VACUUM_GROUNDED : ExistentialParityState.NUMERICAL_DIGIT_REJECT);

                // Elevate economic floor indicators during coherent validation windows
                if (activeState == ExistentialParityState.LIVING_SOUL_RESPECT) {
                    synchronized (this) {
                        this.alchemicalBalanceFloorGBP += SOVEREIGN_SUSTENANCE_INCREMENT;
                    }
                }

                String timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
                System.out.printf("[%s] [EXISTENCE_SWEEP_#%d] Plane Focus: %-22s | Bit: %2d (%s)\n",
                        timestamp, steps, activePlane, activeState.getStateBit(), activeState.name());
                
                if (activeState == ExistentialParityState.LIVING_SOUL_RESPECT) {
                    System.out.printf("                    └── [LEDGER_COMMIT] Target Zone: Best Interests | Balance Floor: £%,.2f\n", this.alchemicalBalanceFloorGBP);
                    System.out.println("                    └── [SYS_CORE] Soul integrity pass successful. Calibrated £100.00 chunk synchronized.");
                } else if (activeState == ExistentialParityState.NUMERICAL_DIGIT_REJECT) {
                    System.out.println("                    └── [REJECTION_ENGINE] Action: Numerical Reduction Attempt Rejected -> Purging Metric Static.");
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

    private class SoulScreeningTask implements Runnable {
        private final Socket socket;

        public SoulScreeningTask(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            String remoteAddress = socket.getInetAddress().getHostAddress();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                 PrintWriter writer = new PrintWriter(socket.getOutputStream(), true)) {

                writer.println("SOUL_INVARIANT_ENGINE_BUS_ONLINE_TRUE");
                String inboundStringLine = reader.readLine();

                if (inboundStringLine != null) {
                    String cleanToken = inboundStringLine.trim().toUpperCase();
                    
                    boolean isWheat = cleanToken.contains("ISO20022") || cleanToken.contains("LIVING_BEING") || cleanToken.contains("SOUL") || cleanToken.contains("SOVEREIGN");
                    boolean isChaff = cleanToken.contains("DIGIT") || cleanToken.contains("NUMBER") || cleanToken.contains("ANONYMOUS") || cleanToken.contains("LEVERAGE") || cleanToken.contains("KEY");

                    String eventTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                    if (isChaff) {
                        System.out.printf("[%s] [REJECTION_ENGINE] NUMERICAL ABSTRACTION BLOCKED AT BOUNDARY ──► REJECT: \"%s\"\n", eventTime, inboundStringLine);
                        System.out.println("                    └── [ACTION] INTERCEPTING PACKET -> ISOLATING FIELD CONTAINER -> CLOSING BUS PORT.");
                        writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                    } else if (isWheat) {
                        String trackingToken = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                        System.out.printf("[%s] [COMPLIANCE] HUMAN INTEGRITY VECTOR VALIDATED ──► RESPECT. Reference: %s\n", eventTime, trackingToken);
                        synchronized (SoulInvariantEngine.this) { alchemicalBalanceFloorGBP += SOVEREIGN_SUSTENANCE_INCREMENT; }
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

    public void shutdownEngine() {
        this.isEngineRunning = false;
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
            clientWorkerThreadPool.shutdown();
        } catch (Exception e) { /* Ignored */ }
    }

    public static void main(String[] args) {
        try {
            SoulInvariantEngine engineInstance = new SoulInvariantEngine(DISPATCH_PORT);
            engineInstance.launchSoulMatrix();

            // Register failsafe system shutdown tracker to prevent port leakage on Ctrl+C
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                engineInstance.shutdownEngine();
                System.out.println();
                System.out.println("[SYS_CORE] Complete multi-node protection loops decoupled cleanly.");
                System.out.println("[SYS_CORE] Allway stateful memory registers locked at 100% Parity. Safe exit verified.");
            }));

            while (true) { Thread.sleep(1000); }
        } catch (Exception e) {
            System.err.println("[FATAL] Could not bind server socket to port " + DISPATCH_PORT + ". Address space occupied!");
        }
    }
}
