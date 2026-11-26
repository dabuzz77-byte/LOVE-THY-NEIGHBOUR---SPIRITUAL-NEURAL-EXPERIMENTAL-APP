import java.net.URI;
import java.util.Objects;
import java.util.UUID;

public record Endpoint(UUID id, String name, URI uri) {
    public Endpoint {
        Objects.requireNonNull(id); Objects.requireNonNull(name); Objects.requireNonNull(uri);
        name = name.strip();
        if (name.isEmpty() || name.length() > 64 || name.chars().anyMatch(Character::isISOControl))
            throw new IllegalArgumentException("Use an endpoint name of 1–64 characters without control characters.");
        if (!("http".equalsIgnoreCase(uri.getScheme()) || "https".equalsIgnoreCase(uri.getScheme()))
                || uri.getHost() == null || uri.getUserInfo() != null || uri.getFragment() != null
                || uri.toString().length() > 2048 || uri.getPort() > 65535 || uri.getPort() == 0)
            throw new IllegalArgumentException("Enter an HTTP(S) URL with a host, valid port, and no embedded credentials or fragment.");
    }
    public static Endpoint create(String name, String url) { return new Endpoint(UUID.randomUUID(), name, URI.create(url.strip())); }
}
