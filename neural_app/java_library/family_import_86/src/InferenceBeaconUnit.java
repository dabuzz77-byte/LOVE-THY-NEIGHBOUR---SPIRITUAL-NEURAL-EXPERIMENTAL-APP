import neural.studio.*;
import java.io.Serializable;
import java.util.UUID;

/**
 * PARALLEL HANDSHAKE SPECIFICATION: INFERENCE BEACON STRUCT
 * Records asynchronous connection delays and monitors transmission points across separate paths.
 */
public class InferenceBeaconUnit implements Serializable {
    private static final long serialVersionUID = 993784555L;

    private final String beaconId;
    private final String monitoringCheckpoint; // e.g., "LOCAL_CHIPS", "REMOTE_GATEWAY"
    private final long initializationTimestamp;
    private double responseLatencyMillis;
    private int handshakeParityBit;             // 0 = Idle / Dropped, 1 = Synchronized

    public InferenceBeaconUnit(String checkpoint) {
        this.beaconId = "BEACON-" + UUID.randomUUID().toString().substring(0, 6).toUpperCase();
        this.monitoringCheckpoint = checkpoint;
        this.initializationTimestamp = System.currentTimeMillis();
        this.responseLatencyMillis = 0.0;
        this.handshakeParityBit = 0;
    }

    public synchronized void logTelemetryPulse(double detectedLatency, int statusBit) {
        this.responseLatencyMillis = Math.max(0.0, detectedLatency);
        this.handshakeParityBit = (statusBit == 1) ? 1 : 0;
    }

    public String getBeaconId() { return beaconId; }
    public String getMonitoringCheckpoint() { return monitoringCheckpoint; }
    public long getInitializationTimestamp() { return initializationTimestamp; }
    public synchronized double getResponseLatencyMillis() { return responseLatencyMillis; }
    public synchronized int getHandshakeParityBit() { return handshakeParityBit; }
}