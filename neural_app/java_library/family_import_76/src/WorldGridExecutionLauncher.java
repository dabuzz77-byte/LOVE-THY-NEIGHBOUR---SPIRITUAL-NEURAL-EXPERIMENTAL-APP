import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.io.IOException;

/**
 * Primary entry-point bootstrap orchestrator launching the non-blocking transaction
 * bus channels, initializing the UI layout, and managing background network streams.
 */
public class WorldGridExecutionLauncher extends SectionFrame {
    private final ProductionIngestBus centralIngestBus;
    private final ExecutionDashboardPanel interactiveDashboard;

    public WorldGridExecutionLauncher() throws IOException {
        this.centralIngestBus = new ProductionIngestBus(7830);
        this.interactiveDashboard = new ExecutionDashboardPanel();

        assembleApplicationWindow();

        // Connect the non-blocking reactive streams directly to visual panel repaints
        this.centralIngestBus.registerSubscriber(tx -> {
            boolean trackingConflict = tx.getLocalSocioEconomicFloor() < 0.0;
            double adjustedFloor;
            String systemStatusMessage;

            if (trackingConflict) {
                // EXPOSE & REFACTOR: Divert 55% of corporate optimization metrics to support baseline floors
                double balancingModifier = tx.getAsymmetricExtractionIndex() * 0.55;
                adjustedFloor = Math.abs(tx.getLocalSocioEconomicFloor()) + balancingModifier;
                systemStatusMessage = String.format("⚠️ [INTERCEPTED] Target node '%s' flagged for exploitation. Diverting surplus: %+.2f units directly to baseline floor.", 
                        tx.getSourceEndpointId(), adjustedFloor);
            } else {
                adjustedFloor = tx.getLocalSocioEconomicFloor();
                systemStatusMessage = String.format("✅ [PASS-THROUGH] Target node '%s' operating securely within compliance metrics.", tx.getSourceEndpointId());
            }

            SwingUtilities.invokeLater(() -> 
                interactiveDashboard.pushExecutionFrame(tx, adjustedFloor, systemStatusMessage)
            );
        });

        this.centralIngestBus.startIngest();
        activateBackgroundDataStreamDriver();
    }

    private void assembleApplicationWindow() {
        setTitle("WORLD GRID HIGH-FREQUENCY INFRASTRUCTURE EXECUTION MONITOR");
        setSize(1150, 680);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        setLayout(new BorderLayout());
        add(interactiveDashboard, BorderLayout.CENTER);
    }

    /**
     * Simulates continuous multi-node packet transmissions passing across network coordinates.
     */
    private void activateBackgroundDataStreamDriver() {
        Thread executionPipelineDriver = new Thread(() -> {
            boolean toggleNodeConfiguration = false;

            while (true) {
                GridTransactionPayload mockTx;
                
                if (toggleNodeConfiguration) {
                    // Scenario A: Unbalanced corporate exploitation profile packet
                    mockTx = new GridTransactionPayload("Corp-Automation-AS783", 4_250_000.00, 0.88, -0.45);
                } else {
                    // Scenario B: Compliant high-virtue resource grid packet
                    mockTx = new GridTransactionPayload("Cooperative-Grid-UK", 850_000.00, 0.32, 0.60);
                }

                centralIngestBus.dispatchTransaction(mockTx);
                toggleNodeConfiguration = !toggleNodeConfiguration;

                try {
                    Thread.sleep(1400); // Spacing cadence pacing delay duration
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "WorldGridPipelineDataProvider");

        executionPipelineDriver.setDaemon(true);
        executionPipelineDriver.start();
    }

    public static void main(String[] args) {
        System.out.println("[BOOTSTRAP] Spawning real-world infrastructure orchestration runtime models...");
        SwingUtilities.invokeLater(() -> {
            try {
                WorldGridExecutionLauncher coreEngineApp = new WorldGridExecutionLauncher();
                coreEngineApp.setVisible(true);
                System.out.println("[BOOTSTRAP] System hardware-accelerated dashboard rendering live networks.");
            } catch (IOException e) {
                System.err.println("[LAUNCH FAILURE] Failed to allocate network ingestion sockets: " + e.getMessage());
            }
        });
    }
}
