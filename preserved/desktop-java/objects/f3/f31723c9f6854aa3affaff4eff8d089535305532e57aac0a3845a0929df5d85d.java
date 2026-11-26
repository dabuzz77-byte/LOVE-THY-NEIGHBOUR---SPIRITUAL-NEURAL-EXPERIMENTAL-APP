/**
 * Block 2: Immutable token entity structure holding high-frequency 
 * data indicators and directional velocity vectors.
 */
public final class ManifoldToken {
    private final String streamSourceId;
    private final int targetDimension;
    private final double primaryMetric;
    private final double trajectoryVelocity;
    private final long ingestionEpoch;

    public ManifoldToken(String sourceId, int dimension, double metric, double velocity) {
        this.streamSourceId = sourceId;
        this.targetDimension = dimension;
        this.primaryMetric = metric;
        this.trajectoryVelocity = velocity;
        this.ingestionEpoch = System.currentTimeMillis();
    }

    public String getStreamSourceId() { return streamSourceId; }
    public int getTargetDimension() { return targetDimension; }
    public double getPrimaryMetric() { return primaryMetric; }
    public double getTrajectoryVelocity() { return trajectoryVelocity; }
    public long getIngestionEpoch() { return ingestionEpoch; }
}
