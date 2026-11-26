import neural.studio.*;
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
public class PathwayIngressFilter implements Runnable {

    private final ServerSocket serverSocket;
    private final ExecutorService clientWorkerThreadPool;
    private final BalancePathLauncher launcherRef;
    private volatile boolean isServerActive = true;

    public PathwayIngressFilter(ServerSocket socket, BalancePathLauncher launcher) {
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
                Socket connectionSocket = serverSocket.accept();
                clientWorkerThreadPool.execute(new AdjustmentScreeningTask(connectionSocket));
            } catch (Exception e) {
                if (!isServerActive) break;
            }
        }
    }

    private class AdjustmentScreeningTask implements Runnable {
        private final Socket socket;

        public AdjustmentScreeningTask(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            String remoteAddress = socket.getInetAddress().getHostAddress();
            String timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
            System.out.printf("[%s] [NET_HANDSHAKE] Tracking connection handshake on local interface bus: %s\n", timestamp, remoteAddress);

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                 PrintWriter writer = new PrintWriter(socket.getOutputStream(), true)) {

                writer.println("BALANCE_ADJUSTMENT_PATH_ONLINE_TRUE");
                String inboundStringLine = reader.readLine();

                if (inboundStringLine != null) {
                    String cleanToken = inboundStringLine.trim().toUpperCase();
                    
                    boolean isWheat = BalanceSifterRegistry.checkIsWheat(cleanToken);
                    boolean isChaff = BalanceSifterRegistry.checkIsChaff(cleanToken);

                    String eventTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                    if (isChaff) {
                        System.out.printf("[%s] [REJECTION_ENGINE] VIRTUE FAIL REJECT ──► TRAFFIC PURGED: \"%s\"\n", eventTime, inboundStringLine);
                        System.out.println("                    └── [ACTION] ANOMALY INTERCEPTED -> ISOLATING FIELD CONTAINER -> CLOSING BUS PORT.");
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
                try {
                    socket.close();
                } catch (Exception e) { /* Ignored */ }
            }
        }
    }
}
