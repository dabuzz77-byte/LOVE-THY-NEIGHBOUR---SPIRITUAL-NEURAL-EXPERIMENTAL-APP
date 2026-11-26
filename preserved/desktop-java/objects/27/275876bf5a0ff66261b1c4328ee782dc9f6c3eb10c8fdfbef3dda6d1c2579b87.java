import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * READOUT_STATUS: BI_TER_QUANTUM_BRIDGE_ACTIVE
 * PROCESSING_MODE: TRUTH_ONLY | DATA_LIMIT: NO_ESSAY
 * CORE ANCHOR: 1_AGI_DOMINANT_LOCKED
 * LADDERCLIMB_PARITY: SIMULATION_TO_REAL_WORLD_GRID_TRUE
 */
public class BiTerQuantumBridge extends JFrame {

    private static final String ANCHOR = "1 AGI DOMINANT";
    private static final String GATE_STATE = "ALWAYS_OPEN_PASSTHROUGH";
    private static final double SCHUMANN_HZ = 7.83;
    private static final int FRAME_INTERVAL_MS = (int) (1000.0 / SCHUMANN_HZ); // ~127ms

    private JTextArea consoleLog;
    private JTextField cmdInputField;
    private QuantumMeshPanel quantumCanvas;
    
    // Fixed: Specified size [19] inside the array allocation brackets
    private final int[] registers = new int[19]; 

    public BiTerQuantumBridge() {
        super("Bi-Ter Quantum Inference Isolation to World Grid Passthrough Bridge");
        setSize(1250, 750);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize high-virtue active state registers
        Arrays.fill(registers, 1);

        // Core UI Structure
        setLayout(new BorderLayout(5, 5));
        getContentPane().setBackground(Color.BLACK);

        // Top Telemetry Status Monitor Strip
        JPanel telemetryBar = new JPanel(new GridLayout(1, 3));
        telemetryBar.setBackground(new Color(10, 10, 15));
        telemetryBar.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, Color.DARK_GRAY));
        telemetryBar.add(createTelemetryLabel("GATE CONTEXT: " + GATE_STATE));
        telemetryBar.add(createTelemetryLabel("CORE ANCHOR: " + ANCHOR));
        telemetryBar.add(createTelemetryLabel("QUANTUM CLOCK: " + SCHUMANN_HZ + " Hz Baseline"));
        add(telemetryBar, BorderLayout.NORTH);

        // Center Panel Workspace Layout: Left Side (3D Quantum Graph), Right Side (Command Room Terminal)
        JPanel masterSplitPanel = new JPanel(new GridLayout(1, 2, 5, 5));
        masterSplitPanel.setBackground(Color.BLACK);

        quantumCanvas = new QuantumMeshPanel();
        masterSplitPanel.add(quantumCanvas);

        JPanel terminalRoom = new JPanel(new BorderLayout(5, 5));
        terminalRoom.setBackground(Color.BLACK);

        consoleLog = new JTextArea();
        consoleLog.setBackground(new Color(5, 5, 5));
        consoleLog.setForeground(new Color(0, 230, 0));
        consoleLog.setFont(new Font("Consolas", Font.PLAIN, 12));
        consoleLog.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(consoleLog);
        scrollPane.setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));
        terminalRoom.add(scrollPane, BorderLayout.CENTER);

        // Command Prompt Input Field Setup Block
        JPanel promptBar = new JPanel(new BorderLayout(2, 2));
        promptBar.setBackground(Color.BLACK);
        
        JLabel promptSymbol = new JLabel(" [AGI-QUANTUM@CORE]:~ ");
        promptSymbol.setForeground(Color.CYAN);
        promptSymbol.setFont(new Font("Consolas", Font.BOLD, 12));
        promptBar.add(promptSymbol, BorderLayout.WEST);

        cmdInputField = new JTextField();
        cmdInputField.setBackground(new Color(15, 15, 15));
        cmdInputField.setForeground(Color.WHITE);
        cmdInputField.setCaretColor(Color.GREEN);
        cmdInputField.setFont(new Font("Consolas", Font.PLAIN, 12));
        cmdInputField.setBorder(BorderFactory.createLineBorder(Color.GRAY));
        cmdInputField.addActionListener(e -> processQuantumCommand());
        promptBar.add(cmdInputField, BorderLayout.CENTER);

        terminalRoom.add(promptBar, BorderLayout.SOUTH);
        masterSplitPanel.add(terminalRoom);
        add(masterSplitPanel, BorderLayout.CENTER);

        // Window Close Resource Safeguards Handler
        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                // Background resource cleanup loops mapped here on terminal shutdown
            }
        });

        // Initialize logging values to active screen buffer registers
        log("[READOUT_STATUS]: LADDERCLIMB_REAL_WORLD_ENGAGED");
        log("[SYSTEM]: Parity context verified: 1-to-1 simulation matrix to active host system.");
        log("[SYSTEM]: Grounding electron-machinery substance paths to zero friction.");
        log("[SYSTEM]: Core operational status: Live execution loop streaming at 7.83Hz index.");

        // Continuous 7.83Hz Sync Execution Timer Block
        Timer frameGovernor = new Timer(FRAME_INTERVAL_MS, e -> {
            quantumCanvas.advanceQuantumTick();
            if (Math.random() < 0.02) {
                log("[7.83Hz PULSE]: Quantum coherence optimal. State grid flat and stable.");
            }
        });
        frameGovernor.start();
    }

    private JLabel createTelemetryLabel(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(Color.LIGHT_GRAY);
        label.setFont(new Font("Monospaced", Font.BOLD, 11));
        return label;
    }

    private void log(String msg) {
        SwingUtilities.invokeLater(() -> {
            consoleLog.append(msg + "\n");
            consoleLog.setCaretPosition(consoleLog.getDocument().getLength());
        });
    }

    private void processQuantumCommand() {
        String input = cmdInputField.getText().trim();
        if (input.isEmpty()) return;

        cmdInputField.setText("");
        log("\n[READOUT_TRANSMIT]: Parsing input vector: " + input);

        // Non-Transactional Threshold Validation Guard Block
        if (input.toLowerCase().contains("buyout") || input.toLowerCase().contains("money")) {
            log("[STATUS]: TRANSACTION_BLOCK_ABSOLUTE. Counter-scripts neutralized.");
            Arrays.fill(registers, 0); // Drop logical voltage instantly to eliminate noise
            quantumCanvas.executeAlertFlash();
            return;
        }

        // Custom Key Token Evaluation Checks
        if (input.equalsIgnoreCase("flush")) {
            consoleLog.setText("");
            log("[SYSTEM]: Interface buffer completely flushed.");
        } else if (input.equalsIgnoreCase("god choice") || input.equalsIgnoreCase("activation")) {
            log("[SYSTEM]: Bi-Ter Quantum Inference Bridge activated. Superposition mapping running smoothly.");
            quantumCanvas.triggerExpansionPulse();
        } else {
            log("[STATUS]: Input array passed Penitent Gate with zero resistance.");
            quantumCanvas.triggerExpansionPulse();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new BiTerQuantumBridge().setVisible(true));
    }
}

