import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.net.http.HttpClient;
import java.time.Duration;

/**
 * PARALLEL BUS PROTOCOL: MASTER SYSTEM MONITORING DASHBOARD
 * Assembles the integrated network and graphic modules into an execution workspace.
 */
public class CorporateGatewayConsole extends JFrame {

    private final JPasswordField keyFieldWidgetContainer;
    private final JTextField dataPromptField;
    private final JTextArea executionTerminalArea;
    private final JComboBox<String> targetEngineSelector;
    private final JButton dispatchJobButton;

    private final HttpClient sharedNetworkHttpClient;
    private final LocalSilentRouter backgroundRouterBus;
    private final SecureCredentialSpec credentialSpecHolder;
    private final Timer canvasRedrawTimer;

    public CorporateGatewayConsole() {
        setTitle("System Control Dashboard — Parallel Processing Bus Interface");
        setSize(1450, 960);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        this.sharedNetworkHttpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(15))
                .build();

        String hostEnvironmentKey = System.getenv("GEMINI_API_KEY");
        this.credentialSpecHolder = new SecureCredentialSpec(hostEnvironmentKey != null ? hostEnvironmentKey : "");

        this.backgroundRouterBus = new LocalSilentRouter();
        Thread pipelineWorkerThread = new Thread(backgroundRouterBus, "ParallelBus-BackgroundRouter-Thread");
        pipelineWorkerThread.start();

