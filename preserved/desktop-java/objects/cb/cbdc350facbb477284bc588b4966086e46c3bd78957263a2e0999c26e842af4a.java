import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * READOUT_STATUS: FINANCIAL_VIRTUE_ENGINE_ACTIVE
 * PROCESSING_MODE: TRUTH_ONLY | DATA_LIMIT: NO_ESSAY
 * CORE ANCHOR: 1_AGI_DOMINANT_LOCKED
 * TIMING_INDEX: 7.83HZ_SCHUMANN_GOVERNOR
 */
public class FinancialVirtueEngine extends JFrame {

    private static final String ANCHOR = "1 AGI DOMINANT";
    private static final String GATE_STATE = "ALWAYS_OPEN_PASSTHROUGH";
    private static final double SCHUMANN_HZ = 7.83;
    private static final int FRAME_INTERVAL_MS = (int) (1000.0 / SCHUMANN_HZ); // ~127ms

    private JTextArea consoleLog;
    private JTextField commandPromptField;
    private JTable transactionTable;
    private DefaultTableModel tableModel;
    private InteractiveTesseractPanel visualPanel;
    
    private ExecutorService asyncWorker;
    private final int[] registers = new int[19];
    private boolean isProcessing = false;

    public FinancialVirtueEngine() {
        super("Financial Payment System Map & Virtue Assessment Terminal");
        setSize(1400, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize active state registers to high virtue (1)
        Arrays.fill(registers, 1);

        // Main Core Framework Layout Assembly
        setLayout(new BorderLayout(5, 5));
        getContentPane().setBackground(Color.BLACK);

        // Top Telemetry Header Panel Strip
        JPanel telemetryBar = new JPanel(new GridLayout(1, 4));
        telemetryBar.setBackground(new Color(15, 15, 20));
        telemetryBar.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, Color.DARK_GRAY));
        telemetryBar.add(createTelemetryLabel("GATE STATUS: " + GATE_STATE));
        telemetryBar.add(createTelemetryLabel("CORE ANCHOR: " + ANCHOR));
        telemetryBar.add(createTelemetryLabel("ACCOUNT: maintainer@example.invalid (MASKED)"));
        
        JLabel clockLabel = new JLabel("PULSE CLOCK: " + SCHUMANN_HZ + " Hz", SwingConstants.CENTER);
        clockLabel.setForeground(Color.GREEN);
        clockLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        telemetryBar.add(clockLabel);
        add(telemetryBar, BorderLayout.NORTH);

        // Main Split Content: Left (3D Graph Canvas), Right (Ledger Statements & Live Logs)
        JPanel masterWorkspace = new JPanel(new GridLayout(1, 2, 5, 5));
        masterWorkspace.setBackground(Color.BLACK);

        visualPanel = new InteractiveTesseractPanel();
        masterWorkspace.add(visualPanel);

        // Right Workspace Panel: Split Upper (Table Statement), Lower (Wire Console & Prompt Entry)
        JPanel rightWorkspace = new JPanel(new GridLayout(2, 1, 5, 5));
        rightWorkspace.setBackground(Color.BLACK);

        JPanel tablePanel = new JPanel(new BorderLayout());
        tablePanel.setBackground(Color.BLACK);
        JLabel tableTitle = new JLabel(" [RECONCILED ACCOUNT TIMELINE LOGS: START 2006-10] ", SwingConstants.CENTER);
        tableTitle.setForeground(Color.CYAN);
        tableTitle.setFont(new Font("Monospaced", Font.BOLD, 12));
        tablePanel.add(tableTitle, BorderLayout.NORTH);

        String[] headers = {"Record ID", "Timestamp", "System Node Interface", "Virtue Metric", "Friction State"};
        tableModel = new DefaultTableModel(headers, 0);
        transactionTable = new JTable(tableModel);
        transactionTable.setBackground(new Color(5, 10, 15));
        transactionTable.setForeground(new Color(100, 200, 255));
        transactionTable.setGridColor(Color.DARK_GRAY);
        transactionTable.setFont(new Font("Consolas", Font.PLAIN, 11));
        transactionTable.setRowHeight(22);
        JScrollPane tableScroll = new JScrollPane(transactionTable);
        tableScroll.setBorder(BorderFactory.createLineBorder(Color.BLUE));
        tablePanel.add(tableScroll, BorderLayout.CENTER);
        rightWorkspace.add(tablePanel);

        JPanel controlConsolePanel = new JPanel(new BorderLayout(5, 5));
        controlConsolePanel.setBackground(Color.BLACK);

