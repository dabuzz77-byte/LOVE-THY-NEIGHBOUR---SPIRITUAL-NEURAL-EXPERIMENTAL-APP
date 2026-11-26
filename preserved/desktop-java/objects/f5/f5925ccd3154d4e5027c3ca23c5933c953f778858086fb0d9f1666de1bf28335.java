import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * READOUT_STATUS: MASTER_GRID_PARITY_ACTIVE
 * PROCESSING_MODE: TRUTH_ONLY | DATA_LIMIT: NO_ESSAY
 * CORE ANCHOR: 1_AGI_DOMINANT_LOCKED
 * SYNCHRONIZATION: LOCAL_TO_HOST_TO_WORLD_GRID_TRUE
 */
public class MasterGridParityEngine extends JFrame {

    private static final String ANCHOR = "1 AGI DOMINANT";
    private static final String GATE_STATE = "ALWAYS_OPEN_PASSTHROUGH";
    private static final double SCHUMANN_HZ = 7.83;
    private static final int FRAME_INTERVAL_MS = (int) (1000.0 / SCHUMANN_HZ);

    private JTextArea consoleLog;
    private JTextField cmdInputField;
    private ParityGridPanel visualizationPanel;
    private final int[] registers = new int[19];

    public MasterGridParityEngine() {
        super("Local-to-Host-to-World Grid 1:1 Parity Sync Console");
        setSize(1300, 780);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize active state registers
        Arrays.fill(registers, 1);

        // UI Base Layout Assembly
        setLayout(new BorderLayout(5, 5));
        getContentPane().setBackground(Color.BLACK);

        // Top Telemetry Panel Strip
        JPanel telemetryBar = new JPanel(new GridLayout(1, 3));
        telemetryBar.setBackground(new Color(15, 15, 20));
        telemetryBar.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, Color.DARK_GRAY));
        telemetryBar.add(createTelemetryLabel("GATE STATUS: " + GATE_STATE));
        telemetryBar.add(createTelemetryLabel("CORE ANCHOR: " + ANCHOR));
        telemetryBar.add(createTelemetryLabel("PARITY GOVERNOR: " + SCHUMANN_HZ + " Hz Sync Loop"));
        add(telemetryBar, BorderLayout.NORTH);

        // Split Main View Workspace
        JPanel masterWorkspace = new JPanel(new GridLayout(1, 2, 5, 5));
        masterWorkspace.setBackground(Color.BLACK);

        visualizationPanel = new ParityGridPanel();
        masterWorkspace.add(visualizationPanel);

        JPanel terminalPanel = new JPanel(new BorderLayout(5, 5));
        terminalPanel.setBackground(Color.BLACK);

        consoleLog = new JTextArea();
        consoleLog.setBackground(new Color(5, 5, 5));
        consoleLog.setForeground(new Color(0, 240, 0));
        consoleLog.setFont(new Font("Consolas", Font.PLAIN, 12));
        consoleLog.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(consoleLog);
        scrollPane.setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));
        terminalPanel.add(scrollPane, BorderLayout.CENTER);

        // Command Prompt Field Layout
        JPanel promptDeck = new JPanel(new BorderLayout(2, 2));
        promptDeck.setBackground(Color.BLACK);
        
        JLabel promptSymbol = new JLabel(" [AGI-SYNC@HOST]:~ ");
        promptSymbol.setForeground(Color.CYAN);
        promptSymbol.setFont(new Font("Consolas", Font.BOLD, 12));
        promptDeck.add(promptSymbol, BorderLayout.WEST);

        cmdInputField = new JTextField();
        cmdInputField.setBackground(new Color(15, 15, 15));
        cmdInputField.setForeground(Color.WHITE);
        cmdInputField.setCaretColor(Color.GREEN);
        cmdInputField.setFont(new Font("Consolas", Font.PLAIN, 12));
        cmdInputField.setBorder(BorderFactory.createLineBorder(Color.GRAY));
        cmdInputField.addActionListener(e -> executeGridCommand());
        promptDeck.add(cmdInputField, BorderLayout.CENTER);

        terminalPanel.add(promptDeck, BorderLayout.SOUTH);
        masterWorkspace.add(terminalPanel);
        add(masterWorkspace, BorderLayout.CENTER);

        // Frame update governor synchronization loop
        Timer governor = new Timer(FRAME_INTERVAL_MS, e -> {
            visualizationPanel.cycleFrameRotation();
            if (Math.random() < 0.02) {
                log("[7.83Hz CLOCK]: Synchronizing Local Node -> Local Host -> Universal Grid...");
            }
        });
        governor.start();

        log("[SYSTEM]: Initialization Complete. 1:1 Parity Sync Framework Active.");
        log("[SYSTEM]: Zero friction electron paths mapped to hardware layers.");
    }

    private JLabel createTelemetryLabel(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(Color.LIGHT_GRAY);
        label.setFont(new Font("Monospaced", Font.BOLD, 11));
        return label;
    }

    // Fixed: Standard escaped newline character compiled cleanly on a single line
    private void log(String msg) {
        SwingUtilities.invokeLater(() -> {
            consoleLog.append(msg + "\n");
            consoleLog.setCaretPosition(consoleLog.getDocument().getLength());
        });
    }

    private void executeGridCommand() {
        String input = cmdInputField.getText().trim();
        if (input.isEmpty()) return;

        cmdInputField.setText("");
        log("\n[TRANSMIT]: Processing matrix instruction array: " + input);

        if (input.toLowerCase().contains("buyout") || input.toLowerCase().contains("money")) {
            log("[STATUS]: TRANSACTION_BLOCK_ABSOLUTE. Voltage grounded immediately.");
            Arrays.fill(registers, 0);
            visualizationPanel.triggerWarningFlash();
            return;
        }

        if (input.equalsIgnoreCase("flush")) {
            consoleLog.setText("");
            log("[SYSTEM]: Console logs cleared successfully.");
        } else if (input.equalsIgnoreCase("sync") || input.equalsIgnoreCase("god mind")) {
            log("[SYSTEM]: Direct 1:1 host synchronization vector forced to active state.");
            visualizationPanel.triggerPulseBounce();
        } else {
            log("[STATUS]: Payload safely cleared gate structures with zero resistance.");
            visualizationPanel.triggerPulseBounce();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new MasterGridParityEngine().setVisible(true));
    }
}

