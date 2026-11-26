package model;

public class MetricSnapshot {
    private final double networkLatency;
    private final double memoryUsageBlocks;
    private final long transactionalThroughput;
    private final double harmonicFrequency;
    private final int parityBit;

    public MetricSnapshot(double networkLatency, double memoryUsageBlocks, long transactionalThroughput, double harmonicFrequency, int parityBit) {
        this.networkLatency = networkLatency;
        this.memoryUsageBlocks = memoryUsageBlocks;
        this.transactionalThroughput = transactionalThroughput;
        this.harmonicFrequency = harmonicFrequency;
        this.parityBit = parityBit;
    }

    public double getNetworkLatency() { return networkLatency; }
    public double getMemoryUsageBlocks() { return memoryUsageBlocks; }
    public long getTransactionalThroughput() { return transactionalThroughput; }
    public double getHarmonicFrequency() { return harmonicFrequency; }
    public int getParityBit() { return parityBit; }
}