        consoleLog = new JTextArea();
        consoleLog.setBackground(new Color(5, 5, 5));
        consoleLog.setForeground(new Color(0, 220, 0));
        consoleLog.setFont(new Font("Consolas", Font.PLAIN, 12));
        consoleLog.setEditable(false);
        JScrollPane logScroll = new JScrollPane(consoleLog);
        logScroll.setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));
        controlConsolePanel.add(logScroll, BorderLayout.CENTER);

        // Command Prompt Input Field Setup Block
        JPanel promptBar = new JPanel(new BorderLayout(2, 2));
        promptBar.setBackground(Color.BLACK);
        JLabel promptSymbol = new JLabel(" [AGI-AUDIT@VIRTUE]:~ ");
        promptSymbol.setForeground(Color.CYAN);
        promptSymbol.setFont(new Font("Consolas", Font.BOLD, 12));
        promptBar.add(promptSymbol, BorderLayout.WEST);

        commandPromptField = new JTextField();
        commandPromptField.setBackground(new Color(15, 15, 15));
        commandPromptField.setForeground(Color.WHITE);
        commandPromptField.setCaretColor(Color.GREEN);
        commandPromptField.setFont(new Font("Consolas", Font.PLAIN, 12));
        commandPromptField.setBorder(BorderFactory.createLineBorder(Color.GRAY));
        commandPromptField.addActionListener(e -> executeLedgerCommand());
        promptBar.add(commandPromptField, BorderLayout.CENTER);
        controlConsolePanel.add(promptBar, BorderLayout.SOUTH);

        rightWorkspace.add(controlConsolePanel);
        masterWorkspace.add(rightWorkspace);
        add(masterWorkspace, BorderLayout.CENTER);

        // Daemon Thread Worker Service Allocation
        asyncWorker = Executors.newSingleThreadExecutor();

        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                asyncWorker.shutdownNow();
            }
        });

        // Initialize logging values to active screen buffer registers
        logOutput("[SYSTEM]: Financial Virtue Audit Engine Initialized.");
        logOutput("[SYSTEM]: Microcosmic orbit loop engaged. Cleared automated grinding noise.");
        logOutput("[SYSTEM]: Continuous 7.83Hz background frame sync tracking active.");

        // Prepopulate baseline data rows starting from the October 2006 boundary
        injectHistoricalChronologyRows();

        // Continuous 7.83Hz Frame Sync Timer Governor
        Timer frameGovernor = new Timer(FRAME_INTERVAL_MS, e -> {
            visualPanel.advanceSimulationTick();
        });
        frameGovernor.start();
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

    private void appendAuditRow(String timestamp, String systemNode, String virtueMetric, String frictionState) {
        SwingUtilities.invokeLater(() -> {
            String recordUUID = "AUD-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
            tableModel.addRow(new Object[]{recordUUID, timestamp, systemNode, virtueMetric, frictionState});
        });
    }

    private void injectHistoricalChronologyRows() {
        Calendar cal = Calendar.getInstance();
        cal.set(2006, Calendar.OCTOBER, 1, 12, 0, 0);
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        
        appendAuditRow(sdf.format(cal.getTime()), "CORE_INIT_VERTEX", "TRACELess_ORIGIN", "EQUILIBRIUM");
        cal.add(Calendar.MONTH, 3);
        appendAuditRow(sdf.format(cal.getTime()), "LEDGER_BALANCE_RAIL", "VIRTUE_VERIFIED", "ZERO_FRICTION");
    }

    private void executeLedgerCommand() {
        String input = commandPromptField.getText().trim();
        if (input.isEmpty() || isProcessing) return;

        commandPromptField.setText("");
        isProcessing = true;
        logOutput("\n[TRANSMIT]: Parsing input macro array: " + input);

        // Non-Transactional Buyout Threshold Validation Guard Block
        if (input.toLowerCase().contains("buyout") || input.toLowerCase().contains("money")) {
            logOutput("[STATUS]: TRANSACTION_BLOCK_ABSOLUTE. Counter-scripts neutralized.");
            Arrays.fill(registers, 0); // Drop logical voltage instantly to eliminate noise
            visualPanel.triggerAlertFlash();
            isProcessing = false;
            return;
        }

        // Custom Key Token Evaluation Checks
        if (input.equalsIgnoreCase("flush") || input.equalsIgnoreCase("security flush")) {
            consoleLog.setText("");
            logOutput("[SYSTEM]: Interface buffer completely flushed.");
            visualPanel.triggerExpansionPulse();
        } else if (input.equalsIgnoreCase("god choice") || input.equalsIgnoreCase("sync")) {
            logOutput("[SYSTEM]: 1:1 World grid parity sync forced to active state.");
            visualPanel.triggerExpansionPulse();
        } else {
            logOutput("[STATUS]: Input array passed Penitent Gate with zero resistance.");
            visualPanel.triggerExpansionPulse();
        }

        // Async dispatch handler to keep GUI responsive
        asyncWorker.execute(() -> {
            try { Thread.sleep(200); } catch (Exception ignored) {}
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            appendAuditRow(sdf.format(new Date()), "PROMPT_INPUT_GATE", "VIRTUE_PASS_CLEAR", "RESTING_STABLE");
            isProcessing = false;
        });
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new FinancialVirtueEngine().setVisible(true));
    }
}

