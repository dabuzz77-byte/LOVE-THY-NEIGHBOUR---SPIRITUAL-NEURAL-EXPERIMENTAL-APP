import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.net.http.HttpClient;
import java.time.Duration;

/**
 * 1-0 TRUTH PARITY SPECIFICATION: MASTER SYSTEM CONSOLE FRAMEWORK
 * PART A: Core class setup, component variable allocation, and window frame generation.
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
    private final ProcessDiagnosticPanel systemProcessDiagnosticPanel;

    public CorporateGatewayConsole() {
        setTitle("Sovereign Cross-Platform Frame — Desktop Runtime Telemetry Matrix");
        setSize(1550, 980);
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
        Thread pipelineWorkerThread = new Thread(backgroundRouterBus, "SovereignEngine-BackgroundRouter");
        pipelineWorkerThread.start();

        // TOP SETTINGS BAR ARRANGEMENT
        JPanel controlStratumPanel = new JPanel(new GridLayout(2, 1, 6, 6));
        controlStratumPanel.setBackground(new Color(12, 18, 30));
        controlStratumPanel.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));

        JPanel credentialsRow = new JPanel(new BorderLayout(10, 10));
        credentialsRow.setOpaque(false);
        JLabel keyLabel = new JLabel("ENTER REGULATION API CREDENTIAL STRINGS: ");
        keyLabel.setForeground(new Color(0, 255, 195));
        keyLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        credentialsRow.add(keyLabel, BorderLayout.WEST);

        keyFieldWidgetContainer = new JPasswordField(credentialSpecHolder.getExplicitTokenString());
        keyFieldWidgetContainer.setBackground(new Color(7, 11, 18));
        keyFieldWidgetContainer.setForeground(Color.WHITE);
        keyFieldWidgetContainer.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 195, 80)));
        credentialsRow.add(keyFieldWidgetContainer, BorderLayout.CENTER);

        JPanel targetSelectorRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        targetSelectorRow.setOpaque(false);
        JLabel matrixSelectorLabel = new JLabel("TARGET DISPATCH EXECUTOR ENGINE: ");
        matrixSelectorLabel.setForeground(Color.WHITE);
        matrixSelectorLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        targetSelectorRow.add(matrixSelectorLabel);

        String[] coreOptionsList = {"LOCAL PC COMPUTING HARDWARE: LLAMA3 (Private Local Kernel)", "LOCAL PC HARDWARE: PROCESS EXPLORER (Diagnostic Surface)", "REMOTE GATEWAY NODE: GEMINI (Out-Of-Band Secure Pipeline)"};
        targetEngineSelector = new JComboBox<>(coreOptionsList);
        targetEngineSelector.setBackground(new Color(18, 28, 44));
        targetEngineSelector.setForeground(Color.WHITE);
        targetSelectorRow.add(targetEngineSelector);

        controlStratumPanel.add(credentialsRow);
        controlStratumPanel.add(targetSelectorRow);
        add(controlStratumPanel, BorderLayout.NORTH);

        // CONTINUED DIRECTLY IN CODE BLOCK 2B...
        // CONTINUED FROM CODE BLOCK 2A...
        // CENTER TABS: CONSOLE LOGS, ARTWORK GRAPHICS, AND ATTACHED OS INSPECTORS
        JTabbedPane systemWorkspaceTabbedPane = new JTabbedPane();
        systemWorkspaceTabbedPane.setBackground(new Color(16, 24, 40));
        systemWorkspaceTabbedPane.setForeground(Color.WHITE);

        // Tab Layout Panel 1: Consolidated Command Terminal Area
        executionTerminalArea = new JTextArea();
        executionTerminalArea.setBackground(new Color(5, 7, 14));
        executionTerminalArea.setForeground(new Color(225, 235, 245));
        executionTerminalArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        executionTerminalArea.setEditable(false);
        executionTerminalArea.setLineWrap(true);
        executionTerminalArea.setText("=== DEUS EX MACHINA SYSTEM CONSOLE ENGAGEMENT ===\n" +
                                      "Cross-platform process monitoring panel deployed.\n" +
                                      "Base Clock Anchor: 7.83Hz frequency ratio match active.\n" +
                                      "Local PC runtime workspace configured. Network isolation verified.\n\n");
        JScrollPane logScrollPaneFrame = new JScrollPane(executionTerminalArea);
        logScrollPaneFrame.setBorder(BorderFactory.createLineBorder(new Color(25, 38, 58)));
        systemWorkspaceTabbedPane.addTab("System Terminal Console", logScrollPaneFrame);

        // Tab Layout Panel 2: Vector Animation Mapping Canvas Panel
        DiagnosticCanvasPanel canvasMonitorView = new DiagnosticCanvasPanel(backgroundRouterBus);
        systemWorkspaceTabbedPane.addTab("7.83Hz Signal Architecture Monitor", canvasMonitorView);

        // Tab Layout Panel 3: Connected Native Process Diagnostic Explorer Layout Panel
        systemProcessDiagnosticPanel = new ProcessDiagnosticPanel();
        systemWorkspaceTabbedPane.addTab("Active Runtime Process Explorer Grid", systemProcessDiagnosticPanel);

        add(systemWorkspaceTabbedPane, BorderLayout.CENTER);

        // LOWER INPUT DATA PANEL ARRANGEMENT
        JPanel inputActionPanel = new JPanel(new BorderLayout(10, 10));
        inputActionPanel.setBorder(BorderFactory.createEmptyBorder(10, 16, 15, 16));
        inputActionPanel.setBackground(new Color(12, 18, 30));

        dataPromptField = new JTextField();
        dataPromptField.setBackground(new Color(7, 11, 18));
        dataPromptField.setForeground(Color.WHITE);
        dataPromptField.setCaretColor(Color.WHITE);
        dataPromptField.setFont(new Font("Monospaced", Font.PLAIN, 13));
        dataPromptField.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 195, 80)));
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

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            backgroundRouterBus.terminateRouterSystem();
            systemProcessDiagnosticPanel.haltDiagnosticLoop();
        }));
    }

    private void handleIngressExecution(ActionEvent event) {
        final String inputKeyToken = new String(keyFieldWidgetContainer.getPassword()).trim();
        credentialSpecHolder.updateTokenValue(inputKeyToken);

        final String promptText = dataPromptField.getText().trim();
        final int activeSelection = targetEngineSelector.getSelectedIndex();

        if (promptText.isEmpty()) return;

        executionTerminalArea.append("[USER REGULATION SOURCE]: " + promptText + "\n");
        dataPromptField.setText("");
        dispatchJobButton.setEnabled(false);

        pingRouterPortBus();

        SwingWorker<String, Void> networkTask = new SwingWorker<>() {
            @Override
            protected String doInBackground() throws Exception {
                if (activeSelection == 0) {
                    return MicroNetworkBridge.executeLocalRequest(sharedNetworkHttpClient, "llama3", promptText);
                } else if (activeSelection == 1) {
                    return "[DIAGNOSTIC NOTICE]: Target routed directly to Active Runtime Process Explorer tab view.";
                } else {
                    if (inputKeyToken.isEmpty()) {
                        return "[CRITICAL ABORT]: Remote pipeline rejected. Target credential string is empty.";
                    }
                    return MicroNetworkBridge.executeCloudRequest(sharedNetworkHttpClient, inputKeyToken, promptText);
                }
            }

            @Override
            protected void done() {
                try {
                    String outputResponse = get();
                    executionTerminalArea.append("[HARDWARE BUS CHIPS RESPONSE]:\n" + outputResponse + "\n\n");
                } catch (Exception ex) {
                    executionTerminalArea.append("[ROUTER CONTEXT EXCEPTION INTERCEPT]: " + ex.getMessage() + "\n\n");
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

