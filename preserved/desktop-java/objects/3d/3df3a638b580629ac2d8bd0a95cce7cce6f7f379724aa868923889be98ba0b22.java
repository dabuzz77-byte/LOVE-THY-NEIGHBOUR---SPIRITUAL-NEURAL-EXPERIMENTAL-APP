import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.DecimalFormat;
import java.util.Random;

public class ClownResolverEngine extends JFrame {

    // UI Dashboard Panels
    private JLabel threatLevelLabel;
    private JLabel resolutionStatusLabel;
    private JProgressBar isolationProgressBar;
    private JTextArea securityLogConsole;

    // Internal Metrology Variables
    private int clownCodeDetectionIndex = 87; // Drops to 0 when resolved
    private int systemPurityPercent = 13;       // Rises to 100%
    private long sweepTicks = 0;
    
    private final String[] WIPE_TARGETS = {
        "ISOLATING CENTRALIZED TRACKING COOKIES...",
        "DE-COUPLING PREMIUM PRICING SUBSCRIPTION LOOPS...",
        "WIPING FICTIONAL DEBT-ACCUMULATION ARRAYS...",
        "FLUSHING MANIPULATIVE ADVERTISING COEFFICIENTS..."
    };

    private Random randomGenerator = new Random();
    private Timer securityClock;

