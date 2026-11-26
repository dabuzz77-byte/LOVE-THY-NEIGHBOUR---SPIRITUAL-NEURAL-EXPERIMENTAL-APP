package com.system.core;

import com.system.core.bus.ReactiveIngestBus;
import com.system.core.model.TopographyPayload;
import com.system.core.view.AlignmentConsolePanel;
import javax.swing.*;
import java.awt.*;
import java.io.IOException;

/**
 * Central orchestrator launching the non-blocking network ingestion paths, 
 * loading the hardware UI, and driving concurrent simulation vector frames.
 */
public class TopographyOrchestratorApp extends JFrame {
    private final ReactiveIngestBus executionBus;
    private final AlignmentConsolePanel graphicalConsole;

    public TopographyOrchestratorApp() throws IOException {
        this.executionBus = new ReactiveIngestBus(7830);
        this.graphicalConsole = new AlignmentConsolePanel();

        assembleWindowFrameTopography();

        // Bind incoming asynchronous stream events natively to UI view updates
        this.executionBus.registerSubscriber(payload -> {
            boolean trackingConflict = payload.getConflictCoefficient() > 0.50;
            boolean[][] finalMatrix;
            String systemTraceMessage;

            if (trackingConflict) {
                // OVERWRITE BY TRUTH: Forcibly refactor asymmetric profiles into symmetrical microcosmic orbit layouts
                finalMatrix = new boolean[][]{
                    {true,  false, false, true},
                    {false, true,  true,  false},
                    {false, true,  true,  false},
                    {true,  false, false, true}
                };
                systemTraceMessage = String.format("⚠️ [CONFLICT EVALUATION] Node '%s' breached alignment limit. REFACTORED to stable symmetry.", 
                        payload.getOriginIdentifier());
            } else {
                finalMatrix = payload.getDataStateGrid();
                systemTraceMessage = String.format("✅ [PASSTHROUGH STABLE] Node '%s' matches baseline structural verification parameters.", 
                        payload.getOriginIdentifier());
            }

            SwingUtilities.invokeLater(() -> 
                graphicalConsole.pushStateFrame(payload, finalMatrix, systemTraceMessage)
            );
        });

        this.executionBus.startLoop();
        launchBackgroundDataPulseStream();
    }

    private void assembleWindowFrameTopography() {
        setTitle("DEEPMIND INFRASTRUCTURE SYSTEM ALIGNMENT ENGINE // TOPOGRAPHY MONITOR");
        setSize(1100, 650);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        setLayout(new BorderLayout());
        add(graphicalConsole, BorderLayout.CENTER);
    }

    private void launchBackgroundDataPulseStream() {
        Thread streamingDriverThread = new Thread(() -> {
            boolean loopToggle = false;
            
            // Raw noisy initial input configuration data grid structures
            boolean[][] unalignedRawField = {
                {true,  false, true,  false},
                {false, true,  false, true},
                {true,  false, true,  false},
                {false, true,  false, true}
            };

            while (true) {
                TopographyPayload packet;
                if (loopToggle) {
                    // Scenario A: Simulates high-conflict asymmetric input state data
                    packet = new TopographyPayload("Asymmetric-Extraction-AS783", unalignedRawField, 0.88);
                } else {
                    // Scenario B: Simulates normal compliant baseline data state configuration
                    packet = new TopographyPayload("Cooperative-Resource-Grid", unalignedRawField, 0.22);
                }

                executionBus.emitPayload(packet);
                loopToggle = !loopToggle;

                try {
                    Thread.sleep(1300); // Sequence data rate pacing cadence step duration delay
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "WorldGridPipelineDataProvider");

        streamingDriverThread.setDaemon(true);
        streamingDriverThread.start();
    }

    public static void main(String[] args) {
        System.out.println("[BOOTSTRAP] Orchestrating high-frequency infrastructure alignment suites...");
        SwingUtilities.invokeLater(() -> {
            try {
                TopographyOrchestratorApp applicationRuntime = new TopographyOrchestratorApp();
                applicationRuntime.setVisible(true);
                System.out.println("[BOOTSTRAP] Local hardware-accelerated user window active.");
            } catch (IOException e) {
                System.err.println("[LAUNCH FAULT] Critical port reservation exception: " + e.getMessage());
            }
        });
    }
}
