import neural.studio.*;
import java.util.UUID;

/**
 * Core Data Substrate representing a physical tracking location on the World Grid.
 * Encapsulates the metric indices for local, regional, and global scopes.
 */
public class GridNode {
    public enum Scope { LOCAL, REGIONAL, GLOBAL }
    public enum Status { BALANCED, COMPLIANT, REBALANCING, FLAGGED_VIOLATION }

    private final UUID nodeCid;
    private final String locationName;
    private final Scope scope;
    private double efficiencyYield;
    private double humanFloorImpact;
    private Status status;
    private long lastHeartbeat;

    public GridNode(String locationName, Scope scope, double efficiencyYield, double humanFloorImpact) {
        this.nodeCid = UUID.randomUUID();
        this.locationName = locationName;
        this.scope = scope;
        this.efficiencyYield = efficiencyYield;
        this.humanFloorImpact = humanFloorImpact;
        this.status = humanFloorImpact < 0.0 ? Status.FLAGGED_VIOLATION : Status.BALANCED;
        this.lastHeartbeat = System.currentTimeMillis();
    }

    public synchronized void updateMetrics(double yield, double floorImpact) {
        this.efficiencyYield = yield;
        this.humanFloorImpact = floorImpact;
        // Automatically isolate conflicting vectors if floor dips below zero
        if (floorImpact < 0.0) {
            this.status = Status.FLAGGED_VIOLATION;
        } else if (this.status == Status.REBALANCING && floorImpact >= 0.2) {
            this.status = Status.BALANCED;
        } else if (yield > 0.85) {
            this.status = Status.COMPLIANT;
        } else {
            this.status = Status.BALANCED;
        }
        this.lastHeartbeat = System.currentTimeMillis();
    }

    public synchronized void forceVirtueRefactor(double adjustedFloor) {
        this.humanFloorImpact = adjustedFloor;
        this.status = Status.REBALANCING;
        this.lastHeartbeat = System.currentTimeMillis();
    }

    public UUID getNodeCid() { return nodeCid; }
    public String getLocationName() { return locationName; }
    public Scope getScope() { return scope; }
    public synchronized double getEfficiencyYield() { return efficiencyYield; }
    public synchronized double getHumanFloorImpact() { return humanFloorImpact; }
    public synchronized Status getStatus() { return status; }
    public synchronized long getLastHeartbeat() { return lastHeartbeat; }
}
