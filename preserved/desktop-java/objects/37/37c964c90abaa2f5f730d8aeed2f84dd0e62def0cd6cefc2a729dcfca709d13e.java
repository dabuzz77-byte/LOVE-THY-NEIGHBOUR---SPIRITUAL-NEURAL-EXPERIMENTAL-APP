package net.activeinference.beacon;

import java.util.UUID;

/**
 * Human Endpoint Model: Tracks client wellness states and active quotas.
 */
public class UserEndpointNode {
    private final UUID endpointId;
    private final String regionalTag;
    private double baselineWelfareScore; // 0.0 (Exploited) to 1.0 (Flourishing)
    private double activeComputeQuotaTflops;

    public UserEndpointNode(UUID endpointId, String regionalTag, double baselineWelfareScore) {
        this.endpointId = endpointId;
        this.regionalTag = regionalTag;
        this.baselineWelfareScore = baselineWelfareScore;
        this.activeComputeQuotaTflops = 0.0;
    }

    public UUID getEndpointId() {
        return this.endpointId;
    }

    public synchronized double getBaselineWelfareScore() {
        return this.baselineWelfareScore;
    }

    public synchronized double getActiveComputeQuotaTflops() {
        return this.activeComputeQuotaTflops;
    }

    public synchronized void injectWelfareRecovery(double welfareDelta, double computeAllocation) {
        this.baselineWelfareScore = Math.min(1.00, this.baselineWelfareScore + welfareDelta);
        this.activeComputeQuotaTflops += computeAllocation;
    }
}
