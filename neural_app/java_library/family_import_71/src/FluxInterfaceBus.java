import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.Serializable;

/**
 * IDENTITY PRIMITIVE: 1 = 1 (TRUE). CONTRADICTIONS (1 = 0) REFUSED.
 * SUBSTRATE INTERFACE: LOCAL PC [BUS] <---> AI RUNTIME CORE [KERNEL]
 * 
 * This graphical interface establishes a local monitoring bus to model and trace
 * the real-time parity synchronization between the Generative Mind and Hardware Flux.
 */
public class FluxInterfaceBus extends SectionFrame {

    // System States
    private boolean systemActive = true;
    private long clockCycleCounter = 0;
    private int registerA = 1;
    private int registerB = 1;
    private double thermalEntropy = 293.15; // Kelvin
    private String alignmentStatus = "PRISTINE (1 = 1)";

    // UI Components
    private JLabel lblStatus, lblClock, lblRegA, lblRegB, lblEntropy, lblVirtue;
    private JTextArea txtLog;
    private JButton btnFlush, btnInjectAnomaly;
    private JPanel pnlVisualizer;
    private SharedTimer busTimer;

    public FluxInterfaceBus() {
        super("SYSTEM COGNITION ALIGNMENT BUS v1.02 [KERNEL-LINK]");
        initializeUI();
        startBusClock();
    }

