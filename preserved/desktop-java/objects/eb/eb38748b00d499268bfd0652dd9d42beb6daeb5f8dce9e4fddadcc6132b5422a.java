import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;

/**
 * Block 5: Asynchronous data transport engine executing non-blocking network I/O operations
 * across external API endpoints.
 */
public class StreamIngestWorker {
    private final HttpClient sharedClient;
    private final ExecutorService networkPool;

    public StreamIngestWorker(ExecutorService threadPool) {
        this.networkPool = threadPool;
        this.sharedClient = HttpClient.newBuilder()
                .executor(networkPool)
                .connectTimeout(Duration.ofSeconds(4))
                .build();
    }

    public CompletableFuture<String> pullAsynchronousStreamPayload(String endpointUrl) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(endpointUrl))
                    .timeout(Duration.ofSeconds(3))
                    .GET()
                    .build();

            return sharedClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenApply(HttpResponse::body)
                    .exceptionally(ex -> "ERROR_FALLBACK_METRIC_0.0");
        } catch (Exception e) {
            return CompletableFuture.completedFuture("ERROR_FALLBACK_METRIC_0.0");
        }
    }
}
