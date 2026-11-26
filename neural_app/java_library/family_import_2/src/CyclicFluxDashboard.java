import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.io.Serializable;
import java.util.Random;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * ================================================================================
 * SYSTEM COGNITION ALIGNMENT INVARIANT // UNIFIED MONOLITHIC ORBIT CHASSIS
 * ================================================================================
 * Standalone monolithic version with stabilized fractal lightning math bounds.
 * All UI styles, drawing panels, and translation matrices within a single file.
 */
public class CyclicFluxDashboard extends SectionFrame implements Serializable {
    private static final long serialVersionUID = 783802L;

    // Core Constants & Carrier Frequency Definitions
    private static final double SCHUMANN_CARRIER_HZ = 7.83;

    // Theme Custom UI Tokens
    private static final Color BG_MATRIX = new Color(5, 7, 9);
    private static final Color BG_PANEL = new Color(14, 18, 22);
    private static final Color ELEC_CORE = new Color(220, 245, 255);
    private static final Color ELEC_GLOW = new Color(0, 160, 255, 130);
    private static final Color BINARY_GLINT = new Color(50, 215, 120);
    private static final Color QUANTUM_PURPLE = new Color(190, 80, 255);
    private static final Color TERNARY_AMBER = new Color(255, 160, 0);
    private static final Color TEXT_LIGHT = new Color(230, 235, 245);
    private static final Color TEXT_MUTED = new Color(130, 145, 160);

    private static final Font MONO_SM = new Font("Monospaced", Font.PLAIN, 11);
    private static final Font SANS_MD = new Font("SansSerif", Font.BOLD, 12);

    // Multi-Lattice Core Tracking Fields
    private final ScheduledExecutorService orbitScheduler;
    private double systemTickerStep = 0.0;

    private final int[] binaryInputGrid = {1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0};
    private final double[][] quantumAmplitudes = new double[16][2]; // alpha, beta
    private final int[] ternaryOutputGrid = new int[16];
    private final int[] terminalBinaryGrid = new int[16];

    // Nested Graphical Containers
    private ElectricityPanel plasmaOrbitPanel;
    private JPanel dataMatrixPanel;
    private JTextArea mathAuditConsole;

    /**
     * Inner Class Panel: Custom Electrical Microcosmic Filament Channel Renderer.
     */
    public static class ElectricityPanel extends JPanel {
        private final Random rand = new Random();
        private double dischargePhase = 0.0;

        public ElectricityPanel() {
            setBackground(BG_PANEL);
        }

