package net.activeinference.beacon.core;
import neural.studio.*;


import java.util.UUID;

public class UserWelfareNode {
    private final UUID id;
    private final String location;
    private double wellnessBuffer;

    public UserWelfareNode(String location, double initialWelfare) {
        this.id = UUID.randomUUID();
        this.location = location;
        this.wellnessBuffer = initialWelfare;
    }

    public UUID getId() { return id; }
    public String getLocation() { return location; }
    public synchronized double getWelfare() { return wellnessBuffer; }
    
    public synchronized void adjustWelfare(double delta) {
        this.wellnessBuffer = Math.min(1.0, Math.max(0.0, this.wellnessBuffer + delta));
    }
}
