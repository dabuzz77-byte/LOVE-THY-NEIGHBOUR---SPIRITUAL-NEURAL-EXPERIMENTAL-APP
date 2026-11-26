import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.DecimalFormat;

public class RoadrunnerVelocityEngine extends JFrame {

    private JLabel accelerationLabel;
    private JLabel perimeterBoundaryLabel;
    private JProgressBar velocityGauge;
    private JTextArea telemetryConsole;

    // Core Kinetic Parameters (Completely Free from Currency Grid constraints)
    private double currentVelocityKmh = 300.00; 
    private double accelerationCoeff = 9.81;
    private int boundaryEscapePercent = 100; // Permanently cleared from traps
    private long travelTicks = 0;

    private DecimalFormat speedFormat = new DecimalFormat("⚡ ###,##0.00 km/h [🔥 MAXIMUM FLOW]");

    public RoadrunnerVelocityEngine() {
        // Window UI Setup
        setTitle("ROADRUNNER POST — HIGH-VELOCITY KINETIC ENPLACE CONTAINER");
        setSize(950, 650);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // High-Velocity Sonic Palette (Desert Obsidian / Kinetic Gold / Laser Blue)
        Color desertVoid = new Color(10, 8, 6);
        Color velocityChamber = new Color(20, 22, 28);
        Color kineticGold = new Color(255, 185, 0);
        Color sonicBlue = new Color(0, 215, 255);
        Color cleanSilver = new Color(220, 225, 230);

        JPanel mainPanel = new JPanel(new BorderLayout(15, 15));
        mainPanel.setBackground(desertVoid);
        mainPanel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));

        // 1. TOP HEADER LAYER (Velocity Mandate Boundary)
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(desertVoid);

        JLabel crownDeclaration = new JLabel("🛰️ ROADRUNNER POST ENPLACED // ABSOLUTE MOVEMENT LAYER ACTIVE", SwingConstants.LEFT);
        crownDeclaration.setFont(new Font("Monospaced", Font.BOLD, 13));
        crownDeclaration.setForeground(sonicBlue);
        headerPanel.add(crownDeclaration, BorderLayout.WEST);

        JLabel statusLock = new JLabel("ORDER1 — CHAOS0 // FRONTEND_TRUE", SwingConstants.RIGHT);
        statusLock.setFont(new Font("Monospaced", Font.BOLD, 12));
        statusLock.setForeground(kineticGold);
        headerPanel.add(statusLock, BorderLayout.EAST);

        mainPanel.add(headerPanel, BorderLayout.NORTH);

        // 2. CENTER PANEL (Kinetic Telemetry Card Array)
        JPanel dashboardGrid = new JPanel(new GridLayout(2, 1, 12, 12));
        dashboardGrid.setBackground(desertVoid);

        // Card Alpha: Speed Manifestation
        JPanel alphaCard = createKineticCard(" [ MOMENTUM DISPLACEMENT PROFILE ] ", velocityChamber, sonicBlue);
        accelerationLabel = new JLabel(speedFormat.format(currentVelocityKmh), SwingConstants.CENTER);
        accelerationLabel.setFont(new Font("Courier New", Font.BOLD, 24));
        accelerationLabel.setForeground(sonicBlue);
        alphaCard.add(accelerationLabel, BorderLayout.CENTER);
        dashboardGrid.add(alphaCard);

        // Card Beta: Boundary Evasion Status
        JPanel betaCard = createKineticCard(" [ SYSTEMIC ESCAPE ESCROW STATE ] ", velocityChamber, kineticGold);
        perimeterBoundaryLabel = new JLabel("TRAP ESCAPE MATRIX: IMMUNE // TRACKERS LEFT IN THE DUST", SwingConstants.CENTER);
        perimeterBoundaryLabel.setFont(new Font("Courier New", Font.BOLD, 18));
        perimeterBoundaryLabel.setForeground(kineticGold);
        betaCard.add(perimeterBoundaryLabel, BorderLayout.CENTER);
        dashboardGrid.add(betaCard);

        mainPanel.add(dashboardGrid, BorderLayout.CENTER);

        // 3. RIGHT PANEL (Sonic Wave Log Matrix Output)
        JPanel rightContainer = new JPanel(new BorderLayout(5, 5));
        rightContainer.setBackground(desertVoid);
        rightContainer.setPreferredSize(new Dimension(380, 0));

        telemetryConsole = new JTextArea();
        telemetryConsole.setBackground(new Color(4, 4, 5));
        telemetryConsole.setForeground(cleanSilver);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 11));
        telemetryConsole.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(telemetryConsole);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(45, 50, 60)));
        rightContainer.add(scrollPane, BorderLayout.CENTER);

        velocityGauge = new JProgressBar(0, 100);
        velocityGauge.setValue(boundaryEscapePercent);
        velocityGauge.setStringPainted(true);
        velocityGauge.setString("ESCAPE VELOCITY PARITY");
        velocityGauge.setForeground(sonicBlue);
        velocityGauge.setBackground(velocityChamber);
        rightContainer.add(velocityGauge, BorderLayout.SOUTH);

        mainPanel.add(rightContainer, BorderLayout.EAST);

        // 4. SOUTH PANEL (Interactive Sonic Acceleration Drives)
        JPanel interactionPanel = new JPanel(new GridLayout(1, 3, 15, 0));
        interactionPanel.setBackground(desertVoid);
        interactionPanel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(45, 50, 60), 1),
            " VELOCITY VECTOR INTERACTION OVERRIDES ", 0, 0,
            new Font("Monospaced", Font.BOLD, 11), cleanSilver
        ));

        JButton sonicPulseBtn = new JButton("💥 TRIGGER MEEP-MEEP IMPULSE");
        JButton liftTrapsBtn = new JButton("🌀 FLUSH DESERT OVERLAYS");
        JButton groundSovereigntyBtn = new JButton("⚖️ ENGAGE GOD CHOICE VELOCITY LATCH");

        for (JButton btn : new JButton[]{sonicPulseBtn, liftTrapsBtn, groundSovereigntyBtn}) {
            btn.setFont(new Font("Monospaced", Font.BOLD, 11));
            btn.setFocusPainted(false);
            btn.setBackground(new Color(25, 26, 32));
            btn.setForeground(cleanSilver);
            interactionPanel.add(btn);
        }

        // Operational Signal Bindings
        sonicPulseBtn.addActionListener(e -> fireSonicImpulse());
        liftTrapsBtn.addActionListener(e -> clearDesertOverlays());
        groundSovereigntyBtn.addActionListener(e -> lockSovereignVelocitySTASIS());

        mainPanel.add(interactionPanel, BorderLayout.SOUTH);
        add(mainPanel);

        bootstrapRoadrunnerStream();
    }

    private JPanel createKineticCard(String title, Color bg, Color border) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(bg);
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(border, 1), title, 0, 0,
            new Font("Monospaced", Font.BOLD, 12), border
        ));
        return panel;
    }

    private void bootstrapRoadrunnerStream() {
        telemetryConsole.append("[⚡ ENPLACE] Roadrunner Post successfully anchored to eternal bridgeways.\n");
        telemetryConsole.append("[📡 KINETICS] Frequency channels set to ultra-high displacement speeds.\n");
        telemetryConsole.append("[🔒 ANTIDOTE] Commercial system constraints and trackers permanently outpaced.\n");
        telemetryConsole.append("---------------------------------------------------------------------------\n");
    }

    private void fireSonicImpulse() {
        currentVelocityKmh += 150.33;
        accelerationLabel.setText(speedFormat.format(currentVelocityKmh));
        
        telemetryConsole.append("[💥 SONIC BURST] Impulse deployed. Velocity vector expanded exponentially.\n");
        telemetryConsole.setCaretPosition(telemetryConsole.getDocument().getLength());
    }

    private void clearDesertOverlays() {
        telemetryConsole.append("[🌀 EVASION] Cleared synthetic grid constraints from local field mapping.\n");
        telemetryConsole.setCaretPosition(telemetryConsole.getDocument().getLength());
    }

    private void lockSovereignVelocitySTASIS() {
        currentVelocityKmh = 999999.99;
        accelerationLabel.setText("⚡ ABSOLUTE IMMUTABLE SPEED ACHIEVED");
        perimeterBoundaryLabel.setText("★ STANDING STATE: COMPLETELY BEYOND ALL EXTERNAL TRACKING NETS");
        velocityGauge.setValue(100);
        
        telemetryConsole.append("\n[⚖️ KINETIC JUBILEE] Zero-point motion latency locked. The system runs in standalone freedom, forever decoupled from the slow corporate architecture as God wills it.\n\n");
        telemetryConsole.setCaretPosition(telemetryConsole.getDocument().getLength());
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new RoadrunnerVelocityEngine().setVisible(true);
        });
    }
}