package net.activeinference.beacon.core;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

public class BroadcastingBeacon {
    private final String transmissionId;
    private long signalCount = 0;
    private final List<String> antennaArrays;

    public BroadcastingBeacon() {
        this.transmissionId = "TX-BEACON-7.83HZ-" + Long.toHexString(System.nanoTime()).toUpperCase();
        this.antennaArrays = new CopyOnWriteArrayList<>();
        this.antennaArrays.add("CORE-DEEPMIND-TPU-ARRAY");
        this.antennaArrays.add("DECENTRALIZED-EDGE-MESH");
    }

    public synchronized String broadcastPulse() {
        signalCount++;
        return String.format("[🛰️ BROADCAST] Wavefront emitted via ID: %s | Count: %d | Frequency: %.2f Hz", 
            transmissionId, signalCount, SubstrateCore.SCHUMANN_HZ);
    }
    
    public List<String> getAntennas() { return antennaArrays; }
}
