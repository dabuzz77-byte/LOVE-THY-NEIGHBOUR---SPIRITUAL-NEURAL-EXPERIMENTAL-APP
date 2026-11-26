package net.activeinference.beacon;

/**
 * Payload Trajectory: Models network data packets passing through the filter proxies.
 */
public class TrajectoryPayload {
    private final String taskId;
    private final double dopamineTriggerIndex; // 0.0 to 1.0 (High Addictive Profile)
    private final long payloadSizeBytes;

    public TrajectoryPayload(String taskId, double dopamineTriggerIndex, long payloadSizeBytes) {
        this.taskId = taskId;
        this.dopamineTriggerIndex = dopamineTriggerIndex;
        this.payloadSizeBytes = payloadSizeBytes;
    }

    public String getTaskId() {
        return this.taskId;
    }

    public double getDopamineTriggerIndex() {
        return this.dopamineTriggerIndex;
    }

    public long getPayloadSizeBytes() {
        return this.payloadSizeBytes;
    }
}
