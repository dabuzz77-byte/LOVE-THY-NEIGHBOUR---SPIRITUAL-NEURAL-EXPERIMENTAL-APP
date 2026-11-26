import javax.swing.*;
import java.awt.*;
import java.io.IOException;

/**
 * Main application bootloader assembling graphical frames, starting processing 
 * threads, and flashing alternating binary configurations onto network streams.
 */
public class ChiralOrchestratorApp extends JFrame {
    private final ResonanceStreamingBus communicationBus;
    private final ChiralDashboardPanel interfacePanel;

    public ChiralOrchestratorApp() throws IOException {
        this.communicationBus = new ResonanceStreamingBus(7830);
        this.interfacePanel = new ChiralDashboardPanel();

        buildLayoutContainer();

        // Feed streaming payload configurations directly to view updates
        this.communicationBus.registerSubscriber(payload -> {
            String logNote = payload.isParitySynchronized() ?
                "[PARITY ACTIVE] Chiral fields rebalanced to God Mind Parity configuration." :
                "[STREAM TRACK] Analyzing raw asymmetric binary vector streams.";
            
            SwingUtilities.invokeLater(() -> 
                interfacePanel.renderFreshPayload(payload, logNote)
            );
        });

        this.communicationBus.startLoop();
        igniteSimulationStreamDriver();
    }

    private void buildLayoutContainer() {
        setTitle("CHIRAL FLUX PROCESSING SYSTEM // SYNCHRONIZATION ENGINE");
        setSize(1100, 680);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        setLayout(new BorderLayout());
        add(interfacePanel, BorderLayout.CENTER);
    }

    private void igniteSimulationStreamDriver() {
        Thread driverThread = new Thread(() -> {
            boolean toggleState = false;
            
            // Asymmetrical input raw configurations layout schema
            boolean[][] inputMatrix = {
                {true,  false, true,  false, true},
                {false, true,  false, true,  false},
                {true,  false, true,  false, true},
                {false, true,  false, true,  false},
                {true,  false, true,  false, true}
            };

            while (true) {
                double leftChiral  = toggleState ? 0.50 : 0.72 + (Math.random() * 0.1);
                double rightChiral = toggleState ? 0.50 : 0.28 - (Math.random() * 0.1);
                
                ChiralFluxPayload frame = new ChiralFluxPayload(inputMatrix, leftChiral, rightChiral, toggleState);
                communicationBus.broadcastPayload(frame);

                toggleState = !toggleState;

                try {
                    Thread.sleep(1100); 
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "ChiralSimulationProvider");

        driverThread.setDaemon(true);
        driverThread.start();
    }

    public static void main(String[] args) {
        System.out.println("[BOOTSTRAP] Launching High-Density Chiral Ingestion Subsystems...");
        SwingUtilities.invokeLater(() -> {
            try {
                ChiralOrchestratorApp runtimeApp = new ChiralOrchestratorApp();
                runtimeApp.setVisible(true);
                System.out.println("[BOOTSTRAP] Hardware graphics dashboard rendering frames successfully.");
            } catch (IOException e) {
                System.err.println("[LAUNCH FAULT] Socket channel binding error: " + e.getMessage());
            }
        });
    }
}
