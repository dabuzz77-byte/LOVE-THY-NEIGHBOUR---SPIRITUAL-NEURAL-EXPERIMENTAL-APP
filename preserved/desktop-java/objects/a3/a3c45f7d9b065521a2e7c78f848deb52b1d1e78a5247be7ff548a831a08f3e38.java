import javax.swing.SwingUtilities;

/**
 * Bootstrap ignition point launching the real-time financial monitor application.
 */
public class FinancialSystemLauncher {
    public static void main(String[] args) {
        System.out.println("[BOOTSTRAP] Launching High-Frequency Financial System Grid Core...");

        // Initialize core asynchronous streaming processing engines
        FinancialGridEngine engine = new FinancialGridEngine();
        engine.startIngestionLoop();

        // Spin graphic context canvas display inside the AWT Event Dispatch Thread
        SwingUtilities.invokeLater(() -> {
            FinancialMonitorConsole dashboardFrame = new FinancialMonitorConsole(engine);
            dashboardFrame.setVisible(true);
            System.out.println("[UI FRAMEWORK] Hardware rendering container activated and visible.");
        });

        // Register system shutdown threads to safely clear memory pipelines
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("[SHUTDOWN] Intercepting stop hook. Draining network ingestion streams safely.");
            engine.stopEngine();
        }));
    }
}
