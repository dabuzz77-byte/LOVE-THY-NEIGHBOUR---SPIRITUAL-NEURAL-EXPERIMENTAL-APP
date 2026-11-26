import javax.swing.*;
import java.awt.*;
import java.io.IOException;

/**
 * Consolidated entry-point bootstrap class launching both the network bus router 
 * and the concurrent background task matrix simulation.
 */
public class FluxMonitorApp extends JFrame {
    private final FluxOrchestrationBus communicationBus;
    private final FluxMonitorCanvas userInterfaceCanvas;

    public FluxMonitorApp() throws IOException {
        this.communicationBus = new FluxOrchestrationBus(7830);
        this.userInterfaceCanvas = new FluxMonitorCanvas();

        setupApplicationFrame();

        // Wire streaming bus telemetry payloads directly to repaint the display layers
        this.communicationBus.registerSubscriber(frame -> {
            String logAnnotation = frame.isAlignmentPassActive() ? 
                "[ALIGNMENT PULSE] Asymmetry Trapped -> Restructured Matrix." :
                "[STREAMING DATA] Processing normal-state telemetry matrix.";
            
            SwingUtilities.invokeLater(() -> 
                userInterfaceCanvas.updateCanvasState(frame, logAnnotation)
            );
        });

        this.communicationBus.startEventLoop();
        executeBackgroundSimulationPipeline();
    }

    private void setupApplicationFrame() {
        setTitle("DEEPMIND PARITY LOGIC REFACTOR ENGINE // ONGOING = TRUE");
        setSize(1000, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        
        setLayout(new BorderLayout());
        add(userInterfaceCanvas, BorderLayout.CENTER);
    }

    /**
     * Spins detached simulation cycles, pulsing unbalanced matrices followed by 
     * high-virtue structural alignments back to back across the streaming channels.
     */
    private void executeBackgroundSimulationPipeline() {
        Thread workerThread = new Thread(() -> {
            boolean alignmentToggle = false;
            
            // Raw noisy initial input configuration matrix profile structures
            boolean[][] conflictMatrix = {
                {true, false, true, false},
                {false, true, false, true},
                {true, false, true, false},
                {false, true, false, true}
            };

            while (true) {
                FluxPayload testFrame = new FluxPayload(conflictMatrix, alignmentToggle);
                communicationBus.dispatchLocalPayload(testFrame);
                
                // Flip parameters to cycle through normal and refactored views sequentially
                alignmentToggle = !alignmentToggle;

                try {
                    Thread.sleep(1200); 
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "SimulationDataProvider");
        
        workerThread.setDaemon(true);
        workerThread.start();
    }

    public static void main(String[] args) {
        System.out.println("[BOOTSTRAP] Orchestrating High-Frequency Flux Application Context...");
        
        SwingUtilities.invokeLater(() -> {
            try {
                FluxMonitorApp mainApplicationFrame = new FluxMonitorApp();
                mainApplicationFrame.setVisible(true);
                System.out.println("[BOOTSTRAP] GUI display frame compiled and listening smoothly.");
            } catch (IOException e) {
                System.err.println("[CRITICAL INIT FAILURE] Failed to spawn network bus: " + e.getMessage());
            }
        });
    }
}
