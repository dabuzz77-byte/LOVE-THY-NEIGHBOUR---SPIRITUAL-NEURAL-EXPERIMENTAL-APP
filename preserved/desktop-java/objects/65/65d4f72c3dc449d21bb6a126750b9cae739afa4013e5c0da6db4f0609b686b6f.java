import javax.swing.SwingUtilities;

/**
 * Central Bootstrap Entry class activating the World Grid monitoring subsystem natively.
 */
public class WorldGridMainLauncher {
    public static void main(String[] args) {
        System.out.println("[SYSTEM INIT] Launching World Grid Telemetry Ingestion Layer...");

        // Instantiate core asynchronous runtime engine
        WorldGridEngine engine = new WorldGridEngine();

        // Spin background data processing threads
        engine.startMonitoring();

        // Safely initialize graphic canvas layout over the system event queue
        SwingUtilities.invokeLater(() -> {
            WorldGridDashboard monitoringApp = new WorldGridDashboard(engine);
            monitoringApp.setVisible(true);
            System.out.println("[UI COMPILING] High-throughput monitor window registered into context.");
        });

        // Add thread shutdown runtime hooks for safe resource drainage
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("[SYSTEM INIT] Intercepting exit signal. Draining grid core threads...");
            engine.shutdownEngine();
        }));
    }
}
