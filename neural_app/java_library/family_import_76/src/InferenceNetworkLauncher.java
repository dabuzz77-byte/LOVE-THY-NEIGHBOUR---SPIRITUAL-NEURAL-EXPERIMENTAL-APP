import neural.studio.*;
import javax.swing.SwingUtilities;

/**
 * Bootstrap entry layer deploying the entire distributed inference topography infrastructure.
 */
public class InferenceNetworkLauncher {
    public static void main(String[] args) {
        System.out.println("[BOOTSTRAP] Spawning network topology registers...");

        NetworkTopology topologyLayout = new NetworkTopology();
        InferenceBridgeEngine coreBridge = new InferenceBridgeEngine(topologyLayout);

        // Engage async core stream pipelines
        coreBridge.startBridge();

        // Spin GUI rendering thread
        SwingUtilities.invokeLater(() -> {
            NetworkTopographyTerminal terminal = new NetworkTopographyTerminal(coreBridge);
            terminal.setVisible(true);
            System.out.println("[BOOTSTRAP] Graphic monitor screen activated.");
        });

        // Safe pipeline resource drain handler hooks on shutdown
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("[SHUTDOWN] Exiting runtime context. Draining background threads cleanly.");
            coreBridge.stopBridge();
        }));
    }
}
