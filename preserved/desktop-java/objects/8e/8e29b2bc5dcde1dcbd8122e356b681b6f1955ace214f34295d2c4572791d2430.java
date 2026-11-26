package engine.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class TelemetryModel {
    private double currentFlux = 0.0;
    private double dynamicFrequency = 7.83;
    private double algorithmicDebtTar = 0.0;
    private double alignmentScore = 0.985;
    private int cycleCount = 0;
    
    private final List<DeviceNode> perimeterNodes = Collections.synchronizedList(new ArrayList<>());

    public synchronized void updateState(double flux, double freq, double debt, double alignment, int cycles) {
        this.currentFlux = flux;
        this.dynamicFrequency = freq;
        this.algorithmicDebtTar = debt;
        this.alignmentScore = alignment;
        this.cycleCount = cycles;
    }

    public List<DeviceNode> getPerimeterNodes() { return perimeterNodes; }
    public double getCurrentFlux() { return currentFlux; }
    public double getDynamicFrequency() { return dynamicFrequency; }
    public double getAlgorithmicDebtTar() { return algorithmicDebtTar; }
    public double getAlignmentScore() { return alignmentScore; }
    public int getCycleCount() { return cycleCount; }

    public static class DeviceNode {
        public String id, ip, os, status;
        public DeviceNode(String id, String ip, String os, String status) {
            this.id = id; this.ip = ip; this.os = os; this.status = status;
        }
    }
}