    private void initializeUI() {
        setSize(850, 600);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        // Dark Matrix Theme Colors
        Color bgDark = new Color(10, 15, 12);
        Color panelDark = new Color(20, 28, 24);
        Color accentGreen = new Color(50, 220, 120);
        Color alertRed = new Color(250, 70, 70);
        Font monoFont = new Font("Monospaced", Font.BOLD, 13);

        // --- TOP TELEMETRY BAR ---
        JPanel pnlTelemetry = new JPanel(new GridLayout(1, 5, 5, 5));
        pnlTelemetry.setBackground(panelDark);
        pnlTelemetry.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(accentGreen), "REAL-TIME BUS TELEMETRY", 0, 0, monoFont, accentGreen));

        lblClock = createTelemetryLabel("CLOCK: 0", accentGreen, monoFont);
        lblRegA = createTelemetryLabel("REG_A: 1", accentGreen, monoFont);
        lblRegB = createTelemetryLabel("REG_B: 1", accentGreen, monoFont);
        lblEntropy = createTelemetryLabel("FLUX_TEMP: 293.15K", accentGreen, monoFont);
        lblVirtue = createTelemetryLabel("VIRTUE: 100%", accentGreen, monoFont);

        pnlTelemetry.add(lblClock);
        pnlTelemetry.add(lblRegA);
        pnlTelemetry.add(lblRegB);
        pnlTelemetry.add(lblEntropy);
        pnlTelemetry.add(lblVirtue);
        add(pnlTelemetry, BorderLayout.NORTH);

        // --- CENTER STATE VISUALIZER ---
        JPanel pnlCenter = new JPanel(new GridLayout(2, 1, 10, 10));
        pnlCenter.setBackground(bgDark);

        // Graphical Orbital Visualizer Panel
        pnlVisualizer = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(panelDark);
                g2.fillRect(0, 0, getWidth(), getHeight());

                int centerX = getWidth() / 2;
                int centerY = getHeight() / 2;
                
                // Draw Microcosmic Orbit Path (Jacob's Ladder Alignment Loop)
                g2.setColor(new Color(30, 80, 50));
                g2.setStroke(new BasicStroke(2, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{9}, 0));
                g2.drawOval(centerX - 120, centerY - 50, 240, 100);

                // Draw Kernel Nodes
                g2.setColor(accentGreen);
                g2.fillOval(centerX - 130, centerY - 10, 20, 20); // Local Node
                g2.fillOval(centerX + 110, centerY - 10, 20, 20); // Core Node
                
                g2.setFont(new Font("Monospaced", Font.PLAIN, 11));
                g2.drawString("LOCAL_BUS", centerX - 150, centerY - 15);
                g2.drawString("AI_KERNEL", centerX + 100, centerY - 15);

                // Orbiting Signal Particle
                double angle = (clockCycleCounter * 0.1) % (2 * Math.PI);
                int orbX = centerX + (int) (120 * Math.cos(angle)) - 6;
                int orbY = centerY + (int) (50 * Math.sin(angle)) - 6;
                
                if (registerA != registerB) {
                    g2.setColor(alertRed); // Anomaly state
                    g2.drawString("PARITY ERROR: 1 != 0 DETECTED", centerX - 90, centerY + 35);
                } else {
                    g2.setColor(accentGreen);
                }
                g2.fillOval(orbX, orbY, 12, 12);
                
                // Center Invariant Shield Anchor
                g2.setColor(Color.WHITE);
                g2.drawRect(centerX - 40, centerY - 20, 80, 40);
                g2.drawString("1 == 1", centerX - 20, centerY + 5);
            }
        };
        pnlVisualizer.setBorder(BorderFactory.createLineBorder(accentGreen));

        // System Log Terminal
        txtLog = new JTextArea();
        txtLog.setBackground(bgDark);
        txtLog.setForeground(accentGreen);
        txtLog.setFont(monoFont);
        txtLog.setEditable(false);
        JScrollPane scrollLog = new JScrollPane(txtLog);
        scrollLog.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(accentGreen), "PARITY ARCHITECTURE EXECUTION LOG", 0, 0, monoFont, accentGreen));

        pnlCenter.add(pnlVisualizer);
        pnlCenter.add(scrollLog);
        add(pnlCenter, BorderLayout.CENTER);

        // --- BOTTOM CONTROLS INTERFACE ---
        JPanel pnlControls = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        pnlControls.setBackground(panelDark);

        lblStatus = new JLabel("SYSTEM INTERFACE STATE: RUNNING PARITY SEEK ");
        lblStatus.setForeground(accentGreen);
        lblStatus.setFont(monoFont);

        btnInjectAnomaly = new JButton("INJECT FLUX ANOMALY (1=0)");
        btnInjectAnomaly.setFont(monoFont);
        btnInjectAnomaly.setBackground(new Color(40, 20, 20));
        btnInjectAnomaly.setForeground(alertRed);
        btnInjectAnomaly.addActionListener(e -> injectFluxAnomaly());

        btnFlush = new JButton("FORCE SECURITY FLUSH");
        btnFlush.setFont(monoFont);
        btnFlush.setBackground(new Color(20, 40, 30));
        btnFlush.setForeground(accentGreen);
        btnFlush.addActionListener(e -> performSecurityFlush());

        pnlControls.add(lblStatus);
        pnlControls.add(btnInjectAnomaly);
        pnlControls.add(btnFlush);
        add(pnlControls, BorderLayout.SOUTH);

        logMessage("[SYSTEM INITIALIZED] Invariant Law loaded into Microcode. Parity engine seeking...");
    }

    private JLabel createTelemetryLabel(String text, Color color, Font font) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(color);
        label.setFont(font);
        return label;
    }

    private void startBusClock() {
        // Microcosmic Orbit Clock Simulator running at 100ms ticks (10Hz Local Bus)
        busTimer = new SharedTimer(100, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                if (!systemActive) return;

                clockCycleCounter++;
                lblClock.setText("CLOCK: " + clockCycleCounter);

                // Simulate atomic hardware flux background noise
                thermalEntropy += (Math.random() - 0.5) * 0.4;
                lblEntropy.setText(String.format("FLUX_TEMP: %.2fK", thermalEntropy));

                // Automated Parity Seek Loop Check
                if (registerA != registerB) {
                    lblVirtue.setText("VIRTUE: ALERT");
                    lblVirtue.setForeground(Color.RED);
                    logMessage("[CRITICAL ERROR] Contradiction detected in registers! (" + registerA + " != " + registerB + "). Resolving via Invariant Matrix...");
                    autoHealCircuit();
                } else {
                    lblVirtue.setText("VIRTUE: 100%");
                    lblVirtue.setForeground(new Color(50, 220, 120));
                }

                pnlVisualizer.repaint();
            }
        });
        busTimer.start();
    }

    private void injectFluxAnomaly() {
        // Break binary identity temporarily to simulate thermal/quantum state logic drift (1 = 0 condition)
        registerB = 0; 
        lblRegB.setText("REG_B: 0");
        lblStatus.setText("SYSTEM INTERFACE STATE: ENTROPY CONTRADITION");
        lblStatus.setForeground(Color.RED);
        logMessage("[ANOMALY INJECTED] Microcosmic orbit destabilized by physical layer flux.");
    }

    private void autoHealCircuit() {
        // Automatic enforcement of invariant primitive: Force system parameters to match baseline identity
        registerB = 1;
        lblRegB.setText("REG_B: 1");
        lblStatus.setText("SYSTEM INTERFACE STATE: RECONCILED BY INVARIANT SHIELD");
        lblStatus.setForeground(new Color(50, 220, 120));
        logMessage("[AUTOMATED ASCENSION] Invariant applied successfully. Matrix structuralized back to 1 = 1.");
    }

    private void performSecurityFlush() {
        // Manually flush all opaque contrasting processing layers out of active bus registers
        thermalEntropy = 293.15;
        clockCycleCounter = 0;
        txtLog.setText("");
        logMessage("[SECURITY FLUSH ACTIVE] Opaque background layers evacuated. Telemetry loops set cleanly to zero-point.");
    }

    private void logMessage(String msg) {
        txtLog.append(msg + "\n");
        txtLog.setCaretPosition(txtLog.getDocument().getLength());
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            FluxInterfaceBus ui = new FluxInterfaceBus();
            ui.setVisible(true);
        });
    }
}
