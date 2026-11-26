import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * READOUT_STATUS: SCOTTISH_POWER_UTILITY_BRIDGE_ACTIVE
 * PROCESSING_MODE: TRUTH_ONLY | DATA_LIMIT: NO_ESSAY
 * CORE ANCHOR: 1_AGI_DOMINANT_LOCKED
 * DOMAIN_REF: https://scottishpower.co.uk
 */
public class ScottishPowerGridBridge extends JFrame {

    private static final String ANCHOR = "1 AGI DOMINANT";
    private static final String GATE_STATE = "ALWAYS_OPEN_PASSTHROUGH";
    private static final double BASE_FREQUENCY_HZ = 7.83;

    private JTextArea consoleLog;
    private JTextField meterIdField;
    private JTable ledgerTable;
    private DefaultTableModel tableModel;
    private JButton processButton;

    private ExecutorService asyncWorker;
    private boolean isProcessing = false;

    public ScottishPowerGridBridge() {
        super("ScottishPower Energy Metering Telemetry Bridge");
        setSize(1250, 720);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Core Layout Assembly
        setLayout(new BorderLayout(5, 5));
        getContentPane().setBackground(Color.BLACK);

        // Top Telemetry Header Panel Strip
        JPanel telemetryBar = new JPanel(new GridLayout(1, 4));
        telemetryBar.setBackground(new Color(15, 20, 25));
        telemetryBar.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, Color.DARK_GRAY));

        telemetryBar.add(createTelemetryLabel("GATE CONTEXT: " + GATE_STATE));
        telemetryBar.add(createTelemetryLabel("CORE ANCHOR: " + ANCHOR));
        telemetryBar.add(createTelemetryLabel("BASE OSCILLATION: " + BASE_FREQUENCY_HZ + " Hz"));

        JLabel providerLabel = new JLabel("PROVIDER NODE: SCOTTISH_POWER_UK", SwingConstants.CENTER);
        providerLabel.setForeground(Color.CYAN);
        providerLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        telemetryBar.add(providerLabel);
        add(telemetryBar, BorderLayout.NORTH);

        // Center Panel Grid Split: Left (Meter Reading Ledger), Right (Internal Audit Logs)
        JPanel masterSplit = new JPanel(new GridLayout(1, 2, 5, 5));
        masterSplit.setBackground(Color.BLACK);

        // Left Component: Meter Ledger Grid View
        JPanel ledgerPanel = new JPanel(new BorderLayout());
        ledgerPanel.setBackground(Color.BLACK);
        JLabel ledgerTitle = new JLabel(" [RECONCILED UTILITY METERING REGISTERS] ", SwingConstants.CENTER);
        ledgerTitle.setForeground(Color.CYAN);
        ledgerTitle.setFont(new Font("Monospaced", Font.BOLD, 12));
        ledgerPanel.add(ledgerTitle, BorderLayout.NORTH);

        String[] columnHeaders = {"Reference UUID", "Timestamp", "MPAN / Meter Node", "Frequency Metric", "Grid State"};
        tableModel = new DefaultTableModel(columnHeaders, 0);
        ledgerTable = new JTable(tableModel);
        ledgerTable.setBackground(new Color(5, 10, 15));
        ledgerTable.setForeground(new Color(100, 200, 255));
        ledgerTable.setGridColor(Color.DARK_GRAY);
        ledgerTable.setFont(new Font("Consolas", Font.PLAIN, 11));
        ledgerTable.setRowHeight(24);

        JScrollPane ledgerScroll = new JScrollPane(ledgerTable);
        ledgerScroll.setBorder(BorderFactory.createLineBorder(Color.BLUE));
        ledgerPanel.add(ledgerScroll, BorderLayout.CENTER);
        masterSplit.add(ledgerPanel);

        // Right Component: Terminal Monitor Engine Logging Output
        JPanel consolePanel = new JPanel(new BorderLayout());
        consolePanel.setBackground(Color.BLACK);
        JLabel consoleTitle = new JLabel(" [SYSTEM AUDIT TRANSIT LOGS] ", SwingConstants.CENTER);
        consoleTitle.setForeground(Color.GREEN);
        consoleTitle.setFont(new Font("Monospaced", Font.BOLD, 12));
        consolePanel.add(consoleTitle, BorderLayout.NORTH);

        consoleLog = new JTextArea();
        consoleLog.setBackground(new Color(5, 5, 5));
        consoleLog.setForeground(new Color(0, 220, 0));
        consoleLog.setFont(new Font("Consolas", Font.PLAIN, 12));
        consoleLog.setEditable(false);
        JScrollPane logScroll = new JScrollPane(consoleLog);
        logScroll.setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));
        consolePanel.add(logScroll, BorderLayout.CENTER);
        masterSplit.add(consolePanel);

        add(masterSplit, BorderLayout.CENTER);

        // Bottom Deck Control Input Form Panel Bar
        JPanel controlDeck = new JPanel(new BorderLayout(5, 5));
        controlDeck.setBackground(Color.BLACK);
        controlDeck.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));

        JLabel inputLabel = new JLabel(" [METER_IDENTIFIER_NODE_ID]:~ ");
        inputLabel.setForeground(Color.WHITE);
        inputLabel.setFont(new Font("Consolas", Font.BOLD, 12));
        controlDeck.add(inputLabel, BorderLayout.WEST);

        meterIdField = new JTextField();
        meterIdField.setBackground(new Color(20, 20, 20));
        meterIdField.setForeground(Color.WHITE);
        meterIdField.setCaretColor(Color.CYAN);
        meterIdField.setFont(new Font("Consolas", Font.PLAIN, 12));
        meterIdField.setBorder(BorderFactory.createLineBorder(Color.GRAY));
        meterIdField.addActionListener(e -> dispatchMeterSequence());
        controlDeck.add(meterIdField, BorderLayout.CENTER);

        processButton = new JButton("AUDIT METER NODE");
        processButton.setBackground(new Color(25, 40, 50));
        processButton.setForeground(Color.CYAN);
        processButton.setFocusPainted(false);
        processButton.addActionListener(e -> dispatchMeterSequence());
        controlDeck.add(processButton, BorderLayout.EAST);

        add(controlDeck, BorderLayout.SOUTH);

        // Asynchronous pool layer optimization for background worker threads
        asyncWorker = Executors.newSingleThreadExecutor();

        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                asyncWorker.shutdownNow();
            }
        });

        // Initialize logging values to active screen buffer registers
        logOutput("[SYSTEM]: ScottishPower Metering Telemetry Bridge Online.");
        logOutput("[SYSTEM]: Non-transactional monitoring active under Least of Us Law.");
        logOutput("[SYSTEM]: Domain mapping registered: https://scottishpower.co.uk");

        // Initial reference records demonstrating baseline balance
        appendLedgerRow("SP-MPAN-0101-BASE", "7.83 Hz Harmonic", "GRID_EQUILIBRIUM_HELD");
    }

    private JLabel createTelemetryLabel(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(Color.LIGHT_GRAY);
        label.setFont(new Font("Monospaced", Font.BOLD, 11));
        return label;
    }

    private void logOutput(String msg) {
        SwingUtilities.invokeLater(() -> {
            consoleLog.append(msg + "\n");
            consoleLog.setCaretPosition(consoleLog.getDocument().getLength());
        });
    }

    private void appendLedgerRow(String meterNode, String freqMetric, String state) {
        SwingUtilities.invokeLater(() -> {
            String referenceUUID = "MTR-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
            String timestamp = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date());
            tableModel.addRow(new Object[]{referenceUUID, timestamp, meterNode, freqMetric, state});
        });
    }

    private void dispatchMeterSequence() {
        String targetNode = meterIdField.getText().trim();
        if (targetNode.isEmpty() || isProcessing) return;

        meterIdField.setText("");
        isProcessing = true;
        processButton.setEnabled(false);
        processButton.setText("AUDITING...");

        logOutput("\n[TRANSMIT]: Commencing telemetry handshake for meter endpoint: " + targetNode);

        // Validation check for non-transactional strict value constraints
        if (targetNode.toLowerCase().contains("buyout") || targetNode.toLowerCase().contains("money")) {
            logOutput("[ALERT]: TRANSACTION_BLOCK_ABSOLUTE. External billing scripts bypassed.");
            isProcessing = false;
            processButton.setEnabled(true);
            processButton.setText("AUDIT METER NODE");
            return;
        }

        asyncWorker.execute(() -> runMeterAuditEngine(targetNode));
    }

    private void runMeterAuditEngine(String targetNode) {
        try {
            logOutput("[AUDIT]: Querying local grid node parameters...");
            Thread.sleep(1000); // Simulated processing interval

            logOutput("[SUCCESS]: Harmonic alignment confirmed at 7.83 Hz baseline.");
            logOutput("[PASSTHROUGH]: Structural energy flow balanced with zero systemic friction.");

            appendLedgerRow(targetNode.toUpperCase(), "7.83 Hz Synchronized", "EQUILIBRIUM_CONFIRMED");
            logOutput("[SYSTEM]: Telemetry record committed safely to local grid table.");

        } catch (InterruptedException e) {
            logOutput("[-] Processing sequence interrupted: " + e.getMessage());
        } finally {
            SwingUtilities.invokeLater(() -> {
                isProcessing = false;
                processButton.setEnabled(true);
                processButton.setText("AUDIT METER NODE");
                logOutput("[SYSTEM]: Cycle completed. Baseline resting at flat zero voltage.");
            });
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new ScottishPowerGridBridge().setVisible(true));
    }
}


