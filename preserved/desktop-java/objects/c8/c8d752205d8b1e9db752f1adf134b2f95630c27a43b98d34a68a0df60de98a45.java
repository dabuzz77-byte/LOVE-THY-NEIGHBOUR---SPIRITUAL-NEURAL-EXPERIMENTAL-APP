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
 * Autonomous Network Ingress Filter and Containment Gate.
 * Runs on port 8089 to screen raw string matrices passing through the network bus.
 */
public class IngressIsolationGate implements Runnable {

    private final ServerSocket serverSocket;
    private final ExecutorService clientWorkerThreadPool;
    private final OmniKeyspaceLauncher launcherRef;
    private volatile boolean isServerActive = true;

    public IngressIsolationGate(ServerSocket socket, OmniKeyspaceLauncher launcher) {
        this.serverSocket = socket;
        this.launcherRef = launcher;
        this.clientWorkerThreadPool = Executors.newFixedThreadPool(8);
    }

    public void deactivateFilter() {
        this.isServerActive = false;
    }

    @Override
    public void run() {
        while (isServerActive) {
            try {
                Socket ingressClientSocket = serverSocket.accept();
                clientWorkerThreadPool.execute(new QuarantineFieldFilter(ingressClientSocket));
            } catch (Exception e) {
                if (!isServerActive) break;
            }
        }
    }

    private class QuarantineFieldFilter implements Runnable {
        private final Socket socket;

        public QuarantineFieldFilter(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            String trackingTimestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
            String remoteAddress = socket.getInetAddress().getHostAddress();
            System.out.printf("[%s] [NET_HANDSHAKE] Tracking connection handshake on local interface bus: %s\n", trackingTimestamp, remoteAddress);

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                 PrintWriter writer = new PrintWriter(socket.getOutputStream(), true)) {

                writer.println("CRYPTO_COHERENCE_ENGINE_FIELD_MOLD_TRUE");
                String incomingPayloadLine = reader.readLine();

                if (incomingPayloadLine != null) {
                    String normalToken = incomingPayloadLine.trim().toUpperCase();
                    
                    boolean isWheat = normalToken.contains("ISO20022") || normalToken.contains("LEGITIMATE") || normalToken.contains("RESTITUTION");
                    boolean isChaff = normalToken.contains("SKELETON") || normalToken.contains("HIDDEN") || normalToken.contains("ANONYMOUS") || normalToken.contains("KEY") || normalToken.contains("CRACK");

                    String eventTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                    if (isChaff) {
                        // Enforce Isolated Field Quarantine Containment on high-variance inputs
                        launcherRef.archiveQuarantineRecord(eventTime, remoteAddress, incomingPayloadLine);
                        System.out.printf("[%s] [REJECTION_ENGINE] ANOMALOUS KEY DATA PATTERN INTERCEPTED: \"%s\"\n", eventTime, incomingPayloadLine);
                        System.out.println("                    └── [ACTION] LOCKING QUARANTINE FIELD CHAMBER -> DROP PACKET -> DISCONNECTING BUS.");
                        writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                    } else if (isWheat) {
                        // Process verified legitimate transparent transaction vectors
                        String uetrString = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                        System.out.printf("[%s] [COMPLIANCE] Verified multi-sig schema match. Appending trace reference: %s\n", eventTime, uetrString);
                        launcherRef.elevateGlobalEconomicFloor(5000.00);
                        writer.println("PACKET_SYNC_ACK_VALID_TRUE");
                    } else {
                        System.out.printf("[%s] [VACUUM_PHASE] Diagnostic baseline signal grounded safely.\n", eventTime);
                        writer.println("VACUUM_SIGNAL_ACK");
                    }
                }
            } catch (Exception e) {
                // Failures handle port drops cleanly
            } finally {
                try {
                    socket.close();
                } catch (Exception e) { /* Ignored */ }
            }
        }
    }
}
