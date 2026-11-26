import java.nio.charset.StandardCharsets;
import java.util.Objects;

/** A JSON message; the signature label and telemetry are not cryptographically signed or encrypted here. */
public record DispatchPayload(long session, String signature, String telemetry) {
    public DispatchPayload {
        Objects.requireNonNull(signature); Objects.requireNonNull(telemetry);
        if (session < 0) throw new IllegalArgumentException("Session must be a non-negative whole number.");
        if (signature.isBlank() || signature.length() > 1024) throw new IllegalArgumentException("Signature label must contain 1–1024 characters.");
        if (telemetry.length() > 32768) throw new IllegalArgumentException("Telemetry is limited to 32,768 characters.");
    }
    public String json() {
        return "{\n  \"session_height\": " + session + ",\n  \"prime_signature\": " + quote(signature)
                + ",\n  \"telemetry\": " + quote(telemetry) + ",\n  \"directive\": \"PLANETARY_PARITY_SYNC\"\n}";
    }
    public byte[] bytes() {
        byte[] result = json().getBytes(StandardCharsets.UTF_8);
        if (result.length > 65536) throw new IllegalArgumentException("Encoded JSON exceeds the 64 KiB request limit.");
        return result;
    }
    public static String quote(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toCharArray()) {
            switch (c) {
                case '"' -> out.append("\\\""); case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n"); case '\r' -> out.append("\\r"); case '\t' -> out.append("\\t");
                default -> { if (c < 32 || Character.isSurrogate(c)) out.append(String.format("\\u%04x", (int)c)); else out.append(c); }
            }
        }
        return out.append('"').toString();
    }
}
