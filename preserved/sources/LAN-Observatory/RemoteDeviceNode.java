/** Immutable snapshot, safe to share between the receiver and the Swing event thread. */
public final class RemoteDeviceNode {
    public final String deviceId;
    public final String platformType;
    public final String ipAddress;
    public final double lastEntropy;
    public final double lastSalience;
    public final long lastSeenTimestamp;
    public final long lastTelemetryTimestamp;
    public final long messageCount;
    private final double[] probabilities;

    public RemoteDeviceNode(String id, String platform, String ip) {
        this(id, platform, ip, new double[0], 0, 0, System.currentTimeMillis(), 0, 0);
    }

    private RemoteDeviceNode(String id, String platform, String ip, double[] probabilities,
                             double entropy, double salience, long seen, long telemetry, long count) {
        deviceId = id;
        platformType = platform;
        ipAddress = ip;
        this.probabilities = probabilities.clone();
        lastEntropy = entropy;
        lastSalience = salience;
        lastSeenTimestamp = seen;
        lastTelemetryTimestamp = telemetry;
        messageCount = count;
    }

    public RemoteDeviceNode heartbeat(String platform, String ip, long now) {
        return new RemoteDeviceNode(deviceId, platform, ip, probabilities, lastEntropy, lastSalience,
                now, lastTelemetryTimestamp, messageCount);
    }

    public RemoteDeviceNode updateTelemetry(double[] values, double entropy, double salience, long now) {
        return new RemoteDeviceNode(deviceId, platformType, ipAddress, values, entropy, salience,
                now, now, messageCount + 1);
    }

    public double[] getProbabilities() { return probabilities.clone(); }
    public String status(long now) {
        if (now - lastSeenTimestamp > 10_000) return "Quiet";
        if (lastTelemetryTimestamp == 0) return "Discovered";
        return now - lastTelemetryTimestamp > 10_000 ? "Awaiting data" : "Streaming";
    }
}

