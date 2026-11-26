import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Real HTTP endpoints bound only to loopback. Responses are test scenarios, not remote acknowledgements. */
public final class LocalTestServer implements AutoCloseable {
    private final HttpServer server;
    private final ExecutorService workers = Executors.newFixedThreadPool(4, GridEngine.daemonFactory("resonance-local-test"));
    public final AtomicInteger requests = new AtomicInteger(), active = new AtomicInteger(), peak = new AtomicInteger();
    public volatile String lastBody = "";
    public LocalTestServer() throws IOException {
        server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
        server.setExecutor(workers); server.createContext("/", this::handle); server.start();
    }
    public Endpoint endpoint(String name, String path) {
        try { return new Endpoint(java.util.UUID.randomUUID(), name, new URI("http", null,
                server.getAddress().getAddress().getHostAddress(), server.getAddress().getPort(), path, null, null)); }
        catch (URISyntaxException impossible) { throw new IllegalStateException(impossible); }
    }
    public List<Endpoint> endpoints() {
        return List.of(endpoint("Local · healthy", "/sync"), endpoint("Local · delayed", "/delayed"), endpoint("Local · rejection", "/reject"));
    }
    private void handle(HttpExchange exchange) throws IOException {
        int inFlight = active.incrementAndGet(); peak.accumulateAndGet(inFlight, Math::max);
        try (exchange) {
            if (!exchange.getRequestMethod().equals("POST")) { exchange.sendResponseHeaders(405, -1); return; }
            byte[] body = exchange.getRequestBody().readNBytes(65537);
            if (body.length > 65536) { exchange.sendResponseHeaders(413, -1); return; }
            lastBody = new String(body, StandardCharsets.UTF_8); requests.incrementAndGet();
            String path = exchange.getRequestURI().getPath();
            if (path.equals("/delayed")) sleep(650);
            if (path.equals("/timeout")) sleep(3000);
            if (path.equals("/slow-body")) {
                exchange.sendResponseHeaders(200, 100); exchange.getResponseBody().write('x'); exchange.getResponseBody().flush();
                sleep(3000); return;
            }
            int code = path.equals("/reject") ? 503 : path.equals("/delayed") ? 202 : path.equals("/redirect") ? 307
                    : path.equals("/created") ? 201 : path.equals("/no-content") ? 204 : 200;
            if (code == 204) { exchange.sendResponseHeaders(204, -1); return; }
            if (code == 307) exchange.getResponseHeaders().set("Location", "/sync");
            byte[] response = ("{\"mode\":\"local_test\",\"received_bytes\":" + body.length + ",\"status\":" + code + "}").getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(code, response.length); exchange.getResponseBody().write(response);
        } finally { active.decrementAndGet(); }
    }
    private static void sleep(long millis) { try { Thread.sleep(millis); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }
    @Override public void close() { server.stop(0); workers.shutdownNow(); }
}
