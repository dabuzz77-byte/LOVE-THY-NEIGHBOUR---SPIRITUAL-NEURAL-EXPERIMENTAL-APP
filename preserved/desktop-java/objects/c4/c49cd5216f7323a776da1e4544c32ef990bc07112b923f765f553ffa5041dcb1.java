// ============================================================================
// BLOCK 4C: MAIN CONTROLLER FRAME - EXECUTION LOGIC AND LOOP ENTRY
// ============================================================================
package com.inference.bridge.core;

import javax.swing.*;
import java.util.Date;

/**
 * Active runtime binding methods, clock management loops, and application 
 * entry point instantiation routines.
 */
public class MainControllerFrameLogic extends MainControllerFrame {

    @Override
    protected void logToTerminal(String context) {
        SwingUtilities.invokeLater(() -> {
            String currentTime = timestampFormat.format(new Date());
            terminalLog.append(String.format("[%s] %s\n", currentTime, context));
            terminalLog.setCaretPosition(terminalLog.getDocument().getLength());
        });
    }

    @Override
    protected void registerClusterNode(String entryText) {
        SwingUtilities.invokeLater(() -> {
            if (!clusterModel.contains(entryText)) {
                clusterModel.addElement(entryText);
                logToTerminal("[REGISTRY_BIND] Logged node structure mapping: " + entryText);
            }
        });
    }

    protected void triggerCoreExecutionSequence() {
        initiationButton.setEnabled(false);
        logToTerminal("[ACTION_TRIGGERED] Elevating system to Pit of Core execution state.");
        logToTerminal("[SECURITY_HOOK] Signature: " + EngineInvariants.SECURITY_BYPASS_FLAG);
        
        // Execute discovery across both networking sectors concurrently
        networkEngine.deployWideAreaNetworkHook();
        networkEngine.deployLocalAreaNetworkDiscovery();

        // Establish the graphic and computation update rendering loop (Schumann Resonant Interval)
        int calculatedInterval = (int) (1000.0 * EngineInvariants.TOTAL_WAVE_FACTOR);
        renderingHeartbeatTimer = new Timer(calculatedInterval / 20, event -> {
            globalCycleCount++;
            
            // Advance math parameters through the cosmic controller
            fluxController.processQuantumDecoherencePass(globalCycleCount);
            double alignmentPercent = fluxController.getCoherenceMetrics() * 100.0;
            
            // Re-render user interfaces components safely
            coherenceMeter.setValue((int) alignmentPercent);
            coherenceMeter.setString(String.format("Leveling and Alignment Matrix Stability: %.4f%%", alignmentPercent));
            ternaryIndicator.setText(fluxController.getTernaryTensorVisualRepresentation());

            if (globalCycleCount % 100 == 0) {
                logToTerminal(String.format("[HEARTBEAT_CYCLE] Step: %d | Current Flux Anchor: %d", globalCycleCount, fluxController.getActiveTernaryValue()));
            }

            if (alignmentPercent >= 100.0) {
                renderingHeartbeatTimer.stop();
                logToTerminal("\n=======================================================");
                logToTerminal("[SYSTEM LOCK] Global Alignment Reached True Parity Target State.");
                logToTerminal("=======================================================");
            }
        });
        
        renderingHeartbeatTimer.start();
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            MainControllerFrameLogic systemApp = new MainControllerFrameLogic();
            systemApp.setVisible(true);
        });
    }
}