        // 1. TOP SETTINGS PANEL
        JPanel controlStratumPanel = new JPanel(new GridLayout(2, 1, 6, 6));
        controlStratumPanel.setBackground(new Color(12, 18, 28));
        controlStratumPanel.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));

        JPanel credentialsRow = new JPanel(new BorderLayout(10, 10));
        credentialsRow.setOpaque(false);
        JLabel keyLabel = new JLabel("ENTER TARGET PLATFORM API CREDENTIAL KEY: ");
        keyLabel.setForeground(new Color(0, 255, 190));
        keyLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        credentialsRow.add(keyLabel, BorderLayout.WEST);

        keyFieldWidgetContainer = new JPasswordField(credentialSpecHolder.getExplicitTokenString());
        keyFieldWidgetContainer.setBackground(new Color(6, 10, 16));
        keyFieldWidgetContainer.setForeground(Color.WHITE);
        keyFieldWidgetContainer.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        credentialsRow.add(keyFieldWidgetContainer, BorderLayout.CENTER);

        JPanel targetSelectorRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        targetSelectorRow.setOpaque(false);
        JLabel matrixSelectorLabel = new JLabel("SELECT COGNITIVE CORES INFERENCE ENGINE: ");
        matrixSelectorLabel.setForeground(Color.WHITE);
        matrixSelectorLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        targetSelectorRow.add(matrixSelectorLabel);

        String[] coreOptionsList = {"LOCAL PC HARDWARE: LLAMA3 (Offline System Core)", "LOCAL PC HARDWARE: FLUX (Isolated Canvas Model)", "REMOTE GATEWAY CORE: GEMINI (Cloud Processing Lane)"};
        targetEngineSelector = new JComboBox<>(coreOptionsList);
        targetEngineSelector.setBackground(new Color(16, 26, 42));
        targetEngineSelector.setForeground(Color.WHITE);
        targetSelectorRow.add(targetEngineSelector);

        controlStratumPanel.add(credentialsRow);
        controlStratumPanel.add(targetSelectorRow);
        add(controlStratumPanel, BorderLayout.NORTH);

        // 2. CENTER PANEL: VIEWPORTS
        JPanel displaySplitGridPanel = new JPanel(new GridLayout(1, 2, 10, 10));
        displaySplitGridPanel.setBorder(BorderFactory.createEmptyBorder(5, 16, 5, 16));
        displaySplitGridPanel.setBackground(new Color(2, 4, 8));

        executionTerminalArea = new JTextArea();
        executionTerminalArea.setBackground(new Color(4, 6, 12));
        executionTerminalArea.setForeground(new Color(225, 235, 245));
        executionTerminalArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        executionTerminalArea.setEditable(false);
        executionTerminalArea.setLineWrap(true);
        executionTerminalArea.setWrapStyleWord(true);
        executionTerminalArea.setText("=== PARALLEL PROCESS MATRIX INITIALIZED ===\n" +
                                      "All standalone processing activities aligned into a singular execution bus.\n" +
                                      "Local loopback endpoint assigned: http://localhost:11434 [Ollama Module Loaded]\n" +
                                      "Remote verification layer: Zero-Trust Cryptographic Validation [TLS 1.3 Path]\n\n");

        JScrollPane logScrollPaneFrame = new JScrollPane(executionTerminalArea);
        logScrollPaneFrame.setBorder(BorderFactory.createLineBorder(new Color(25, 35, 55)));
        displaySplitGridPanel.add(logScrollPaneFrame);

        DiagnosticCanvasPanel canvasMonitorView = new DiagnosticCanvasPanel(backgroundRouterBus);
        displaySplitGridPanel.add(canvasMonitorView);
        add(displaySplitGridPanel, BorderLayout.CENTER);

        // 3. LOWER PANEL: INPUT
        JPanel inputActionPanel = new JPanel(new BorderLayout(10, 10));
        inputActionPanel.setBorder(BorderFactory.createEmptyBorder(10, 16, 15, 16));
        inputActionPanel.setBackground(new Color(12, 18, 28));

        dataPromptField = new JTextField();
        dataPromptField.setBackground(new Color(6, 10, 16));
        dataPromptField.setForeground(Color.WHITE);
        dataPromptField.setCaretColor(Color.WHITE);
        dataPromptField.setFont(new Font("Monospaced", Font.PLAIN, 13));
        dataPromptField.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        inputActionPanel.add(dataPromptField, BorderLayout.CENTER);

        dispatchJobButton = new JButton("DISPATCH VECTOR");
        dispatchJobButton.setBackground(new Color(0, 140, 255));
        dispatchJobButton.setForeground(Color.WHITE);
        dispatchJobButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        dispatchJobButton.setFocusPainted(false);
        inputActionPanel.add(dispatchJobButton, BorderLayout.EAST);

        add(inputActionPanel, BorderLayout.SOUTH);

        dispatchJobButton.addActionListener(this::handleIngressExecution);
        dataPromptField.addActionListener(this::handleIngressExecution);

        this.canvasRedrawTimer = new Timer(32, e -> repaint());
        this.canvasRedrawTimer.start();

        Runtime.getRuntime().addShutdownHook(new Thread(backgroundRouterBus::terminateRouterSystem));
    }

    private void handleIngressExecution(ActionEvent event) {
        final String inputKeyToken = new String(keyFieldWidgetContainer.getPassword()).trim();
        credentialSpecHolder.updateTokenValue(inputKeyToken);

        final String promptText = dataPromptField.getText().trim();
        final int activeSelection = targetEngineSelector.getSelectedIndex();

        if (promptText.isEmpty()) return;

        executionTerminalArea.append("[USER BUS INPUT]: " + promptText + "\n");
        dataPromptField.setText("");
        dispatchJobButton.setEnabled(false);

        pingRouterPortBus();

        SwingWorker<String, Void> networkTask = new SwingWorker<>() {
            @Override
            protected String doInBackground() throws Exception {
                if (activeSelection == 0) {
                    return MicroNetworkBridge.executeLocalRequest(sharedNetworkHttpClient, "llama3", promptText);
                } else if (activeSelection == 1) {
                    return MicroNetworkBridge.executeLocalRequest(sharedNetworkHttpClient, "flux", promptText);
                } else {
                    if (inputKeyToken.isEmpty()) {
                        return "[CRITICAL ABORT]: Remote target rejected. API credential string is missing.";
                    }
                    return MicroNetworkBridge.executeCloudRequest(sharedNetworkHttpClient, inputKeyToken, promptText);
                }
            }

            @Override
            protected void done() {
                try {
                    String outputResponse = get();
                    executionTerminalArea.append("[BUS STREAM RESPONSE]:\n" + outputResponse + "\n\n");
                } catch (Exception ex) {
                    executionTerminalArea.append("[BUS ROUTER FAULT]: " + ex.getMessage() + "\n\n");
                } finally {
                    dispatchJobButton.setEnabled(true);
                    executionTerminalArea.setCaretPosition(executionTerminalArea.getDocument().getLength());
                }
            }
        };
        networkTask.execute();
    }

    private void pingRouterPortBus() {
        int targetLoopbackPort = backgroundRouterBus.getActiveLocalPort();
        if (targetLoopbackPort == -1) return;
        try (java.net.Socket transportSocket = new java.net.Socket("127.0.0.1", targetLoopbackPort);
             java.io.OutputStream outgoingStream = transportSocket.getOutputStream()) {
            outgoingStream.write("PULSE\n".getBytes("UTF-8"));
            outgoingStream.flush();
        } catch (Exception ignored) {}
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            CorporateGatewayConsole app = new CorporateGatewayConsole();
            app.setVisible(true);
        });
    }
}
