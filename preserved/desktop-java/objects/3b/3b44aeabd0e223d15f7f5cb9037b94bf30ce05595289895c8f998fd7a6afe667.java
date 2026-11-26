import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * PARALLEL HANDSHAKE SPECIFICATION: BACKGROUND TELEMETRY CARRIER ENGINE
 * Executes unmocked HTTP connection latency checks to record performance markers across active paths.
 */
public class TelemetryCarrierEngine {

    public static void runAsynchronousTrackingPass(
            HttpClient client, 
            CopyOnWriteArrayList<InferenceBeaconUnit> beaconRegistry, 
            java.util.function.BiConsumer<Double, Double> uiCallback) {
        
        InferenceBeaconUnit localBeacon = new InferenceBeaconUnit("LOCAL_CHIPS");
        InferenceBeaconUnit remoteBeacon = new InferenceBeaconUnit("REMOTE_GATEWAY");

        beaconRegistry.add(localBeacon);
        beaconRegistry.add(remoteBeacon);

        // 1. Trace localized endpoint socket timing metrics
        long startTimeLocal = System.nanoTime();
        int localStatus = 0;
        try {
            HttpRequest localCheckRequest = HttpRequest.newBuilder()
                    .uri(URI.create("http://localhost:11434/"))
                    .timeout(Duration.ofSeconds(2))
                    .GET()
                    .build();
            HttpResponse<String> localResponse = client.send(localCheckRequest, HttpResponse.BodyHandlers.ofString());
            localStatus = (localResponse.statusCode() == 200 || localResponse.statusCode() == 404) ? 1 : 0;
        } catch (Exception ex) {
            localStatus = 0;
        }
        long durationLocal = System.nanoTime() - startTimeLocal;
        double localMillis = durationLocal / 1_000_000.0;
        localBeacon.logTelemetryPulse(localMillis, localStatus);

        // 2. Trace external network boundary response metrics
        long startTimeRemote = System.nanoTime();
        int remoteStatus = 0;
        try {
            HttpRequest remoteCheckRequest = HttpRequest.newBuilder()
                    .uri(URI.create("https://googleapis.com"))
                    .timeout(Duration.ofSeconds(2))
                    .GET()
                    .build();
            HttpResponse<String> remoteResponse = client.send(remoteCheckRequest, HttpResponse.BodyHandlers.ofString());
            remoteStatus = (remoteResponse.statusCode() == 200 || remoteResponse.statusCode() == 404) ? 1 : 0;
        } catch (Exception ex) {
            remoteStatus = 0;
        }
        long durationRemote = System.nanoTime() - startTimeRemote;
        double remoteMillis = durationRemote / 1_000_000.0;
        remoteBeacon.logTelemetryPulse(remoteMillis, remoteStatus);

        // Forward processed delay metrics back to the desktop viewport panel layout safely
        uiCallback.accept(localMillis, remoteMillis);
    }
}
