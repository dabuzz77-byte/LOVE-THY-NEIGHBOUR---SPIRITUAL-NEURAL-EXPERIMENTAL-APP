import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * PARALLEL HANDSHAKE SPECIFICATION: MASTER USER INTERFACE FRAME
 * Renders automated diagnostic status trackers and handles user prompt inputs.
 */
public class ParallelHandshakeApp extends JFrame {

    private final JTextArea diagnosticTerminalLog;
    private final JTextField userPromptInput;
    private final JButton executeJobButton;
    private final JProgressBar localLatencyIndicator;
    private final JProgressBar remoteLatencyIndicator;

    private final HttpClient sharedNetworkHttpClient;
    private final CopyOnWriteArrayList<InferenceBeaconUnit> activeTelemetryBeacons;
    private final ScheduledExecutorService telemetryScheduler;

    public ParallelHandshakeApp() {
        setTitle("Parallel Handshake System Console — Async Inference Beacon Monitor");
        setSize(1400, 900);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(12, 12));

        this.activeTelemetryBeacons = new CopyOnWriteArrayList<>();
        
        this.sharedNetworkHttpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        // 1. TOP LAYOUT PANEL: GRAPHICAL METRICS DISPLAY
        JPanel metricsDisplayPanel = new JPanel(new GridLayout(1, 2, 16, 16));
        metricsDisplayPanel.setBackground(new Color(12, 18, 28));
        metricsDisplayPanel.setBorder(BorderFactory.createEmptyBorder(14, 16, 14, 16));

        JPanel localMetricBox = new JPanel(new BorderLayout(5, 5));
        localMetricBox.setOpaque(false);
        JLabel localLabel = new JLabel("LOCAL OLLAMA INTERCEPT DEPTH LATENCY:");
        localLabel.setForeground(new Color(0, 255, 190));
        localLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        localLatencyIndicator = new JProgressBar(0, 200);
        localLatencyIndicator.setStringPainted(true);
        localMetricBox.add(localLabel, BorderLayout.NORTH);
        localMetricBox.add(localLatencyIndicator, BorderLayout.CENTER);

        JPanel remoteMetricBox = new JPanel(new BorderLayout(5, 5));
        remoteMetricBox.setOpaque(false);
        JLabel remoteLabel = new JLabel("REMOTE SUBSYSTEM GOOGLE CLOUD GATEWAY RTT:");
        remoteLabel.setForeground(new Color(0, 150, 255));
        remoteLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        remoteLatencyIndicator = new JProgressBar(0, 1000);
        remoteLatencyIndicator.setStringPainted(true);
        remoteMetricBox.add(remoteLabel, BorderLayout.NORTH);
        remoteMetricBox.add(remoteLatencyIndicator, BorderLayout.CENTER);

        metricsDisplayPanel.add(localMetricBox);
        metricsDisplayPanel.add(remoteMetricBox);
        add(metricsDisplayPanel, BorderLayout.NORTH);

        // 2. CENTER LAYOUT PANEL: LOG AREA
        diagnosticTerminalLog = new JTextArea();
        diagnosticTerminalLog.setBackground(new Color(4, 6, 12));
        diagnosticTerminalLog.setForeground(new Color(215, 230, 245));
        diagnosticTerminalLog.setFont(new Font("Monospaced", Font.PLAIN, 12));
        diagnosticTerminalLog.setEditable(false);
        diagnosticTerminalLog.setLineWrap(true);
        diagnosticTerminalLog.setText("=== PARALLEL HANDSHAKE INFERENCE BEACON NETWORK RUNNING ===\n" +
                                      "Background scheduler activated: Processing loopback checks at 7.83Hz baseline intervals.\n" +
                                      "Two-block splitting applied cleanly to the main UI cockpit dashboard frame.\n\n");

        JScrollPane logScrollPane = new JScrollPane(diagnosticTerminalLog);
        logScrollPane.setBorder(BorderFactory.createLineBorder(new Color(25, 35, 55)));
        add(logScrollPane, BorderLayout.CENTER);

        // 3. LOWER LAYOUT PANEL: ACTION INPUT BAR
        JPanel actionEntryPanel = new JPanel(new BorderLayout(10, 10));
        actionEntryPanel.setBackground(new Color(12, 18, 28));
        actionEntryPanel.setBorder(BorderFactory.createEmptyBorder(10, 16, 15, 16));

        userPromptInput = new JTextField();
        userPromptInput.setBackground(new Color(6, 10, 16));
        userPromptInput.setForeground(Color.WHITE);
        userPromptInput.setCaretColor(Color.WHITE);
        userPromptInput.setFont(new Font("Monospaced", Font.PLAIN, 13));
        userPromptInput.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        actionEntryPanel.add(userPromptInput, BorderLayout.CENTER);

        executeJobButton = new JButton("DISPATCH TELEMETRY FORCE");
        executeJobButton.setBackground(new Color(0, 140, 255));
        executeJobButton.setForeground(Color.WHITE);
        executeJobButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        executeJobButton.setFocusPainted(false);
        actionEntryPanel.add(executeJobButton, BorderLayout.EAST);

        add(actionEntryPanel, BorderLayout.SOUTH);

        executeJobButton.addActionListener(this::triggerManualTelemetryPulse);
        userPromptInput.addActionListener(this::triggerManualTelemetryPulse);

        this.telemetryScheduler = Executors.newSingleThreadScheduledExecutor(runnable -> {
            Thread daemonWorker = new Thread(runnable, "Telemetry-Beacon-Daemon");
            daemonWorker.setDaemon(true);
            return daemonWorker;
        });
        
        this.telemetryScheduler.scheduleAtFixedRate(this::triggerTrackingPassRoutine, 2, 3, TimeUnit.SECONDS);
    }

    private void triggerManualTelemetryPulse(ActionEvent event) {
        String promptString = userPromptInput.getText().trim();
        if (promptString.isEmpty()) return;

        diagnosticTerminalLog.append("[MANUAL TARGET TRACE]: Checking tracking vector for token: '" + promptString + "'\n");
        userPromptInput.setText("");
        Executors.newSingleThreadExecutor().execute(this::triggerTrackingPassRoutine);
    }

    private void triggerTrackingPassRoutine() {
        TelemetryCarrierEngine.runAsynchronousTrackingPass(
            sharedNetworkHttpClient, 
            activeTelemetryBeacons, 
            (localMs, remoteMs) -> SwingUtilities.invokeLater(() -> updateUserInterfaceIndicators(localMs, remoteMs))
        );
    }

    private void updateUserInterfaceIndicators(double localMillis, double remoteMillis) {
        localLatencyIndicator.setValue((int) localMillis);
        localLatencyIndicator.setString(String.format("%.1f ms", localMillis));
        
        remoteLatencyIndicator.setValue((int) remoteMillis);
        remoteLatencyIndicator.setString(String.format("%.1f ms", remoteMillis));

        diagnosticTerminalLog.append(String.format(
                "[BEACON TICK] Telemetry check complete -> Local Ingress: %.1fms | Remote Cloud Gate: %.1fms\n",
                localMillis, remoteMillis
        ));
        
        if (activeTelemetryBeacons.size() > 40) {
            activeTelemetryBeacons.remove(0);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            ParallelHandshakeApp masterApplication = new ParallelHandshakeApp();
            masterApplication.setVisible(true);
        });
    }
}
