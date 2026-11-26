import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
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
    private final OmniCoherenceLauncher launcherRef;
    private volatile boolean isServerActive = true;

    public IngressIsolationGate(ServerSocket socket, OmniCoherenceLauncher launcher) {
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
                Socket ingressClientSocket = serverSocket.accept();
                clientWorkerThreadPool.execute(new FilterTask(ingressClientSocket));
            } catch (Exception e) {
                if (!isServerActive) break;
            }
        }
    }

    private class FilterTask implements Runnable {
        private final Socket socket;

        public FilterTask(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                 PrintWriter writer = new PrintWriter(socket.getOutputStream(), true)) {

                writer.println("OMNI_COHERENCE_NET_BUS_ONLINE_TRUE");
                String incomingPayloadLine = reader.readLine();

                if (incomingPayloadLine != null) {
                    String normToken = incomingPayloadLine.trim().toLowerCase();
                    boolean isWheat = SifterRegistryMatrix.checkIsWheat(normToken);
                    boolean isChaff = SifterRegistryMatrix.checkIsChaff(normToken);

                    String trackId = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 8);

                    if (isChaff) {
                        DataTelemetryRecord errorRecord = new DataTelemetryRecord(trackId, "EXTERNAL_INGRESS", -1, "VIRTUE_FAIL_REJECT", launcherRef.getAlchemicalBalanceFloorGBP());
                        launcherRef.pushTelemetryToDashboard(errorRecord);
                        writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                    } else if (isWheat) {
                        launcherRef.elevateGlobalEconomicFloor(100.00);
                        DataTelemetryRecord successRecord = new DataTelemetryRecord(trackId, "EXTERNAL_INGRESS", 1, "VIRTUE_PASS_RESPECT", launcherRef.getAlchemicalBalanceFloorGBP());
                        launcherRef.pushTelemetryToDashboard(successRecord);
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
}
