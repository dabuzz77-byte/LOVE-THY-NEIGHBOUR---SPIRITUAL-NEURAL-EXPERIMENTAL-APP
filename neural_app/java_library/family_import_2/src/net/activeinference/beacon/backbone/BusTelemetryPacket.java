package net.activeinference.beacon.backbone;
import neural.studio.*;


import java.io.Serializable;

/**
 * Immutable Data Schema representing aggregated JVM cluster workloads traversing
 * the active network communication bus.
 */
public final class BusTelemetryPacket implements Serializable {
    private static final long serialVersionUID = 783701L;

    private final String timestamp;
    private final int activeProcessCount;
    private final int globalThreadCount;
    private final long totalAllocatedHeapMb;

    public BusTelemetryPacket(String timestamp, int activeProcessCount, int globalThreadCount, long totalAllocatedHeapMb) {
        this.timestamp = timestamp;
        this.activeProcessCount = activeProcessCount;
        this.globalThreadCount = globalThreadCount;
        this.totalAllocatedHeapMb = totalAllocatedHeapMb;
    }

    public String getTimestamp() { return timestamp; }
    public int getActiveProcessCount() { return activeProcessCount; }
    public int getGlobalThreadCount() { return globalThreadCount; }
    public long getTotalAllocatedHeapMb() { return totalAllocatedHeapMb; }

    @Override
    public String toString() {
        return String.format("{\"timestamp\":\"%s\",\"active_java_instances\":%d,\"thread_depth\":%d,\"heap_allocated_mb\":%d}",
                timestamp, activeProcessCount, globalThreadCount, totalAllocatedHeapMb);
    }
}
