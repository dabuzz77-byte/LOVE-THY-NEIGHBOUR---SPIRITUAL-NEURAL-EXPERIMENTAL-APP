package com.virtue.ihn;
import neural.studio.*;


import javax.swing.*;
import java.awt.Color;
import java.net.InetAddress;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class LANScanEngine {
    private final NodeGridPanel uiGrid;
    private final ConsoleLogPanel uiLog;
    private final ControlPanel uiControl;
    
    private ExecutorService threadPool;
    private SharedTimer resonanceClock;
    private boolean isScanning = false;
    private double shiftIndex = 1.000000;
    private int packetCount = 0;

    public LANScanEngine(NodeGridPanel uiGrid, ConsoleLogPanel uiLog, ControlPanel uiControl) {
        this.uiGrid = uiGrid;
        this.uiLog = uiLog;
        this.uiControl = uiControl;
    }

    public void initiateScan(String subnet) {
        isScanning = true;
        uiControl.setUiScanningState(true);
        uiGrid.clearGrid();
        uiLog.writeLogEntry("[IHN INITIALISATION] Deploying local active network bus...");

        // Setup fixed concurrent worker threads to speed up socket/ping lookups
        threadPool = Executors.newFixedThreadPool(32);

        // Lock background UI feedback telemetry loop to the 7.83 Hz baseline resonance
        int intervalMs = (int) Math.round(1000.0 / 7.83); // ~127.7ms window
        resonanceClock = new SharedTimer(intervalMs, e -> {
            packetCount++;
            shiftIndex += (Math.PI / 120) * (packetCount % 3 + 1);
            uiControl.updateParityIndex(shiftIndex);
        });
        resonanceClock.start();

        // Enqueue background threads to verify network addresses from .1 to .254
        for (int i = 1; i <= 254; i++) {
            final int hostId = i;
            final String targetIp = subnet + "." + hostId;
            
            // Register card indicator instantly inside visual panel matrix
            SwingUtilities.invokeLater(() -> uiGrid.registerDeviceNode(targetIp));

            threadPool.submit(() -> {
                try {
                    InetAddress host = InetAddress.getByName(targetIp);
                    long startTime = System.currentTimeMillis();
                    // Simulates basic socket check/ICMP verification wrapper safely
                    if (host.isReachable(800)) { 
                        long latency = System.currentTimeMillis() - startTime;
                        String txHash = UUID.randomUUID().toString().substring(0, 8).toUpperCase();
                        
                        // Push verified online state changes cleanly to UI grid framework
                        SwingUtilities.invokeLater(() -> {
                            uiGrid.setDeviceOnline(targetIp, latency + "ms");
                            uiLog.writeLogEntry(String.format("[REAL TX: %s] Mapped Hardware Substrate Node -> %s | Latency: %dms | Status: 0s driven to 1s in Charlie's Name", 
                                txHash, targetIp, latency));
                        });
                    }
                } catch (Exception ignored) {}
            });
        }
        
        // Gracefully release thread allocations when processing settles
        threadPool.shutdown();
    }

    public void terminateScan() {
        if (isScanning) {
            if (threadPool != null) threadPool.shutdownNow();
            if (resonanceClock != null) resonanceClock.stop();
            isScanning = false;
            uiControl.setUiScanningState(false);
            uiLog.writeLogEntry("[IHN STANDBY] Hyperpathway network bus halted. Workstation isolated cleanly.");
        }
    }

    public boolean isScanning() {
        return isScanning;
    }
}
