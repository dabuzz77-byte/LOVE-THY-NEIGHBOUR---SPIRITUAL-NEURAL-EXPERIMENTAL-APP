import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.concurrent.ExecutionException;

/** Desktop entry point for the LAN telemetry dashboard. Requires Java 17 or newer. */
@SuppressWarnings("serial") // Swing views are never serialized.
public final class LANCoordinatorEngine extends SectionFrame {
    private static final long serialVersionUID = 1L;
    private final QuantumTernaryBinaryCore core = new QuantumTernaryBinaryCore(6, 0.40);
    private final LocalNetworkLatchingEngine network = new LocalNetworkLatchingEngine();
    private final HardwareMetricSampler sampler = new HardwareMetricSampler(core);
    private final LANMatrixCanvas dashboard = new LANMatrixCanvas(core, network);
    private final SharedTimer refreshClock;
    private final JButton receiverButton = new JButton("Starting...");
    private boolean closing;

    public LANCoordinatorEngine() {
        super("LAN Observatory | Android & iOS telemetry");
        setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        setMinimumSize(new Dimension(1080, 800));
        setSize(1420, 940);
        setLocationRelativeTo(null);
        dashboard.addAction(receiverButton);
        JButton connect = new JButton("Connect a device");
        JButton export = new JButton("Export CSV");
        dashboard.addAction(connect);
        dashboard.addAction(export);
        receiverButton.addActionListener(event -> toggleReceiver());
        connect.addActionListener(event -> showConnectionGuide());
        export.addActionListener(event -> exportSnapshot());
        add(dashboard);
        refreshClock = new SharedTimer(1000, event -> {
            dashboard.refresh(sampler.getLatest());
            if (receiverButton.isEnabled()) receiverButton.setText(network.isRunning() ? "Stop receiver" : "Start receiver");
        });
        refreshClock.start();
        addWindowListener(new WindowAdapter() {
            @Override public void windowClosed(WindowEvent event) { shutdown(); }
        });
        receiverButton.setEnabled(true); receiverButton.setText("Start receiver");
    }

    private void toggleReceiver() {
        receiverButton.setEnabled(false);
        receiverButton.setText(network.isRunning() ? "Stopping..." : "Starting...");
        new SharedSwingWorker<Void, Void>() {
            @Override protected Void doInBackground() {
                if (network.isRunning()) network.stopEngine();
                else network.startEngine();
                return null;
            }
            @Override protected void done() {
                if (closing) { network.stopEngine(); return; }
                try { get(); }
                catch (InterruptedException ex) { Thread.currentThread().interrupt(); }
                catch (ExecutionException ex) {
                    SectionDialogs.showMessageDialog(LANCoordinatorEngine.this, ex.getCause().toString(),
                            "Receiver error", JOptionPane.ERROR_MESSAGE);
                }
                receiverButton.setEnabled(true);
                receiverButton.setText(network.isRunning() ? "Stop receiver" : "Start receiver");
                dashboard.refresh(sampler.getLatest());
            }
        }.execute();
    }

    private void showConnectionGuide() {
        JTextArea guide = new JTextArea(
                "Connect your phone and this computer to the same trusted LAN.\n\n" +
                "TCP telemetry port: 19111    UDP discovery port: 19110\n" +
                "Find this computer's LAN IPv4 address in Windows Settings > Network.\n\n" +
                "Send one UTF-8 line, ending in a newline, per TCP connection:\n" +
                "LAN1|ANDROID|my-phone|1.0|0.75|0.5,0.5\n" +
                "Use IOS for an iPhone or iPad. A valid text frame registers the device.\n" +
                "Success reply: OK followed by a newline. Send a frame every 5 seconds.\n\n" +
                "Optional discovery beacon (UDP): GODMIND_BEACON:ANDROID:my-phone\n" +
                "Send to this computer or multicast group 239.255.255.250.\n" +
                "Devices expire after 30 seconds without a valid beacon or telemetry.\n\n" +
                "A compatible client is required; phones are not detected automatically.\n" +
                "The receiver is unauthenticated and unencrypted; use a trusted LAN.\n" +
                "If Windows asks about the firewall, allow private networks only.\n" +
                "See README.md for Android/iOS integration and the full protocol.");
        guide.setEditable(false);
        guide.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        guide.setMargin(new Insets(12, 12, 12, 12));
        guide.setCaretPosition(0);
        SectionDialogs.showMessageDialog(this, new JScrollPane(guide), "Connect a mobile device", JOptionPane.PLAIN_MESSAGE);
    }

    private void exportSnapshot() {
        SectionFileChooser chooser = new SectionFileChooser();
        chooser.setDialogTitle("Export device telemetry");
        chooser.setSelectedFile(new java.io.File("lan-telemetry.csv"));
        if (chooser.showSaveDialog(this) != SectionFileChooser.APPROVE_OPTION) return;
        Path file = chooser.getSelectedFile().toPath();
        if (Files.exists(file) && SectionDialogs.showConfirmDialog(this, "Replace " + file.getFileName() + "?",
                "Replace file", JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return;
        String csv = TelemetryExport.toCsv(network.getLatchedDevices().values());
        new SharedSwingWorker<Void, Void>() {
            @Override protected Void doInBackground() throws IOException {
                Files.writeString(file, csv, StandardCharsets.UTF_8);
                return null;
            }
            @Override protected void done() {
                try {
                    get();
                    SectionDialogs.showMessageDialog(LANCoordinatorEngine.this, "Saved " + file, "Export complete",
                            JOptionPane.INFORMATION_MESSAGE);
                } catch (InterruptedException ex) { Thread.currentThread().interrupt(); }
                catch (ExecutionException ex) {
                    SectionDialogs.showMessageDialog(LANCoordinatorEngine.this, "Could not save: " + ex.getCause().getMessage(),
                            "Export failed", JOptionPane.ERROR_MESSAGE);
                }
            }
        }.execute();
    }

    private void shutdown() {
        if (closing) return;
        closing = true;
        refreshClock.stop();
        sampler.close();
        network.close();
    }
    @Override public void dispose() { shutdown(); super.dispose(); }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); }
            catch (ReflectiveOperationException | UnsupportedLookAndFeelException ignored) { }
            LANMatrixCanvas.configureTheme();
            new LANCoordinatorEngine().setVisible(true);
        });
    }
}