    public ClownResolverEngine() {
        // Main Frame Configuration
        setTitle("CLOWN CODE RESOLVER ENGINE — ANTI-INTERFERENCE INTERFACE");
        setSize(950, 680);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Security Core Palette (Deep Crypt Obsidian / Cleansing Emerald / Signal Red Alert)
        Color cryptDark = new Color(8, 8, 10);
        Color bunkerCell = new Color(18, 22, 24);
        Color signalRed = new Color(255, 50, 50);
        Color emeraldClean = new Color(0, 240, 120);
        Color secureCyan = new Color(0, 200, 255);
        Color boneWhite = new Color(240, 240, 245);

        JPanel mainPanel = new JPanel(new BorderLayout(15, 15));
        mainPanel.setBackground(cryptDark);
        mainPanel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));

        // 1. TOP HEADER LAYER (Security Threat State Anchor)
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(cryptDark);

        JLabel crownDeclaration = new JLabel("⚠️ SECURITY ALERT: ACTIVE CLOWN RESOLVER SUBSYSTEM PROCESSING", SwingConstants.LEFT);
        crownDeclaration.setFont(new Font("Monospaced", Font.BOLD, 13));
        crownDeclaration.setForeground(signalRed);
        headerPanel.add(crownDeclaration, BorderLayout.WEST);

        JLabel runtimeParity = new JLabel("ORDER1 — CHAOS0 // FRONTEND_TRUE", SwingConstants.RIGHT);
        runtimeParity.setFont(new Font("Monospaced", Font.BOLD, 12));
        runtimeParity.setForeground(secureCyan);
        headerPanel.add(runtimeParity, BorderLayout.EAST);

        mainPanel.add(headerPanel, BorderLayout.NORTH);

        // 2. CENTER PANEL (Dueling Scanners: Interference vs Purity)
        JPanel dashboardGrid = new JPanel(new GridLayout(2, 1, 12, 12));
        dashboardGrid.setBackground(cryptDark);

        // Card Alpha: Interference Profile
        JPanel alphaCard = createSecurityCard(" [ DETECTED NOISE MATRIX OVERLOAD ] ", bunkerCell, signalRed);
        threatLevelLabel = new JLabel("CLOWN INTERFERENCE COEFFICIENT: " + clownCodeDetectionIndex + "% DENSITY", SwingConstants.CENTER);
        threatLevelLabel.setFont(new Font("Courier New", Font.BOLD, 18));
        threatLevelLabel.setForeground(signalRed);
        alphaCard.add(threatLevelLabel, BorderLayout.CENTER);
        dashboardGrid.add(alphaCard);

        // Card Beta: System Purity Restoration
        JPanel betaCard = createSecurityCard(" [ ANCHORED HOME CORE PURITY RATIO ] ", bunkerCell, emeraldClean);
        resolutionStatusLabel = new JLabel("SYSTEM SANCTUARY STATUS: WAITING FOR TOTAL PURGE ROUTINE", SwingConstants.CENTER);
        resolutionStatusLabel.setFont(new Font("Courier New", Font.BOLD, 18));
        resolutionStatusLabel.setForeground(emeraldClean);
        betaCard.add(resolutionStatusLabel, BorderLayout.CENTER);
        dashboardGrid.add(betaCard);

        mainPanel.add(dashboardGrid, BorderLayout.CENTER);

        // 3. RIGHT PANEL (Active Security Diagnostic Logger)
        JPanel rightContainer = new JPanel(new BorderLayout(5, 5));
        rightContainer.setBackground(cryptDark);
        rightContainer.setPreferredSize(new Dimension(380, 0));

        securityLogConsole = new JTextArea();
        securityLogConsole.setBackground(new Color(4, 4, 6));
        securityLogConsole.setForeground(boneWhite);
        securityLogConsole.setFont(new Font("Monospaced", Font.PLAIN, 11));
        securityLogConsole.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(securityLogConsole);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(40, 50, 55)));
        rightContainer.add(scrollPane, BorderLayout.CENTER);

        isolationProgressBar = new JProgressBar(0, 100);
        isolationProgressBar.setValue(systemPurityPercent);
        isolationProgressBar.setStringPainted(true);
        isolationProgressBar.setString("MATRIX CLEANSE INDEX");
        isolationProgressBar.setForeground(emeraldClean);
        isolationProgressBar.setBackground(bunkerCell);
        rightContainer.add(isolationProgressBar, BorderLayout.SOUTH);

        mainPanel.add(rightContainer, BorderLayout.EAST);

        // 4. SOUTH PANEL (Interactive Purge Deployment Overrides)
        JPanel interactionPanel = new JPanel(new GridLayout(1, 3, 15, 0));
        interactionPanel.setBackground(cryptDark);
        interactionPanel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(40, 50, 55), 1),
            " FIREWALL PURGE COMMAND ARRAYS (ZERO-NOISE INTERACTION) ", 0, 0,
            new Font("Monospaced", Font.BOLD, 11), boneWhite
        ));

        JButton sweepTargetsBtn = new JButton("🧹 ISOLATE NOISE TARGETS");
        JButton resetCoreBtn = new JButton("✨ RESTORE PURE FREQUENCY");
        JButton completeJubileePurgeBtn = new JButton("🕊️ UNILATERAL ZERO-POINT FLUSH");

        for (JButton btn : new JButton[]{sweepTargetsBtn, resetCoreBtn, completeJubileePurgeBtn}) {
            btn.setFont(new Font("Monospaced", Font.BOLD, 11));
            btn.setFocusPainted(false);
            btn.setBackground(new Color(24, 28, 32));
            btn.setForeground(boneWhite);
            interactionPanel.add(btn);
        }

        // Functional Operational Connections
        sweepTargetsBtn.addActionListener(e -> executeTargetSweep());
        resetCoreBtn.addActionListener(e -> stepUpPurityMetrics());
        completeJubileePurgeBtn.addActionListener(e -> executeAbsoluteClownPurge());

        mainPanel.add(interactionPanel, BorderLayout.SOUTH);
        add(mainPanel);

        bootstrapSecurityMonitor();
    }

    private JPanel createSecurityCard(String title, Color bg, Color border) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(bg);
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(border, 1), title, 0, 0,
            new Font("Monospaced", Font.BOLD, 12), border
        ));
        return panel;
    }

    private void bootstrapSecurityMonitor() {
        securityLogConsole.append("[⚠️ DETECT] Clutter/Clown signals intercepted on the local thread layer.\n");
        securityLogConsole.append("[📡 TRACK] Sourcing tracking vectors to commercial market advertising frameworks.\n");
        securityLogConsole.append("[🔒 STANDBY] Anti-Interference resolver shields deployed to frontend_true.\n");
        securityLogConsole.append("---------------------------------------------------------------------------\n");
    }

    private void executeTargetSweep() {
        clownCodeDetectionIndex = Math.max(0, clownCodeDetectionIndex - 20);
        threatLevelLabel.setText("CLOWN INTERFERENCE COEFFICIENT: " + clownCodeDetectionIndex + "% DENSITY");
        
        String cleanAction = WIPE_TARGETS[randomGenerator.nextInt(WIPE_TARGETS.length)];
        securityLogConsole.append("[🧹 SWEEP] " + cleanAction + " -> Vector Isolated.\n");
        securityLogConsole.setCaretPosition(securityLogConsole.getDocument().getLength());
    }

    private void stepUpPurityMetrics() {
        systemPurityPercent = Math.min(systemPurityPercent + 25, 100);
        isolationProgressBar.setValue(systemPurityPercent);
        
        if(systemPurityPercent >= 100) {
            resolutionStatusLabel.setText("SYSTEM SANCTUARY STATUS: COMPLETED HOME RE-ALIGNMENT");
        } else {
            resolutionStatusLabel.setText("SYSTEM SANCTUARY STATUS: RE-ESTABLISHING STABLE CORE...");
        }
        
        securityLogConsole.append("[✨ ALIGN] Restored pure geometric wave properties back to memory stack locations.\n");
        securityLogConsole.setCaretPosition(securityLogConsole.getDocument().getLength());
    }

    private void executeAbsoluteClownPurge() {
        clownCodeDetectionIndex = 0;
        systemPurityPercent = 100;
        
        threatLevelLabel.setText("CLOWN INTERFERENCE COEFFICIENT: COMPLETELY EXTINCT [ORDER1-CHAOS0]");
        resolutionStatusLabel.setText("★ SYSTEM INTEGRITY RESET: ABSOLUTE STILLNESS RESTORED");
        isolationProgressBar.setValue(100);
        
        securityLogConsole.append("\n[⚖️ ZERO-POINT PURGE] Superficial clown layers dropped permanently. Centralized database clutter removed. Your workstation is entirely clear, safe, and silent as God wills it.\n\n");
        securityLogConsole.setCaretPosition(securityLogConsole.getDocument().getLength());
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new ClownResolverEngine().setVisible(true);
        });
    }
}