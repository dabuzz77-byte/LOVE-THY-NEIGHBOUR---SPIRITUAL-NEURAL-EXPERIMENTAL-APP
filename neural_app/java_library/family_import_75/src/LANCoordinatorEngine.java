import neural.studio.*;
import javax.swing.*;
import java.awt.*;

/**
 * SYSTEM MAIN FRAME COORDINATOR
 * Compiles local metrics and coordinates tracking operations for mobile assets over LAN.
 */
public class LANCoordinatorEngine extends SectionFrame {
    private static final int DISPLAY_W = 1400;
    private static final int DISPLAY_H = 800;

    private final QuantumTernaryBinaryCore localCore;
    private final LocalNetworkLatchingEngine networkEngine;
    private final HardwareMetricSampler sampler;
    
    private LANMatrixCanvas interfaceCanvas;
    private SharedTimer frameRefreshClock;

    public LANCoordinatorEngine() {
        setTitle("WINDOWS 11 CORE COORDINATOR ENGINE [TOTAL LOCAL LAN MATRIX LATCHING]");
        setSize(DISPLAY_W, DISPLAY_H);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Core Allocations
        this.localCore = new QuantumTernaryBinaryCore(6, 0.40);
        this.networkEngine = new LocalNetworkLatchingEngine();
        this.sampler = new HardwareMetricSampler();

        buildInterfaceStructure();
        initializeExecutionPipelines();
    }

    private void buildInterfaceStructure() {
        setLayout(new BorderLayout());
        this.interfaceCanvas = new LANMatrixCanvas(localCore, networkEngine);
        add(interfaceCanvas, BorderLayout.CENTER);
    }

    private void initializeExecutionPipelines() {
        // Start non-blocking socket loops
        networkEngine.startEngine();

        // Bind main screen renderer ticker loop (~40 FPS)
        frameRefreshClock = new SharedTimer(25, e -> {
            double[] metrics = sampler.sampleHardwareInterrupts();
            localCore.processQuantumState(metrics);
            interfaceCanvas.repaint();
        });
        frameRefreshClock.start();
    }

    @Override
    public void dispose() {
        frameRefreshClock.stop();
        networkEngine.stopEngine();
        super.dispose();
    }

    // INTERNAL HELPER FOR SIMULATING NATIVE DESKTOP REGISTER PRESSURE
    private static class HardwareMetricSampler {
        private final double[] buffer = new double[64];
        public double[] sampleHardwareInterrupts() {
            for (int i = 0; i < buffer.length; i++) {
                buffer[i] = Math.sin(i * 0.15) * Math.cos(System.currentTimeMillis() * 0.002);
            }
            return buffer;
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            LANCoordinatorEngine app = new LANCoordinatorEngine();
            app.setVisible(true);
        });
    }
}