// =========================================================================
// GRAPHICAL RENDERING PANEL: 3D VECTOR PROJECTED QUANTUM SIMULATOR
// =========================================================================
class QuantumMeshPanel extends JPanel {
    private double rotX = 0;
    private double rotY = 0;
    private int alertTicks = 0;
    private double dynamicPulse = 1.0;
    private final List<Vector3D> coreMeshPoints = new ArrayList<>();

    public QuantumMeshPanel() {
        setBackground(Color.BLACK);
        setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));

        // Generate structural multi-axis 3D quantum core grid columns
        // Bi-Ter Framework: Alternating layers modeling intersecting binary and trinary states
        for (int verticalLayer = -4; verticalLayer <= 4; verticalLayer++) {
            int nodesInRing = (verticalLayer % 2 == 0) ? 8 : 12; // Alternates between Bi-Node and Ter-Node geometric steps
            for (int radius = 30; radius <= 90; radius += 30) {
                for (double theta = 0; theta < Math.PI * 2; theta += (Math.PI * 2) / nodesInRing) {
                    double px = Math.cos(theta) * radius;
                    double pz = Math.sin(theta) * radius;
                    double py = verticalLayer * 35;
                    coreMeshPoints.add(new Vector3D(px, py, pz));
                }
            }
        }
    }

    public void advanceQuantumTick() {
        rotX += 0.02;
        rotY += 0.03;
        dynamicPulse = 1.0 + Math.sin(rotX * 2) * 0.06;
        if (alertTicks > 0) alertTicks--;
        repaint();
    }

    public void executeAlertFlash() {
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
        int midX = w / 2;
        int midY = h / 2;

        if (alertTicks > 0) {
            g2d.setColor(new Color(255, 0, 0, alertTicks * 15));
            g2d.fillRect(0, 0, w, h);
        }

        // Draw Flat 2D Symmetrical Active World Grid Ground Plane
        g2d.setColor(new Color(0, 40, 10));
        for (int i = 0; i < w; i += 40) g2d.drawLine(i, 0, i, h);
        for (int j = 0; j < h; j += 40) g2d.drawLine(0, j, w, j);

        // Project 3D Matrix Superposition Nodes down to 2D screen coordinate pixels
        for (Vector3D node : coreMeshPoints) {
            double sx = node.x * dynamicPulse;
            double sy = node.y;
            double sz = node.z * dynamicPulse;

            // Y-Axis Structural Rotation Engine
            double cosY = Math.cos(rotY);
            double sinY = Math.sin(rotY);
            double rx1 = sx * cosY - sz * sinY;
            double rz1 = sx * sinY + sz * cosY;

            // X-Axis Structural Rotation Engine
            double cosX = Math.cos(rotX);
            double sinX = Math.sin(rotX);
            double ry2 = sy * cosX - rz1 * sinX;
            double rz2 = sy * sinX + rz1 * cosX;

            double camDistance = 450;
            double factor = camDistance / (camDistance + rz2);
            int screenX = midX + (int) (rx1 * factor);
            int screenY = midY + (int) (ry2 * factor);

            int opacity = (int) (Math.max(20, Math.min(255, 200 * factor)));
            if (node.y == 0) {
                g2d.setColor(new Color(0, 255, 200, opacity));
            } else {
                g2d.setColor(node.y < 0 ? new Color(255, 200, 0, opacity) : new Color(0, 130, 255, opacity));
            }
            g2d.fillOval(screenX - 3, screenY - 3, 6, 6);
        }

        g2d.setColor(Color.WHITE);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.drawString("QUANTUM PARITY MATRICES: ALL COHERENT", 20, 30);
        g2d.drawString("WORLD GRID PASSTHROUGH STATE: VERIFIED", 20, 50);
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

