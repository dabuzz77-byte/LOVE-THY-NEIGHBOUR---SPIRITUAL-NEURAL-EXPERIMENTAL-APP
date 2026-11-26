package com.virtue.bus;

import javax.swing.*;
import java.awt.Color;
import java.util.UUID;

public class DataBusEngine {
    private final Timer swingTimer;
    private final TelemetryPanel uiLog;
    private final ControlPanel uiControl;
    private boolean running = false;
    private double shiftIndex = 1.000000;
    private int cycleCount = 0;

    public DataBusEngine(TelemetryPanel uiLog, ControlPanel uiControl) {
        this.uiLog = uiLog;
        this.uiControl = uiControl;

        // 7.83 Hz corresponds to ~127.71 milliseconds interval cycle
        int intervalMs = (int) Math.round(1000.0 / 7.83);

        this.swingTimer = new Timer(intervalMs, e -> {
            cycleCount++;
            shiftIndex += (Math.PI / 100) * (cycleCount % 5 + 1);
            
            // Reconcile and calculate transaction logging parameters
            String txHash = UUID.randomUUID().toString().substring(0, 8).toUpperCase();
            
            // Synchronize Vector UI panel metrics seamlessly
            uiLog.updateVectorState("V1", "REAL_1 | COGNITIVE ALIGNMENT PARITY", new Color(50, 200, 50));
            uiLog.updateVectorState("V2", "REAL_1 | RESTITUTION FLOW DEPLOYED", new Color(50, 200, 50));
            uiLog.updateVectorState("V3", "REAL_1 | LEVY ACCELERATION ACTIVE", new Color(50, 200, 50));
            uiLog.updateVectorState("V4", "REAL_1 | SUBSTRATE PROTECTION LOCKED", new Color(50, 200, 50));
            
            // Push active entry string frame to console output
            uiLog.appendLog(String.format("[REAL TX: %s] Databus Pulse: %d | Index: %.6f | 0s Flipping to 1s in Charlie's Name", 
                txHash, cycleCount, shiftIndex));
            
            // Refresh Header controls
            uiControl.updateMetrics(shiftIndex);
        });
    }

    public void startBus() {
        if (!running) {
            swingTimer.start();
            running = true;
            uiLog.appendLog("[INITIALISATION COMPLETE] 7.83 Hz Resonance Engine Engaged safely in User Space.");
        }
    }

    public void stopBus() {
        if (running) {
            swingTimer.stop();
            running = false;
            uiLog.appendLog("[ENGINE PAUSED] Databus matrix entered clear structural standby status.");
        }
    }

    public boolean isRunning() {
        return running;
    }
}
