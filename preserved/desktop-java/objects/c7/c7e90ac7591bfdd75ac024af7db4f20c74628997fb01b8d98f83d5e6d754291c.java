import javax.swing.*;
import java.awt.*;
import java.net.http.HttpClient;
import java.time.Duration;

/**
 * MODULE 6c: CENTRAL WINDOW FRAME CONTAINER
 * Boots the decoupled sub-bridges and maps components natively into clean Swing positions.
 */
public class MasterInterfaceApp extends JFrame {

    private final JPasswordField cloudKeyInputField;
    private final JTextField promptInputField;
    private final JTextArea terminalExecutionArea;
    private final JComboBox<String> routeSelectionBox;
    private final JButton dispatchJobButton;
    
    private final HttpClient sharedNetworkHttpClient;
    private final CentralPortRouter asynchronousRouterBus;
    private final LocalOllamaBridge ollamaTransceiver;
    private final GoogleCloudBridge geminiTransceiver;

    public MasterInterfaceApp() {
        setTitle("Sovereign Multi-Model Bridge Console Architecture Array — Granular Layout (_TRUE)");
        setSize(1450, 960);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        this.sharedNetworkHttpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(15))
                .build();

        this.ollamaTransceiver = new LocalOllamaBridge(sharedNetworkHttpClient);
        this.geminiTransceiver = new GoogleCloudBridge(sharedNetworkHttpClient);

        this.asynchronousRouterBus = new CentralPortRouter();
        Thread pipelineWorkerThread = new Thread(asynchronousRouterBus, "GodMind-MasterRouter-Thread");
        pipelineWorkerThread.start();

        // 1. TOP PANEL: APIS & SELECTORS STRATUM
        JPanel settingsPanel = new JPanel(new GridLayout(2, 1, 6, 6));
        settingsPanel.setBackground(new Color(12, 18, 28));
        settingsPanel.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));

        JPanel credentialsRow = new JPanel(new BorderLayout(10, 10));
        credentialsRow.setOpaque(false);
        JLabel keyLabel = new JLabel("ENTER GOOGLE AI STUDIO CREDENTIAL KEY: ");
        keyLabel.setForeground(new Color(0, 255, 190));
        keyLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        credentialsRow.add(keyLabel, BorderLayout.WEST);

        String systemEnvKey = System.getenv("GEMINI_API_KEY");
        cloudKeyInputField = new JPasswordField(systemEnvKey != null ? systemEnvKey : "");
        cloudKeyInputField.setBackground(new Color(6, 10, 16));
        cloudKeyInputField.setForeground(Color.WHITE);
        cloudKeyInputField.setCaretColor(Color.WHITE);
        cloudKeyInputField.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        credentialsRow.add(cloudKeyInputField, BorderLayout.CENTER);

        JPanel modelSelectorRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        modelSelectorRow.setOpaque(false);
        JLabel selectionLabel = new JLabel("CHOOSE COGNITIVE INFERENCE SUBSTRATE TARGET: ");
        selectionLabel.setForeground(Color.WHITE);
        selectionLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        modelSelectorRow.add(selectionLabel);

        String[] engineRoutesList = {"LOCAL PC HARDWARE: LLAMA3 (Text Core)", "LOCAL PC HARDWARE: FLUX (Image Pipeline Matrix Model)", "GOOGLE REMOTE ENGINE: GEMINI (Cloud Gateway Loop)"};
        routeSelectionBox = new JComboBox<>(engineRoutesList);
        routeSelectionBox.setBackground(new Color(16, 26, 42));
        routeSelectionBox.setForeground(Color.WHITE);
        modelSelectorRow.add(routeSelectionBox);

        settingsPanel.add(credentialsRow);
        settingsPanel.add(modelSelectorRow);
        add(settingsPanel, BorderLayout.NORTH);

        // 2. CENTER PANEL: RENDER MATRIX SPLIT CORES
        JPanel runtimeContainerPanel = new JPanel(new GridLayout(1, 2, 10, 10));
        runtimeContainerPanel.setBorder(BorderFactory.createEmptyBorder(5, 16, 5, 16));
        runtimeContainerPanel.setBackground(new Color(2, 4, 8));

        terminalExecutionArea = new JTextArea();
        terminalExecutionArea.setBackground(new Color(4, 6, 12));
        terminalExecutionArea.setForeground(new Color(225, 235, 245));
        terminalExecutionArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        terminalExecutionArea.setEditable(false);
        terminalExecutionArea.setLineWrap(true);
        terminalExecutionArea.setWrapStyleWord(true);
        terminalExecutionArea.setText("=== UNBLOCKED DECOUPLED DEEPREACH MATRIX ENGINE INITIALIZED ===\n" +
                                      "Local Loopback Target: http://localhost:11434 [Ollama Module Loaded]\n" +
                                      "Remote TLS 1.3 Target: https://googleapis.com [Gemini Module Loaded]\n" +
                                      "All components have been cleanly decoupled to isolate execution vectors.\n\n");

        JScrollPane logScrollPaneFrame = new JScrollPane(terminalExecutionArea);
        logScrollPaneFrame.setBorder(BorderFactory.createLineBorder(new Color(25, 35, 55)));
        runtimeContainerPanel.add(logScrollPaneFrame);

        GraphicalMonitorPanel monitorPanel = new GraphicalMonitorPanel(asynchronousRouterBus);
        runtimeContainerPanel.add(monitorPanel);
        add(runtimeContainerPanel, BorderLayout.CENTER);

        // 3. LOWER PANEL: USER PROMPT INPUT LANE
        JPanel operationActionPanel = new JPanel(new BorderLayout(10, 10));
        operationActionPanel.setBorder(BorderFactory.createEmptyBorder(10, 16, 15, 16));
        operationActionPanel.setBackground(new Color(12, 18, 28));

        promptInputField = new JTextField();
        promptInputField.setBackground(new Color(6, 10, 16));
        promptInputField.setForeground(Color.WHITE);
        promptInputField.setCaretColor(Color.WHITE);
        promptInputField.setFont(new Font("Monospaced", Font.PLAIN, 13));
        promptInputField.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        operationActionPanel.add(promptInputField, BorderLayout.CENTER);

        dispatchJobButton = new JButton("DISPATCH RUN TIME VECTOR");
        dispatchJobButton.setBackground(new Color(0, 140, 255));
        dispatchJobButton.setForeground(Color.WHITE);
        dispatchJobButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        dispatchJobButton.setFocusPainted(false);
        operationActionPanel.add(dispatchJobButton, BorderLayout.EAST);

        add(operationActionPanel, BorderLayout.SOUTH);

        // Connect Decoupled Execution Handlers
        dispatchJobButton.addActionListener(e -> executeActionJob());
        promptInputField.addActionListener(e -> executeActionJob());

        Runtime.getRuntime().addShutdownHook(new Thread(asynchronousRouterBus::terminateAllRouterLocksets));
    }

    private void executeActionJob() {
        ConsoleActionHandler.dispatchInferenceJob(
                promptInputField, cloudKeyInputField, routeSelectionBox, 
                dispatchJobButton, terminalExecutionArea, ollamaTransceiver, 
                geminiTransceiver, asynchronousRouterBus
        );
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            MasterInterfaceApp frameAppInstance = new MasterInterfaceApp();
            frameAppInstance.setVisible(true);
        });
    }
}