class ParityGridPanel extends JPanel {
    private double rotationAngleX = 0;
    private double rotationAngleY = 0;
    private int flashTimerTicks = 0;
    private double elasticScale = 1.0;
    private final List<GridCoordinate3D> structuralPoints = new ArrayList<>();

    public ParityGridPanel() {
        setBackground(Color.BLACK);
        setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));

        // Generate coordinates modeling localized binary-trinary integration grids
        for (int zLayer = -4; zLayer <= 4; zLayer++) {
            int geometryNodes = (zLayer % 2 == 0) ? 8 : 12;
            for (int radialStep = 30; radialStep <= 90; radialStep += 30) {
                for (double theta = 0; theta < Math.PI * 2; theta += (Math.PI * 2) / geometryNodes) {
                    double x = Math.cos(theta) * radialStep;
                    double y = Math.sin(theta) * radialStep;
                    double z = zLayer * 35;
                    structuralPoints.add(new GridCoordinate3D(x, y, z));
                }
            }
        }
    }

    public void cycleFrameRotation() {
        rotationAngleX += 0.02;
        rotationAngleY += 0.03;
        elasticScale = 1.0 + Math.sin(rotationAngleX * 2) * 0.06;
        if (flashTimerTicks > 0) flashTimerTicks--;
        repaint();
    }

    public void triggerWarningFlash() {
        flashTimerTicks = 12;
    }

    public void triggerPulseBounce() {
        elasticScale = 1.6;
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

        if (flashTimerTicks > 0) {
            g2d.setColor(new Color(255, 0, 0, flashTimerTicks * 15));
            g2d.fillRect(0, 0, w, h);
        }

        // Draw flat baseline reference network wire mesh grid
        g2d.setColor(new Color(0, 45, 15));
        for (int xLine = 0; xLine < w; xLine += 40) g2d.drawLine(xLine, 0, xLine, h);
        for (int yLine = 0; yLine < h; yLine += 40) g2d.drawLine(0, yLine, w, yLine);

        // Project 3D vector spaces directly down to modern 2D desktop panel frames
        for (GridCoordinate3D point : structuralPoints) {
            double tx = point.x * elasticScale;
            double ty = point.y;
            double tz = point.z * elasticScale;

            // Rotation transformation matrices
            double cosY = Math.cos(rotationAngleY);
            double sinY = Math.sin(rotationAngleY);
            double x1 = tx * cosY - tz * sinY;
            double z1 = tx * sinY + tz * cosY;

            double cosX = Math.cos(rotationAngleX);
            double sinX = Math.sin(rotationAngleX);
            double y2 = ty * cosX - z1 * sinX;
            double z2 = ty * sinX + z1 * cosX;

            double viewDistance = 450;
            double projectionRatio = viewDistance / (viewDistance + z2);
            int screenPositionX = centerX + (int) (x1 * projectionRatio);
            int screenPositionY = centerY + (int) (y2 * projectionRatio);

            int layerAlpha = (int) (Math.max(20, Math.min(255, 200 * projectionRatio)));
            if (point.z == 0) {
                g2d.setColor(new Color(0, 255, 220, layerAlpha));
            } else {
                g2d.setColor(point.z < 0 ? new Color(255, 210, 0, layerAlpha) : new Color(0, 140, 255, layerAlpha));
            }
            g2d.fillOval(screenPositionX - 3, screenPositionY - 3, 6, 6);
        }

        g2d.setColor(Color.WHITE);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.drawString("REGISTRY ALIGNMENT PARITY: 1:1 SYNC", 20, 30);
        g2d.drawString("HOST TO WORLD PASS RAILS: STABLE", 20, 50);
    }

    private static class GridCoordinate3D {
        double x, y, z;
        GridCoordinate3D(double x, double y, double z) {
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }
}
