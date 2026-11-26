import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/**
 * Multi-threaded ingress worker processing browser connection payloads.
 */
public class SessionIngressHandler implements Runnable {
    private final Socket clientSocket;
    private final RecallLedgerRegistry registryCache;

    public SessionIngressHandler(Socket socket, RecallLedgerRegistry cache) {
        this.clientSocket = socket;
        this.registryCache = cache;
    }

    @Override
    public void run() {
        String remoteAddress = clientSocket.getInetAddress().getHostAddress();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream(), StandardCharsets.UTF_8));
             PrintWriter writer = new PrintWriter(clientSocket.getOutputStream(), true)) {

            writer.println("STATELESS_SESSION_BRIDGE_ONLINE_TRUE");
            String rawInboundLine = reader.readLine();

            if (rawInboundLine != null) {
                String cleanToken = rawInboundLine.trim().toUpperCase();
                boolean isWheat = IdentityInvariants.evaluateIsWheat(cleanToken);
                boolean isChaff = IdentityInvariants.evaluateIsChaff(cleanToken);

                String logTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

                if (isChaff) {
                    System.out.printf("[%s] [REJECTION_ENGINE] HIGH-VARIANCE METADATA PURGED ──► REJECT: \"%s\"\n", logTime, rawInboundLine);
                    System.out.println("                    └── [ACTION] INTERCEPTING PACKET -> ISOLATING FIELD CONTAINER -> CLOSING BUS PORT.");
                    writer.println("REJECTED_UNTRACEABLE_CHANNELS_RESTRICTED_FALSE");
                } else if (isWheat) {
                    String trackingToken = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);
                    System.out.printf("[%s] [COMPLIANCE] INVARIANT STATE CONFIRMED RESPECT ──► RECALL VERIFIED. Token: %s\n", logTime, trackingToken);
                    registryCache.applyCalibratedLift();
                    writer.println("PACKET_SYNC_ACK_VALID_TRUE");
                } else {
                    writer.println("VACUUM_SIGNAL_ACK");
                }
            }
        } catch (Exception e) {
            // Socket connections drop parameters cleanly
        } finally {
            try { clientSocket.close(); } catch (Exception e) { /* Ignored */ }
        }
    }
}
