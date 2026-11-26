import neural.studio.*;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Configuration contains endpoint addresses and runtime controls, never the draft request payload. */
public record GridConfig(List<Endpoint> endpoints, int timeoutSeconds, int concurrency, int intervalSeconds) {
    public GridConfig {
        endpoints = List.copyOf(endpoints);
        if (endpoints.size() > GridEngine.MAX_ENDPOINTS || timeoutSeconds < 1 || timeoutSeconds > 60
                || concurrency < 1 || concurrency > 8 || intervalSeconds < 5 || intervalSeconds > 300)
            throw new IllegalArgumentException("Invalid configuration limits.");
        Set<UUID> ids = new HashSet<>(); Set<String> urls = new HashSet<>();
        for (Endpoint endpoint : endpoints) if (!ids.add(endpoint.id()) || !urls.add(endpoint.uri().normalize().toString()))
            throw new IllegalArgumentException("Duplicate endpoints in configuration.");
    }
    public void save(Path path) throws IOException {
        Properties p = new Properties(); p.setProperty("version", "1");
        p.setProperty("timeout", "" + timeoutSeconds); p.setProperty("concurrency", "" + concurrency); p.setProperty("interval", "" + intervalSeconds);
        p.setProperty("count", "" + endpoints.size());
        for (int i = 0; i < endpoints.size(); i++) {
            Endpoint endpoint = endpoints.get(i); String key = "endpoint." + i + ".";
            p.setProperty(key + "id", endpoint.id().toString()); p.setProperty(key + "name", endpoint.name()); p.setProperty(key + "url", endpoint.uri().toString());
        }
        Path absolute = path.toAbsolutePath();
        Path temporary = Files.createTempFile(absolute.getParent(), ".resonance-", ".tmp");
        try {
            try (Writer writer = Files.newBufferedWriter(temporary, StandardCharsets.UTF_8)) { p.store(writer, "Planetary Resonance configuration; importing does not dispatch requests"); }
            try { Files.move(temporary, absolute, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
            catch (AtomicMoveNotSupportedException ignored) { Files.move(temporary, absolute, StandardCopyOption.REPLACE_EXISTING); }
        } finally { Files.deleteIfExists(temporary); }
    }
    public static GridConfig load(Path path) throws IOException {
        if (Files.size(path) > 131072) throw new IOException("Configuration exceeds 128 KiB.");
        Properties p = new Properties();
        try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) { p.load(reader); }
        try {
            if (!"1".equals(p.getProperty("version"))) throw new IllegalArgumentException("Unsupported configuration version.");
            int count = Integer.parseInt(p.getProperty("count"));
            if (count < 0 || count > GridEngine.MAX_ENDPOINTS) throw new IllegalArgumentException("Invalid endpoint count.");
            List<Endpoint> endpoints = new ArrayList<>();
            for (int i = 0; i < count; i++) { String key = "endpoint." + i + ".";
                endpoints.add(new Endpoint(UUID.fromString(p.getProperty(key + "id")), p.getProperty(key + "name"), URI.create(p.getProperty(key + "url")))); }
            return new GridConfig(endpoints, Integer.parseInt(p.getProperty("timeout")), Integer.parseInt(p.getProperty("concurrency")), Integer.parseInt(p.getProperty("interval")));
        } catch (RuntimeException failure) { throw new IOException("Invalid configuration: " + failure.getMessage(), failure); }
    }
}