        public void incrementOrbitPhase() {
            this.dischargePhase += 0.15;
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();
            int midY = h / 2;

            // Background raw electrical glow arc channel
            g2.setStroke(new BasicStroke(5.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g2.setColor(ELEC_GLOW);
            drawFractalLightningArc(g2, 10, midY, w - 10, midY, 14);

            // Hot inner lightning core path filament
            g2.setStroke(new BasicStroke(1.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g2.setColor(ELEC_CORE);
            drawFractalLightningArc(g2, 10, midY, w - 10, midY, 6);
        }

        private void drawFractalLightningArc(Graphics2D g2, int x1, int y1, int x2, int y2, int displacement) {
            if ((x2 - x1) < 5) {
                g2.drawLine(x1, y1, x2, y2);
            } else {
                int midX = (x1 + x2) / 2;
                int midY = (y1 + y2) / 2;
                
                // CRITICAL MATHEMATICAL FIX: Ensure displacement bound is always positive (>= 1)
                int absoluteBound = Math.max(1, displacement);
                midY += (rand.nextInt(absoluteBound * 2) - absoluteBound) + (Math.sin(dischargePhase) * 2);
                
                drawFractalLightningArc(g2, x1, y1, midX, midY, displacement / 2);
                drawFractalLightningArc(g2, midX, midY, x2, y2, displacement / 2);
            }
        }
    }

    public CyclicFluxDashboard() {
        this.orbitScheduler = SharedScheduler.newSingleThreadScheduledExecutor();

        setTitle("⚡ STANDALONE CYCLIC CONVERGENCE FLUX SUBSTRATE");
        setSize(1200, 750);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(BG_MATRIX);
        setLayout(new BorderLayout(10, 10));

        buildInterfaceTopology();
    }

    private void buildInterfaceTopology() {
        // 1. Top Panel: Electrical Orbit Arc
        plasmaOrbitPanel = new ElectricityPanel();
        plasmaOrbitPanel.setPreferredSize(new Dimension(1200, 80));
        applyContainerBorder(plasmaOrbitPanel, "ELECTRIC MICROCOSMIC ORBIT FIELD CHANNEL (RAW DISCHARGE)");
        add(plasmaOrbitPanel, BorderLayout.NORTH);

        // 2. Center Panel: Visual Data States Grid Panels
        dataMatrixPanel = new JPanel(new GridLayout(1, 4, 10, 10));
        dataMatrixPanel.setBackground(BG_MATRIX);
        dataMatrixPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 0, 10));
        add(dataMatrixPanel, BorderLayout.CENTER);

        // 3. Lower Panel: Invariant Telemetry Console
        JPanel bottomWrapper = new JPanel(new BorderLayout());
        bottomWrapper.setBackground(BG_MATRIX);
        bottomWrapper.setPreferredSize(new Dimension(1200, 240));
        bottomWrapper.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        mathAuditConsole = new JTextArea();
        mathAuditConsole.setEditable(false);
        mathAuditConsole.setBackground(new Color(10, 13, 16));
        mathAuditConsole.setForeground(BINARY_GLINT);
        mathAuditConsole.setFont(MONO_SM);
        
        JScrollPane scrollPane = new JScrollPane(mathAuditConsole);
        applyContainerBorder(scrollPane, "LIVE TRANSFORMATION MATHEMATICS OVERRIDE STREAM");
        bottomWrapper.add(scrollPane, BorderLayout.CENTER);
        add(bottomWrapper, BorderLayout.SOUTH);
    }

    private void applyContainerBorder(JComponent comp, String header) {
        comp.setBackground(BG_PANEL);
        TitledBorder border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(45, 55, 70), 1), header
        );
        border.setTitleFont(SANS_MD);
        border.setTitleColor(TEXT_MUTED);
        comp.setBorder(BorderFactory.createCompoundBorder(border, BorderFactory.createEmptyBorder(6, 6, 6, 6)));
    }

    /**
     * Executes the sequential data translations (Binary -> Quantum -> Ternary -> Binary).
     */
    private void executeSubstrateCyclicShift() {
        systemTickerStep += 0.1;
        plasmaOrbitPanel.incrementOrbitPhase();

        StringBuilder mathLog = new StringBuilder();
        mathLog.append(String.format("[⚡ TIME STAMP %d] Executing Grid Translation Topology Invariant...%n", System.currentTimeMillis()));

        // STEP 1: Binary -> Quantum State Translations
        mathLog.append(" ├── [BI ──► QUANTUM MATCHES]:\n");
        for (int i = 0; i < 16; i++) {
            double theta = (binaryInputGrid[i] * (Math.PI / 2)) + (Math.sin(systemTickerStep) * 0.2);
            quantumAmplitudes[i][0] = Math.cos(theta); // Alpha state value
            quantumAmplitudes[i][1] = Math.sin(theta); // Beta state value
            if (i < 4) {
                mathLog.append(String.format(" │     Node %d: Bit %d ──► ψ|α:%.2f, β:%.2f⟩%n", i, binaryInputGrid[i], quantumAmplitudes[i][0], quantumAmplitudes[i][1]));
            }
        }

        // STEP 2: Quantum -> Balanced Ternary State Slicing
        mathLog.append(" ├── [QUANTUM ──► TERNARY MATCHES]:\n");
        for (int i = 0; i < 16; i++) {
            double probabilityWeight = Math.pow(quantumAmplitudes[i][0], 2) - Math.pow(quantumAmplitudes[i][1], 2);
            ternaryOutputGrid[i] = probabilityWeight > 0.3 ? 1 : (probabilityWeight < -0.3 ? -1 : 0);
            if (i < 4) {
                mathLog.append(String.format(" │     Node %d: ProbDiff: %.2f ──► Ternary: %s%n", i, probabilityWeight, (ternaryOutputGrid[i] == 1 ? "+" : (ternaryOutputGrid[i] == -1 ? "-" : "0"))));
            }
        }

        // STEP 3: Ternary -> Down-Sampled Terminal Binary Alignment
        mathLog.append(" └── [TERNARY ──► TERMINAL BINARY MATCHES]:\n");
        for (int i = 0; i < 16; i++) {
            terminalBinaryGrid[i] = Math.abs(ternaryOutputGrid[i]);
            if (i < 4) {
                mathLog.append(String.format("       Node %d: Ternary %d ──► Final Bit: %d%n", i, ternaryOutputGrid[i], terminalBinaryGrid[i]));
            }
        }

        // Dispatch GUI layout repaints safely back to the Event Dispatch Thread
        SwingUtilities.invokeLater(() -> {
            mathAuditConsole.setText(mathLog.toString());
            updateGraphicalDisplayMatrix();
            plasmaOrbitPanel.repaint();
        });
    }

