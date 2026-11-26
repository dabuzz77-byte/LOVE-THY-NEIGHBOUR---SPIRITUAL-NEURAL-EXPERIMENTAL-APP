import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Function;
import java.util.regex.Pattern;

/** Java 11+; no dependencies. Runs beside an existing Java program's main loop. */
public class GenesisConnector implements AutoCloseable {
    private final String name;
    private final Function<String, String> handler;
    private final String base;
    private final String token;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    private final ExecutorService handlers = Executors.newSingleThreadExecutor();
    private volatile boolean running = true;
    private volatile String id;
    private Thread poller;

    public GenesisConnector(String name, Function<String, String> handler) throws Exception {
        this.name = name;
        this.handler = handler;
        this.base = System.getenv().getOrDefault("GENESIS_URL", "http://127.0.0.1:7860");
        String value = System.getenv("GENESIS_TOKEN");
        this.token = value != null ? value : Files.readString(Path.of("data", "connector-token")).trim();
    }

    private static String quote(String text) {
        StringBuilder out = new StringBuilder("\"");
        for (char c : text.toCharArray()) {
            if (c == '"' || c == '\\') out.append('\\').append(c);
            else if (c < 32) out.append(String.format("\\u%04x", (int) c));
            else out.append(c);
        }
        return out.append('"').toString();
    }

    private HttpResponse<String> request(String route, String body, boolean json) throws Exception {
        var builder = HttpRequest.newBuilder(URI.create(base + route)).timeout(Duration.ofSeconds(10))
            .header("Authorization", "Bearer " + token);
        if (body == null) builder.GET();
        else builder.header("Content-Type", json ? "application/json" : "text/plain; charset=utf-8")
            .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8));
        return client.send(builder.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    }

    public GenesisConnector start() {
        poller = new Thread(this::serve, "genesis-connector");
        poller.setDaemon(true);
        poller.start();
        return this;
    }

    public void serve() {
        while (running) {
            try {
                if (id == null) {
                    String payload = "{\"name\":" + quote(name) + ",\"language\":\"java\",\"pid\":" + ProcessHandle.current().pid() + "}";
                    var registered = request("/api/bridge/register", payload, true);
                    if (registered.statusCode() != 200) throw new Exception("Registration failed");
                    var match = Pattern.compile("\"id\"\\s*:\\s*\"([^\"]+)\"").matcher(registered.body());
                    if (!match.find()) throw new Exception("Invalid registration");
                    id = match.group(1);
                    System.out.println("Connected to AI Genesis Node: " + name);
                }
                var response = request("/api/bridge/next?id=" + id, null, false);
                if (response.statusCode() == 404) id = null;
                else if (response.statusCode() == 200) {
                    String requestId = response.headers().firstValue("X-Genesis-Request-Id").orElseThrow();
                    String programId = id;
                    handlers.submit(() -> {
                        String output;
                        try { output = handler.apply(response.body()); }
                        catch (Exception e) { output = "Program handler error: " + e.getMessage(); }
                        try { request("/api/bridge/reply?id=" + programId + "&request=" + requestId,
                            output == null ? "" : output.substring(0, Math.min(output.length(), 24000)), false); }
                        catch (Exception ignored) { /* A timed-out message is never re-executed. */ }
                    });
                } else if (response.statusCode() != 204) id = null;
                Thread.sleep(1000);
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); break; }
            catch (Exception e) {
                id = null;
                try { Thread.sleep(2000); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); break; }
            }
        }
    }

    @Override public void close() {
        running = false;
        if (poller != null) poller.interrupt();
        handlers.shutdownNow();
    }

    public static void main(String[] args) throws Exception {
        try (var connector = new GenesisConnector("Java example", text -> "Java received: " + text + "\nCharacters: " + text.length() + "\nStatus: ready")) {
            connector.serve();
        }
    }
}