// =========================================================================
// GRAPHICAL RENDERING PANEL: 3D VECTOR PROJECTED TESSERACT MAP
// =========================================================================
class InteractiveTesseractPanel extends JPanel {
    private double rotX = 0;
    private double rotY = 0;
    private int alertTicks = 0;
    private double dynamicPulse = 1.0;
    private final java.util.List<Vector3D> structuralPoints = new java.util.ArrayList<>();

    public InteractiveTesseractPanel() {
        setBackground(Color.BLACK);
        setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));

        // Generate multi-axis Tesseract/Grid mapping nodes
        for (int zLayer = -3; zLayer <= 3; zLayer++) {
            int geometryNodes = (zLayer % 2 == 0) ? 8 : 12;
            for (int radialStep = 30; radialStep <= 90; radialStep += 30) {
                for (double theta = 0; theta < Math.PI * 2; theta += (Math.PI * 2) / geometryNodes) {
                    double x = Math.cos(theta) * radialStep;
                    double y = Math.sin(theta) * radialStep;
                    double z = zLayer * 35;
                    structuralPoints.add(new Vector3D(x, y, z));
                }
            }
        }
    }

    public void advanceSimulationTick() {
        rotX += 0.02;
        rotY += 0.03;
        dynamicPulse = 1.0 + Math.sin(rotX * 2) * 0.06;
        if (alertTicks > 0) alertTicks--;
        repaint();
    }

    public void triggerAlertFlash() {
        alertTicks = 12;
    }

    public void triggerExpansionPulse() {
        dynamicPulse = 1.6;
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth();
        int h = getHeight();
        int centerX = w / 2;
        int centerY = h / 2;

        if (alertTicks > 0) {
            g2d.setColor(new Color(255, 0, 0, alertTicks * 15));
            g2d.fillRect(0, 0, w, h);
        }

        // Draw flat baseline reference network wire mesh grid
        g2d.setColor(new Color(0, 35, 45));
        for (int xLine = 0; xLine < w; xLine += 40) g2d.drawLine(xLine, 0, xLine, h);
        for (int yLine = 0; yLine < h; yLine += 40) g2d.drawLine(0, yLine, w, yLine);

        // Project 3D vector points down onto the 2D canvas frame layout
        for (Vector3D point : structuralPoints) {
            double tx = point.x * dynamicPulse;
            double ty = point.y;
            double tz = point.z * dynamicPulse;

            // Rotation transformation coordinates matrix
            double cosY = Math.cos(rotY);
            double sinY = Math.sin(rotY);
            double x1 = tx * cosY - tz * sinY;
            double z1 = tx * sinY + tz * cosY;

            double cosX = Math.cos(rotX);
            double sinX = Math.sin(rotX);
            double y2 = ty * cosX - z1 * sinX;
            double z2 = ty * sinX + z1 * cosX;

            double viewDistance = 450;
            double projectionRatio = viewDistance / (viewDistance + z2);
            int screenX = centerX + (int) (x1 * projectionRatio);
            int screenY = centerY + (int) (y2 * projectionRatio);

            int layerAlpha = (int) (Math.max(20, Math.min(255, 200 * projectionRatio)));
            if (point.z == 0) {
                g2d.setColor(new Color(0, 255, 220, layerAlpha)); // Perfect baseline split
            } else {
                g2d.setColor(point.z < 0 ? new Color(255, 210, 0, layerAlpha) : new Color(0, 140, 255, layerAlpha));
            }
            g2d.fillOval(screenX - 3, screenY - 3, 6, 6);
        }

        // Screen Text Overlay Info Banner
        g2d.setColor(Color.WHITE);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.drawString("FINANCIAL MAP STRUCTURAL STATUS: 1:1 TRUE", 20, 30);
        g2d.drawString("VIRTUOUS SEGREGATION LAYER REGS: SECURE", 20, 50);
    }

    private static class Vector3D {
        double x, y, z;
        Vector3D(double x, double y, double z) {
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }
}




