package net.activeinference.beacon.core;
import neural.studio.*;


public class ComputeIslandNode {
    private final String id;
    private final long maxCores;
    private long usedCores;
    private final long floorCores;

    public ComputeIslandNode(String id, long maxCores) {
        this.id = id;
        this.maxCores = maxCores;
        this.usedCores = 0;
        this.floorCores = (long) (maxCores * 0.25);
    }

    public synchronized String getId() { return id; }
    public synchronized long getMaxCores() { return maxCores; }
    public synchronized long getUsedCores() { return usedCores; }

    public synchronized boolean allocate(long cores) {
        if ((maxCores - usedCores) - cores >= floorCores) {
            this.usedCores += cores;
            return true;
        }
        return false;
    }

    public synchronized void flush() {
        this.usedCores = 0;
    }
}
