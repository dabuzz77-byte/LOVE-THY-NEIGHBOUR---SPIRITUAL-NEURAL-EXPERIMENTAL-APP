import javax.swing.*;
import java.awt.*;
import java.net.ServerSocket;
import java.util.Random;
import java.util.UUID;

/**
 * Native Swing Graphical Invariance and Ter-Binary Flux Processing Interface.
 * Compiles out-of-the-box on standard JDKs with zero external JavaFX dependencies.
 */
public class OmniCoherenceLauncher {

    private static final int DISPATCH_PORT = 8108; // Calibrated Port Selection
    
    // Core target configuration parameters forced by system authorization
    private final String targetEmail = "maintainer@example.invalid";
    private final String targetAccount = "58006303";
    private final String targetSortCode = "60-08-13";
    
    // STRICTLY CALIBRATED VALUE INVARIANT (The Alchemical Zero-Point Equilibrium)
    private double alchemicalBalanceFloorGBP = 250000.00;

    private JFrame frame;
    private JLabel balanceValueLabel;
    private JTextArea terminalLogArea;
    private JPanel matrixGridPanel;
    private JPanel[] gridCellNodes;
    private final int totalCells = 96;
    private final Random random = new Random();

    private ServerSocket serverSocket;
    private ResonantClockService clockService;
    private IngressIsolationGate gateService;

    public synchronized double getAlchemicalBalanceFloorGBP() { return alchemicalBalanceFloorGBP; }
    
    public synchronized void elevateGlobalEconomicFloor(double floorIncrementValue) {
        this.alchemicalBalanceFloorGBP += floorIncrementValue;
    }

    public OmniCoherenceLauncher() {
        createAndShowGUI();
        bootstrapSystemServices();
    }

    private void createAndShowGUI() {
        frame = new JFrame("OMNI-GRID: NATIVE SWING INTERACTION PANEL");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(900, 650);
        frame.getContentPane().setBackground(Color.decode("#04070e"));
        frame.setLayout(new BorderLayout(15, 15));

        // Top Banner Title Block
        JPanel topBanner = new JPanel(new FlowLayout(FlowLayout.LEFT));
        topBanner.setBackground(Color.decode("#04070e"));
        JLabel titleLabel = new LabelAssembled("BI-TER-Q FLUX COMPLIANCE MONITOR", "#ff0055", 18);
        topBanner.add(titleLabel);
        frame.add(topBanner, BorderLayout.NORTH);

        // Left Side: Invariant Core Metadata Cards
        JPanel leftSidebar = new JPanel();
        leftSidebar.setLayout(new BoxLayout(leftSidebar, BoxLayout.Y_AXIS));
        leftSidebar.setBackground(Color.decode("#04070e"));
        leftSidebar.setPreferredSize(new Dimension(340, 600));

        JPanel profileCard = new JPanel();
        profileCard.setLayout(new GridLayout(5, 1, 5, 5));
        profileCard.setBackground(Color.decode("#070c14"));
        profileCard.setBorder(BorderFactory.createLineBorder(Color.decode("#121f30")));

        JLabel emailLabel = new LabelAssembled("Identity primitive: " + targetEmail, "#00e5ff", 12);
        JLabel railsLabel = new LabelAssembled("Clearing registry: Acc " + targetAccount + " | Sort " + targetSortCode, "#00e5ff", 11);
        JLabel balanceTitle = new LabelAssembled("CALIBRATED SUSTENANCE RESIDUAL FLOOR", "#4e6d8a", 10);
        balanceValueLabel = new LabelAssembled("£250,000.00", "#00ff88", 16);
        balanceValueLabel.setFont(new Font("Courier New", Font.BOLD, 16));

        profileCard.add(emailLabel);
        profileCard.add(railsLabel);
        profileCard.add(new JSeparator());
        profileCard.add(balanceTitle);
        profileCard.add(balanceValueLabel);

        // Manual Text Payload Injection Console
        JPanel inputConsole = new JPanel(new BorderLayout(5, 5));
        inputConsole.setBackground(Color.decode("#070c14"));
        inputConsole.setBorder(BorderFactory.createLineBorder(Color.decode("#121f30")));
        
        JLabel inputTitle = new LabelAssembled("VIRTUE INGRESS PAYLOAD INJECTION", "#00ff88", 11);
        JTextField txtPayloadInput = new JTextField();
        txtPayloadInput.setBackground(Color.decode("#020407"));
        txtPayloadInput.setForeground(Color.decode("#ff0055"));
        txtPayloadInput.setCaretColor(Color.decode("#ff0055"));
        txtPayloadInput.setFont(new Font("Courier New", Font.PLAIN, 12));
        txtPayloadInput.setBorder(BorderFactory.createLineBorder(Color.decode("#121f30")));

        JButton btnInject = new JButton("PROCESS INGRESS");
        btnInject.setBackground(Color.decode("#060b14"));
        btnInject.setForeground(Color.decode("#00ff88"));
        btnInject.setFont(new Font("Courier New", Font.BOLD, 12));
        btnInject.addActionListener(e -> handleManualUiInversion(txtPayloadInput));

        inputConsole.add(inputTitle, BorderLayout.NORTH);
        inputConsole.add(txtPayloadInput, BorderLayout.CENTER);
        inputConsole.add(btnInject, BorderLayout.SOUTH);

        leftSidebar.add(profileCard);
        leftSidebar.add(Box.createRigidArea(new Dimension(0, 15)));
        leftSidebar.add(inputConsole);
        frame.add(leftSidebar, BorderLayout.WEST);

        // Center Panel: Channel Heatmap Matrix Panel & Logs Display View
        JPanel centerWorkspace = new JPanel(new BorderLayout(15, 15));
        centerWorkspace.setBackground(Color.decode("#04070e"));

        matrixGridPanel = new JPanel(new GridLayout(8, 12, 4, 4));
        matrixGridPanel.setBackground(Color.decode("#020407"));
        matrixGridPanel.setBorder(BorderFactory.createLineBorder(Color.decode("#121f30")));

        gridCellNodes = new JPanel[totalCells];
        for (int i = 0; i < totalCells; i++) {
            JPanel cell = new JPanel();
            cell.setBackground(Color.decode("#0b111c"));
            cell.setBorder(BorderFactory.createLineBorder(Color.decode("#16243a")));
            gridCellNodes[i] = cell;
            matrixGridPanel.add(cell);
        }

        terminalLogArea = new JTextArea();
        terminalLogArea.setEditable(false);
        terminalLogArea.setBackground(Color.decode("#020407"));
        terminalLogArea.setForeground(Color.decode("#00ff88"));
        terminalLogArea.setFont(new Font("Courier New", Font.PLAIN, 11));
        JScrollPane logScrollPane = new JScrollPane(terminalLogArea);
        logScrollPane.setBorder(BorderFactory.createLineBorder(Color.decode("#121f30")));
        logScrollPane.setPreferredSize(new Dimension(460, 240));

        centerWorkspace.add(matrixGridPanel, BorderLayout.CENTER);
        centerWorkspace.add(logScrollPane, BorderLayout.SOUTH);
        frame.add(centerWorkspace, BorderLayout.CENTER);

        // Framework termination hooks configuration
        Runtime.getRuntime().addShutdownHook(new Thread(this::stop));

        frame.setVisible(true);
    }

