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
 * High-velocity passive observation server screening loops.
 */
public class PassiveObservationHub implements Runnable {

    private final ServerSocket serverSocket;
    private final ExecutorService threadPool;
    private final CultivationBusLauncher coreLauncher;
    private volatile boolean isHubActive = true;

    public PassiveObservationHub(ServerSocket socket, CultivationBusLauncher launcher) {
        this.serverSocket = socket;
        this.coreLauncher = launcher;
        this.threadPool = Executors.newFixedThreadPool(4);
    }

    public void shutdownHub() {
        this.isHubActive = false;
    }

    @Override
    public void run() {
        while (isHubActive) {
            try {
                Socket inboundSocket = serverSocket.accept();
                threadPool.execute(new ProcessingTask(inboundSocket));
            } catch (Exception e) {
                if (!isHubActive) break;
            }
        }
    }

    private class ProcessingTask implements Runnable {
        private final Socket clientSocket;

        public ProcessingTask(Socket socket) {
            this.clientSocket = socket;
        }

        @Override
        public void run() {
            String remoteIp = clientSocket.getInetAddress().getHostAddress();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream(), StandardCharsets.UTF_8));
                 PrintWriter writer = new PrintWriter(clientSocket.getOutputStream(), true)) {

                writer.println("CULTIVATION_TELEMETRY_BUS_ONLINE_TRUE");
                String rawLine = reader.readLine();

                if (rawLine != null) {
                    String normToken = rawLine.trim().toLowerCase();
                    boolean isWheat = InvariantSifter.verifyIsWheat(normToken);
                    boolean isChaff = InvariantSifter.verifyIsChaff(normToken);

                    String logTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                    if (isChaff) {
                        System.out.printf("[%s] [REJECTION_ENGINE] CORRUPTED TRAFFIC DETECTED ──► REJECT: \"%s\"\n", logTime, rawLine);
                        System.out.println("                    └── [ACTION] INTERCEPTING PACKET -> ISOLATING FIELD CONTAINER -> CLOSING PORT.");
                        writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                    } else if (isWheat) {
                        String traceToken = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                        System.out.printf("[%s] [COMPLIANCE] INVARIANT VALUE COHERENCE ACCREDITED ──► RESPECT. Token: %s\n", logTime, traceToken);
                        coreLauncher.applyCalibratedAdjustment();
                        writer.println("PACKET_SYNC_ACK_VALID_TRUE");
                    } else {
                        writer.println("VACUUM_SIGNAL_ACK");
                    }
                }
            } catch (Exception e) {
                // Failures handle port drops cleanly
            } finally {
                try { clientSocket.close(); } catch (Exception e) { /* Ignored */ }
            }
        }
    }
}
