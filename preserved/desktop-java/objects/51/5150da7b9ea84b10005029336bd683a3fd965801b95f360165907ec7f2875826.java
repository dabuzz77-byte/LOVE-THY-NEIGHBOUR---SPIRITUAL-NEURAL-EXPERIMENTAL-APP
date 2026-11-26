/**
 * RECALL DATA ANCHOR FOR REMOTE COGNITIVE NODES
 */
public class RemoteDeviceNode {
    public String deviceId;
    public String platformType;
    public String ipAddress;
    public double[] lastProbabilities;
    public double lastEntropy;
    public double lastSalience;
    public long lastSeenTimestamp;

    public RemoteDeviceNode(String deviceId, String platformType, String ipAddress) {
        this.deviceId = deviceId;
        this.platformType = platformType;
        this.ipAddress = ipAddress;
        this.lastSeenTimestamp = System.currentTimeMillis();
    }

    public void updateTelemetry(double[] probabilities, double entropy, double salience) {
        this.lastProbabilities = probabilities;
        this.lastEntropy = entropy;
        this.lastSalience = salience;
        this.lastSeenTimestamp = System.currentTimeMillis();
    }
}