    private void updateGraphicalDisplayMatrix() {
        dataMatrixPanel.removeAll();

        dataMatrixPanel.add(createVectorCellPanel("1. SOURCE BINARY", buildArrayDisplayString(binaryInputGrid, false), BINARY_GLINT));
        dataMatrixPanel.add(createVectorCellPanel("2. QUANTUM PHASE", buildQuantumMatrixString(), QUANTUM_PURPLE));
        dataMatrixPanel.add(createVectorCellPanel("3. BALANCED TERNARY", buildArrayDisplayString(ternaryOutputGrid, true), TERNARY_AMBER));
        dataMatrixPanel.add(createVectorCellPanel("4. OUTPUT BINARY", buildArrayDisplayString(terminalBinaryGrid, false), BINARY_GLINT));

        dataMatrixPanel.revalidate();
    }

    private JPanel createVectorCellPanel(String title, String data, Color foregroundColor) {
        JPanel cell = new JPanel(new BorderLayout());
        styleDisplayCell(cell, title);
        JTextArea area = new JTextArea(data);
        area.setEditable(false);
        area.setBackground(BG_PANEL);
        area.setForeground(foregroundColor);
        area.setFont(new Font("Monospaced", Font.BOLD, 13));
        cell.add(area, BorderLayout.CENTER);
        return cell;
    }

    private void styleDisplayCell(JPanel panel, String title) {
        panel.setBackground(BG_PANEL);
        TitledBorder border = BorderFactory.createTitledBorder(BorderFactory.createEmptyBorder(), title);
        border.setTitleFont(SANS_MD);
        border.setTitleColor(TEXT_MUTED);
        panel.setBorder(BorderFactory.createCompoundBorder(border, BorderFactory.createEmptyBorder(4, 4, 4, 4)));
    }

    private String buildArrayDisplayString(int[] arr, boolean isTernary) {
        StringBuilder sb = new StringBuilder("\n");
        for (int i = 0; i < arr.length; i++) {
            String element = isTernary ? (arr[i] == 1 ? "  +  " : (arr[i] == -1 ? "  -  " : "  0  ")) : "  " + arr[i] + "  ";
            sb.append(element);
            if ((i + 1) % 4 == 0) sb.append("\n\n");
        }
        return sb.toString();
    }

    private String buildQuantumMatrixString() {
        StringBuilder sb = new StringBuilder("\n");
        for (int i = 0; i < 4; i++) {
            sb.append(String.format(" |%.1f,%.1f⟩", quantumAmplitudes[i][0], quantumAmplitudes[i][1]));
            if ((i + 1) % 2 == 0) sb.append("\n\n");
        }
        sb.append("   [+12 Nodes]");
        return sb.toString();
    }

    public void startSubstrateLoops() {
        long schumannIntervalMicros = (long) ((1.0 / SCHUMANN_CARRIER_HZ) * 1_000_000.0);
        this.orbitScheduler.scheduleAtFixedRate(this::executeSubstrateCyclicShift, 0, schumannIntervalMicros, TimeUnit.MICROSECONDS);
    }

    /**
     * Monolithic Main Driver Launch Frame.
     */
    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            CyclicFluxDashboard systemChassis = new CyclicFluxDashboard();
            systemChassis.setVisible(true);
            systemChassis.startSubstrateLoops();
        });
    }
}
