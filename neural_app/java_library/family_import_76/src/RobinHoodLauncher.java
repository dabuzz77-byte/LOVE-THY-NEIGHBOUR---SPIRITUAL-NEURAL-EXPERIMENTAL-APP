import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.io.IOException;

/**
 * Main application bootstrap layer assembling windows, initializing routing buses, 
 * and spinning detached transaction delivery task drivers.
 */
public class RobinHoodLauncher extends SectionFrame {
    private final RobinHoodCircuitBreaker interceptorBus;
    private final VirtueMonitorPanel viewPanel;

    public RobinHoodLauncher() throws IOException {
        this.interceptorBus = new RobinHoodCircuitBreaker(7830);
        this.viewPanel = new VirtueMonitorPanel();

        buildWindowLayout();

        // Direct-wire the async event signals straight into UI thread paint refreshes
        this.interceptorBus.registerAuditListener(logLine -> {
            long totalReallocated = interceptorBus.getGloballyReallocatedCapital();
            SwingUtilities.invokeLater(() -> viewPanel.pushLogEntry(logLine, totalReallocated));
        });

        this.interceptorBus.startEnforcementLoop();
        igniteLiveTransactionStream();
    }

    private void buildWindowLayout() {
        setTitle("ROBIN HOOD GRID EXECUTION CONTROLLER // SOULS OVER DIGITS ENGINE");
        setSize(1100, 600);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        setLayout(new BorderLayout());
        add(viewPanel, BorderLayout.CENTER);
    }

    /**
     * Drives continuous data ingestion events into the transaction layers,
     * alternating between compliant models and exploitative corporate footprints.
     */
    private void igniteLiveTransactionStream() {
        Thread infrastructureDriver = new Thread(() -> {
            boolean toggleState = false;

            while (true) {
                AssetTransaction packet;
                if (toggleState) {
                    // Scenario A: Exploitative corporate profile (High concentration profit paired with sub-zero floor degradation)
                    packet = new AssetTransaction("Asymmetric-Automation-Hub", 3_500_000.00, 0.92, -0.65);
                } else {
                    // Scenario B: Compliant high-virtue resource layout (Balanced yield with constructive base floor impact)
                    packet = new AssetTransaction("Cooperative-Wage-Pool-UK", 420_000.00, 0.15, 0.45);
                }

                interceptorBus.processTransaction(packet);
                toggleState = !toggleState;

                try {
                    Thread.sleep(1300); // Transmission loop pacing duration step
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "GridTransactionStreamDriver");

        infrastructureDriver.setDaemon(true);
        infrastructureDriver.start();
    }

    public static void main(String[] args) {
        System.out.println("[BOOTSTRAP] Compiling production virtue audit controllers...");
        SwingUtilities.invokeLater(() -> {
            try {
                RobinHoodLauncher application = new RobinHoodLauncher();
                application.setVisible(true);
                System.out.println("[BOOTSTRAP] Hardware-accelerated UI rendering active.");
            } catch (IOException e) {
                System.err.println("[LAUNCH FAULT] Critical network infrastructure allocation blocked: " + e.getMessage());
            }
        });
    }
}
