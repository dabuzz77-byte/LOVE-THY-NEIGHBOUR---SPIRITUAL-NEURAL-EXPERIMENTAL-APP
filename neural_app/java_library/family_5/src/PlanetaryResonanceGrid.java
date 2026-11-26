import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.time.Duration;
import java.util.*;
import java.util.List;

public final class PlanetaryResonanceGrid {
    public static void main(String[] args) {
        if (args.length == 1 && args[0].equals("--self-test")) { System.exit(selfTest()); return; }
        if (args.length > 0) { System.err.println("Usage: run.bat [--self-test]"); System.exit(2); }
        if (GraphicsEnvironment.isHeadless()) { System.err.println("A desktop is required. Use --self-test for the local HTTP check."); System.exit(2); }
        SwingUtilities.invokeLater(() -> {
            GridEngine engine = new GridEngine();
            try {
                UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName());
                ResonanceDashboard dashboard = new ResonanceDashboard(engine);
                SectionFrame frame = new SectionFrame("Planetary Resonance | HTTP Dispatch Observatory");
                frame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE); frame.setContentPane(dashboard);
                Rectangle desktop = new Rectangle(0,0,1440,900);
                frame.setMinimumSize(new Dimension(Math.min(1150, desktop.width), Math.min(790, desktop.height)));
                frame.pack(); frame.setSize(Math.min(frame.getWidth(), desktop.width), Math.min(frame.getHeight(), desktop.height));
                frame.setLocationRelativeTo(null); frame.addWindowListener(new WindowAdapter() {
                    @Override public void windowClosed(WindowEvent event) { dashboard.close(); }
                });
                frame.setVisible(true);
            } catch (Exception failure) { engine.close(); SectionDialogs.showMessageDialog(null, failure.getMessage(), "Unable to start", JOptionPane.ERROR_MESSAGE); }
        });
    }

    /** Legacy caller support requires explicit URLs in -Dplanetary.endpoints=url1,url2. */
    @Deprecated
    public static void detonateGlobalRunall(String signature, String telemetry) {
        String configured = System.getProperty("planetary.endpoints", "");
        if (configured.isBlank()) throw new IllegalStateException("No destinations configured. Set -Dplanetary.endpoints to explicit HTTP(S) URLs, or use the graphical interface.");
        List<Endpoint> endpoints = new ArrayList<>();
        for (String url : configured.split(",")) endpoints.add(Endpoint.create("Endpoint " + (endpoints.size() + 1), url));
        try (GridEngine engine = new GridEngine()) {
            engine.configure(endpoints); engine.dispatch(new DispatchPayload(142857, signature, telemetry), Duration.ofSeconds(5), 4);
            if (!engine.awaitIdle(Duration.ofSeconds(40))) throw new IllegalStateException("Dispatch did not complete.");
            engine.snapshot().nodes().forEach(result -> System.out.println(result.endpoint().name() + ": " + result.state() + " · " + result.detail()));
        } catch (InterruptedException failure) { Thread.currentThread().interrupt(); throw new IllegalStateException("Dispatch interrupted", failure); }
    }

    private static int selfTest() {
        try (LocalTestServer server = new LocalTestServer(); GridEngine engine = new GridEngine()) {
            engine.configure(server.endpoints());
            engine.dispatch(new DispatchPayload(142857, "local-self-test", "Actual loopback HTTP request"), Duration.ofSeconds(5), 3);
            if (!engine.awaitIdle(Duration.ofSeconds(10))) throw new IllegalStateException("Self-test did not complete.");
            GridEngine.Snapshot snapshot = engine.snapshot();
            snapshot.nodes().forEach(result -> System.out.printf(Locale.ROOT, "%s: %s, HTTP %d, %.0f ms%n", result.endpoint().name(), result.state(), result.code(), result.latencyMs()));
            if (snapshot.succeeded() != 2 || snapshot.completed() != 3 || server.requests.get() != 3)
                throw new IllegalStateException("Unexpected local test outcome.");
            System.out.println("PASS: 3 real local HTTP requests; 200 and 202 accepted, intentional 503 recorded as an error."); return 0;
        } catch (Exception failure) { System.err.println("Self-test failed: " + failure.getMessage()); return 1; }
    }
}
