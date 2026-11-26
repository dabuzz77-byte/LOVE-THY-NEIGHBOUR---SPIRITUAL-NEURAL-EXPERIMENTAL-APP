package net.manifold.ui;
import neural.studio.*;


import net.manifold.engine.InferenceNetworkBroadcaster;
import net.manifold.telemetry.NetworkMonitor;
import net.manifold.telemetry.NetworkSnapshot;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

public final class ManifoldGridVisualizer extends SectionFrame {
    private final NetworkDashboard dashboard;
    private final NetworkMonitor monitor;
    private final InferenceNetworkBroadcaster engine;

    public ManifoldGridVisualizer(InferenceNetworkBroadcaster engine) throws java.io.IOException {
        super("Manifold | Live Network Observatory");
        this.engine = engine;
        monitor = new NetworkMonitor(engine);
        dashboard = new NetworkDashboard(engine);
        monitor.addListener(dashboard::accept);
        setContentPane(dashboard); setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        Rectangle desktop = new Rectangle(0,0,1440,900);
        setMinimumSize(new Dimension(Math.min(1100, desktop.width), Math.min(760, desktop.height)));
        pack(); setSize(Math.min(getWidth(), desktop.width), Math.min(getHeight(), desktop.height)); setLocationRelativeTo(null);
        addWindowListener(new WindowAdapter() {
            @Override public void windowClosed(WindowEvent event) { dashboard.close(); monitor.close(); engine.close(); }
        });
        monitor.start();
    }

    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("--diagnose")) { diagnose(); return; }
        if (args.length > 0 && !args[0].equals("--deployment=hybrid-mesh")) {
            System.err.println("Usage: run.bat [--diagnose]"); return;
        }
        if (GraphicsEnvironment.isHeadless()) { System.err.println("A graphical desktop is required. Use --diagnose for a console check."); return; }
        SwingUtilities.invokeLater(() -> {
            InferenceNetworkBroadcaster engine = new InferenceNetworkBroadcaster();
            try {
                UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName());
                UIManager.put("TabbedPane.selected", new Color(30, 50, 62));
                UIManager.put("TabbedPane.background", new Color(17, 26, 38));
                UIManager.put("TabbedPane.foreground", new Color(227, 238, 243));
                new ManifoldGridVisualizer(engine).setVisible(true);
            } catch (Exception failure) {
                engine.close(); SectionDialogs.showMessageDialog(null, failure.getMessage(), "Unable to start Manifold", JOptionPane.ERROR_MESSAGE);
            }
        });
    }

    private static void diagnose() {
        try (InferenceNetworkBroadcaster engine = new InferenceNetworkBroadcaster(); NetworkMonitor monitor = new NetworkMonitor(engine)) {
            java.util.concurrent.CountDownLatch samples = new java.util.concurrent.CountDownLatch(2);
            monitor.addListener(snapshot -> { if (snapshot.sequence() > 0 && snapshot.error().isEmpty()) samples.countDown(); });
            monitor.start();
            boolean ready = samples.await(35, java.util.concurrent.TimeUnit.SECONDS);
            NetworkSnapshot snapshot = monitor.snapshot();
            System.out.println("Source: Windows netstat + .NET interface counters (local observation)");
            System.out.println("Samples: " + snapshot.sequence() + "; TCP rows: " + snapshot.connections().size()
                    + "; established: " + snapshot.establishedCount() + "; apps: " + snapshot.processCount());
            for (var adapter : snapshot.adapters()) System.out.println(adapter.name() + ": down " + NetworkDashboard.rate(adapter.receiveRate())
                    + ", up " + NetworkDashboard.rate(adapter.sendRate()) + ", baseline ready: " + adapter.rateAvailable());
            if (!snapshot.warning().isEmpty()) System.err.println(snapshot.warning());
            if (!ready || !snapshot.error().isEmpty() || !snapshot.tcpAvailable()) {
                System.err.println("Collection incomplete: " + snapshot.error()); System.exit(1);
            }
        } catch (Exception failure) { System.err.println("Diagnostics failed: " + failure.getMessage()); System.exit(1); }
    }
}
