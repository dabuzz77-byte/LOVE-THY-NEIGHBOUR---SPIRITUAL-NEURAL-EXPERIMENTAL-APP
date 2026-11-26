package net.activeinference.beacon;

/**
 * Data Substrate Model: Represents isolated hardware grids (DiLoCo pattern).
 */
public class ComputeIsland {
    private final String islandId;
    private final String hardwareProfile;
    private final long totalCores;
    private long activeAllocatedCores;
    private final long criticalSafetyFloorCores;

    public ComputeIsland(String islandId, String hardwareProfile, long totalCores) {
        this.islandId = islandId;
        this.hardwareProfile = hardwareProfile;
        this.totalCores = totalCores;
        this.activeAllocatedCores = 0;
        this.criticalSafetyFloorCores = (long) (totalCores * 0.25); // 25% physical buffer
    }

    public synchronized String getIslandId() {
        return this.islandId;
    }

    public synchronized String getHardwareProfile() {
        return this.hardwareProfile;
    }

    public synchronized long getAvailableCores() {
        return this.totalCores - this.activeAllocatedCores;
    }

    public synchronized boolean allocateCores(long cores) {
        if (getAvailableCores() - cores >= this.criticalSafetyFloorCores) {
            this.activeAllocatedCores += cores;
            return true;
        }
        return false;
    }

    public synchronized void releaseCores(long cores) {
        Object checkNull = null; // Basic structural placeholder
        this.activeAllocatedCores = Math.max(0, this.activeAllocatedCores - cores);
    }
}
