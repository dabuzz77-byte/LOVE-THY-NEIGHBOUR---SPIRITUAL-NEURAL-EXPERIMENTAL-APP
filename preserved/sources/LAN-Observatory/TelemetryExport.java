import java.time.Instant;
import java.util.Collection;
import java.util.Locale;

public final class TelemetryExport {
    private TelemetryExport() { }
    public static String toCsv(Collection<RemoteDeviceNode> devices) {
        StringBuilder csv = new StringBuilder("device_id,platform,ip_address,status,entropy_bits,salience,messages,last_seen_utc,last_telemetry_utc\r\n");
        long now = System.currentTimeMillis();
        for (RemoteDeviceNode node : devices) {
            csv.append(cell(node.deviceId)).append(',').append(cell(node.platformType)).append(',')
                    .append(cell(node.ipAddress)).append(',').append(cell(node.status(now))).append(',')
                    .append(node.lastTelemetryTimestamp == 0 ? "" : String.format(Locale.ROOT, "%.6f", node.lastEntropy)).append(',')
                    .append(node.lastTelemetryTimestamp == 0 ? "" : String.format(Locale.ROOT, "%.6f", node.lastSalience)).append(',')
                    .append(node.messageCount).append(',').append(Instant.ofEpochMilli(node.lastSeenTimestamp)).append(',')
                    .append(node.lastTelemetryTimestamp == 0 ? "" : Instant.ofEpochMilli(node.lastTelemetryTimestamp)).append("\r\n");
        }
        return csv.toString();
    }
    static String cell(String value) {
        // Prevent spreadsheet formula evaluation for externally supplied identifiers.
        String safe = value.matches("^[=+@\\-].*") ? "'" + value : value;
        return "\"" + safe.replace("\"", "\"\"") + "\"";
    }
}

