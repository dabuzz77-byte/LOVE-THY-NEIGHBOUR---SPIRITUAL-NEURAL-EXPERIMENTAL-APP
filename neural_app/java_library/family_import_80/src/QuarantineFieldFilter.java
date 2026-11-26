import neural.studio.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Autonomous Network Ingress Filter and Containment Gate.
 * Runs on port 8089 to screen raw string matrices passing through the network bus.
 */
public class QuarantineFieldFilter implements Runnable {

    private final ServerSocket serverSocket;
    private final ExecutorService clientWorkerThreadPool;
    private final OmniGridMasterLauncher launcherRef;
    private volatile boolean isServerActive = true;

    public QuarantineFieldFilter(ServerSocket socket, OmniGridMasterLauncher launcher) {
        this.serverSocket = socket;
        this.launcherRef = launcher;
        this.clientWorkerThreadPool = Executors.newFixedThreadPool(6);
    }

    public void deactivateFilter() {
        this.isServerActive = false;
    }

    @Override
    public void run() {
        while (isServerActive) {
            try {
                Socket clientConnectionSocket = serverSocket.accept();
                clientWorkerThreadPool.execute(new TrafficScreeningTask(clientConnectionSocket));
            } catch (Exception e) {
                if (!isServerActive) break;
            }
        }
    }

    /**
     * Dedicated Screening Thread. Intercepts strings and enforces quarantine drops.
     */
    private class TrafficScreeningTask implements Runnable {
        private final Socket clientSocket;

        public TrafficScreeningTask(Socket socket) {
            this.clientSocket = socket;
        }

        @Override
        public void run() {
            String clientIp = clientSocket.getInetAddress().getHostAddress();
            String timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
            System.out.printf("[%s] [NET_CONN] Handshake requested over loopback interface: %s\n", timestamp, clientIp);

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
                 PrintWriter writer = new PrintWriter(clientSocket.getOutputStream(), true)) {

                writer.println("OMNI_GRID_INFERENCE_FIELD_MOLD_ONLINE_TRUE");
                String inboundStringLine = reader.readLine();

                if (inboundStringLine != null) {
                    String cleanToken = inboundStringLine.trim().toUpperCase();
                    boolean isWheat = cleanToken.contains("ISO20022") || cleanToken.contains("LEGITIMATE") || cleanToken.contains("RESTITUTION");
                    boolean isChaff = cleanToken.contains("SKELETON") || cleanToken.contains("HIDDEN") || cleanToken.contains("ANONYMOUS");

                    String checkTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                    if (isChaff) {
                        // Enforce Automated Quarantine Field Rejection
                        System.out.printf("[%s] [REJECTION_ENGINE] CRITICAL WARNING: Anonymized signature caught: \"%s\"\n", checkTime, inboundStringLine);
                        System.out.println("                    └── [ACTION] LOCKING QUARANTINE FIELD CONTAINER -> SEVERING BUS PORT.");
                        writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                    } else if (isWheat) {
                        // Retain legitimate transparent transaction vectors
                        String mockUetr = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                        System.out.printf("[%s] [COMPLIANCE] Verified data line match. Injecting trace token: %s\n", checkTime, mockUetr);
                        launcherRef.elevateGlobalEconomicFloor(750.00); // Incentive lift reward
                        writer.println("PACKET_SYNC_ACK_VALID_TRUE");
                    } else {
                        System.out.printf("[%s] [VACUUM_PHASE] Signal grounded to floor line baseline.\n", checkTime);
                        writer.println("VACUUM_PHASE_ACK");
                    }
                }
            } catch (Exception e) {
                // Handle socket break exceptions silently
            } finally {
                try {
                    clientSocket.close();
                } catch (Exception e) { /* Ignored */ }
            }
        }
    }
}