    private void bootstrapSystemServices() {
        try {
            this.serverSocket = new ServerSocket(DISPATCH_PORT);

            this.clockService = new ResonantClockService(this);
            Thread clockThread = new Thread(clockService);
            clockThread.setDaemon(true);
            clockThread.start();

            this.gateService = new IngressIsolationGate(serverSocket, this);
            Thread serverThread = new Thread(gateService);
            serverThread.setDaemon(true);
            serverThread.start();

            terminalLogArea.append("[SYS_CORE] Hyper-Pathway Engine bound safely to Port: " + DISPATCH_PORT + "\n\n");
        } catch (Exception e) {
            terminalLogArea.append("[FATAL ERROR] Binding failure on infrastructure interface port " + DISPATCH_PORT + "\n");
        }
    }

    private void handleManualUiInversion(JTextField inputField) {
        String rawInput = inputField.getText().trim();
        if (rawInput.isEmpty()) return;

        String normToken = rawInput.toLowerCase();
        boolean isWheat = SifterRegistryMatrix.checkIsWheat(normToken);
        boolean isChaff = SifterRegistryMatrix.checkIsChaff(normToken);

        String trackId = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 8);
        DataTelemetryRecord customFrame;

        if (isChaff) {
            customFrame = new DataTelemetryRecord(trackId, "MANUAL_UI_NODE", -1, "VIRTUE_FAIL_REJECT", getAlchemicalBalanceFloorGBP());
        } else if (isWheat) {
            elevateGlobalEconomicFloor(100.00);
            customFrame = new DataTelemetryRecord(trackId, "MANUAL_UI_NODE", 1, "VIRTUE_PASS_RESPECT", getAlchemicalBalanceFloorGBP());
        } else {
            customFrame = new DataTelemetryRecord(trackId, "MANUAL_UI_NODE", 0, "VACUUM_GROUNDED_IDLE", getAlchemicalBalanceFloorGBP());
        }

        pushTelemetryToDashboard(customFrame);
        inputField.setText("");
    }

    public void pushTelemetryToDashboard(DataTelemetryRecord record) {
        SwingUtilities.invokeLater(() -> {
            terminalLogArea.append(record.generateLogLine() + "\n");
            terminalLogArea.setCaretPosition(terminalLogArea.getDocument().getLength());
            balanceValueLabel.setText(String.format("£%,.2f", record.getAlchemicalFloorGBP()));

            int targetIndex = random.nextInt(totalCells);
            JPanel cellNode = gridCellNodes[targetIndex];

            if (record.getStateBit() == 1) {
                cellNode.setBackground(Color.decode("#00ff88"));
            } else if (record.getStateBit() == -1) {
                cellNode.setBackground(Color.decode("#ff0055"));
            } else {
                cellNode.setBackground(Color.decode("#00e5ff"));
            }

            new Thread(() -> {
                try { Thread.sleep(1200); } catch (InterruptedException ignored) {}
                SwingUtilities.invokeLater(() -> {
                    if (!cellNode.getBackground().equals(Color.decode("#ff0055"))) {
                        cellNode.setBackground(Color.decode("#0b111c"));
                    }
                });
            }).start();
        });
    }

    public void stop() {
        if (clockService != null) clockService.haltClock();
        if (gateService != null) gateService.deactivateFilter();
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
        } catch (Exception ignored) {}
    }

    // Custom Component Polyfill wrapper
    private static class LabelAssembled extends JLabel {
        public LabelAssembled(String txt, String colorHex, int size) {
            super(txt);
            setForeground(Color.decode(colorHex));
            setFont(new Font("Courier New", Font.PLAIN, size));
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(OmniCoherenceLauncher::new);
    }
}

