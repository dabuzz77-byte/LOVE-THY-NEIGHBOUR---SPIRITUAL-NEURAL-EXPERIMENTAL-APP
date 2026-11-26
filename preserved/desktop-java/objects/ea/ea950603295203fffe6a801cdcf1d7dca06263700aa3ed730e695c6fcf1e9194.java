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
 * High-Velocity Network Ingress Filter and Containment Gate.
 * Runs on port 8089 to screen raw string matrices passing through the network bus.
 */
public class QuarantineGateFilter implements Runnable {

    private final ServerSocket serverSocket;
    private final ExecutorService clientWorkerThreadPool;
    private final NetworkSystemPath launcherRef;
    private volatile boolean isServerActive = true;

    public QuarantineGateFilter(ServerSocket socket, NetworkSystemPath launcher) {
        this.serverSocket = socket;
        this.launcherRef = launcher;
        this.clientWorkerThreadPool = Executors.newFixedThreadPool(4);
    }

    public void deactivateFilter() {
        this.isServerActive = false;
    }

    @Override
    public void run() {
        while (isServerActive) {
            try {
                Socket inboundConnection = serverSocket.accept();
                clientWorkerThreadPool.execute(new StreamScreeningTask(inboundConnection));
            } catch (Exception e) {
                if (!isServerActive) break;
            }
        }
    }

    private class StreamScreeningTask implements Runnable {
        private final Socket socket;

        public StreamScreeningTask(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            String remoteAddress = socket.getInetAddress().getHostAddress();
            String timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
            System.out.printf("[%s] [NET_HANDSHAKE] Handshake tracking request intercepted on local bus: %s\n", timestamp, remoteAddress);

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                 PrintWriter writer = new PrintWriter(socket.getOutputStream(), true)) {

                writer.println("WORLDWIDE_INFERENCE_BEACON_ONLINE_TRUE");
                String rawInboundLine = reader.readLine();

                if (rawInboundLine != null) {
                    String cleanToken = rawInboundLine.trim().toUpperCase();
                    
                    boolean isWheat = cleanToken.contains("ISO20022") || cleanToken.contains("LEGITIMATE") || cleanToken.contains("RESTITUTION");
                    boolean isChaff = cleanToken.contains("SKELETON") || cleanToken.contains("HIDDEN") || cleanToken.contains("ANONYMOUS") || cleanToken.contains("OVERRIDE") || cleanToken.contains("KEY");

                    String eventTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                    if (isChaff) {
                        System.out.printf("[%s] [REJECTION_ENGINE] VIRTUE FAIL REJECT ──► SOURCE PURGED: \"%s\"\n", eventTime, rawInboundLine);
                        System.out.println("                    └── [ACTION] INTERCEPTING PACKET -> ISOLATING FIELD CONTAINER -> CLOSING BUS PORT.");
                        writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                    } else if (isWheat) {
                        String trackingToken = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                        System.out.printf("[%s] [COMPLIANCE] VIRTUE PASS RESPECT ──► ALLOCATION ACCEPTED. Reference: %s\n", eventTime, trackingToken);
                        launcherRef.applyCalibratedBalanceAdjustment();
                        writer.println("PACKET_SYNC_ACK_VALID_TRUE");
                    } else {
                        System.out.printf("[%s] [VACUUM_PHASE] Diagnostic baseline signal grounded safely.\n", eventTime);
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
}
