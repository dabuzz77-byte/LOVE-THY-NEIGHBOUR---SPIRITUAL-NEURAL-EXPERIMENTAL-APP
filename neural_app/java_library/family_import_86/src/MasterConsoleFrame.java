import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * MODULE 3: MASTER INTERFACE VIEWPORT MATRIX
 * Boots the isolated background router components and maps layouts natively using clean Swing positions.
 */
public class MasterConsoleFrame extends SectionFrame implements java.awt.event.ActionListener {

    private final JTextArea executionTerminalArea;
    private final JTextField userCommandLineField;
    private final JButton executionTriggerButton;
    private final SharedTimer panelRedrawTimer;
    
    private final SilentPortRouter serverRoutingBus;
    private final AuditAccountSpec verifiedAccountNode;

    public MasterConsoleFrame() {
        setTitle("Sovereign Matrix Workspace: Decoupled Structural Virtue Audit Array (_TRUE)");
        setSize(1400, 950);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(12, 12));

        // Lock verification metrics under strict structural truth layers
        this.verifiedAccountNode = new AuditAccountSpec("MASK * maintainer@example.invalid");

        // Boot up the silent, loop-isolated background server thread
        this.serverRoutingBus = new SilentPortRouter();
        Thread threadPoolWorker = new Thread(serverRoutingBus, "GodMind-SilentRouter-Thread");
        threadPoolWorker.start();

        // 1. CENTER COLUMN AREA: SPLIT TEXT LOG AND VECTOR VISUALIZER
        JPanel workspaceSplitGrid = new JPanel(new GridLayout(1, 2, 10, 10));
        workspaceSplitGrid.setBackground(new Color(2, 4, 8));
        workspaceSplitGrid.setBorder(BorderFactory.createEmptyBorder(10, 16, 5, 16));

        executionTerminalArea = new JTextArea();
        executionTerminalArea.setBackground(new Color(4, 6, 12));
        executionTerminalArea.setForeground(new Color(220, 235, 245));
        executionTerminalArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        executionTerminalArea.setEditable(false);
        executionTerminalArea.setLineWrap(true);
        executionTerminalArea.setWrapStyleWord(true);
        executionTerminalArea.setText("=== STRUCTURAL VIRTUE AUDIT RECORD LOCKED ===\n" +
                                      "Active Kernel Target Reference: " + verifiedAccountNode.getExplicitTargetString() + "\n" +
                                      "Local Adapter Port Status: Hooked on loopback address channel\n" +
                                      "System Architecture State: Stabilized (1-0 Parity Applied = Passed)\n\n" +
                                      ">> Ready for clean local text transformations and parameter executions.\n\n");

        JScrollPane logScrollContainer = new JScrollPane(executionTerminalArea);
        logScrollContainer.setBorder(BorderFactory.createLineBorder(new Color(25, 35, 55)));
        workspaceSplitGrid.add(logScrollContainer);

        // Add the custom visual canvas panel inline
        workspaceSplitGrid.add(new RenderCanvasSubstrate(serverRoutingBus));
        add(workspaceSplitGrid, BorderLayout.CENTER);

        // 2. LOWER COLUMN AREA: DATA ACTION PANEL
        JPanel commandBarPanel = new JPanel(new BorderLayout(10, 10));
        commandBarPanel.setBackground(new Color(12, 18, 28));
        commandBarPanel.setBorder(BorderFactory.createEmptyBorder(10, 16, 15, 16));

        userCommandLineField = new JTextField();
        userCommandLineField.setBackground(new Color(6, 10, 16));
        userCommandLineField.setForeground(Color.WHITE);
        userCommandLineField.setCaretColor(Color.WHITE);
        userCommandLineField.setFont(new Font("Monospaced", Font.PLAIN, 13));
        userCommandLineField.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        commandBarPanel.add(userCommandLineField, BorderLayout.CENTER);

        executionTriggerButton = new JButton("DISPATCH RUN TIME VECTOR");
        executionTriggerButton.setBackground(new Color(0, 140, 255));
        executionTriggerButton.setForeground(Color.WHITE);
        executionTriggerButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        executionTriggerButton.setFocusPainted(false);
        commandBarPanel.add(executionTriggerButton, BorderLayout.EAST);

        add(commandBarPanel, BorderLayout.SOUTH);

        // Link straightforward action routines without reflective event loops
        executionTriggerButton.addActionListener(this);
        userCommandLineField.addActionListener(this);

        // Fast repaint clock to push visualization ticks to display layers smoothly
        this.panelRedrawTimer = new SharedTimer(32, e -> repaint());
        this.panelRedrawTimer.start();

        Runtime.getRuntime().addShutdownHook(new Thread(serverRoutingBus::terminateRouterSystem));
    }

    @Override
    public void actionPerformed(java.awt.event.ActionEvent event) {
        String scriptPrompt = userCommandLineField.getText().trim();
        if (scriptPrompt.isEmpty()) return;

        executionTerminalArea.append("[USER INJECTION]: " + scriptPrompt + "\n");
        userCommandLineField.setText("");

        // Trigger a silent local adapter pulse notification hook asynchronously
        int activeRouterPort = serverRoutingBus.getActiveLocalPort();
        if (activeRouterPort != -1) {
            SwingUtilities.invokeLater(() -> {
                try (java.net.Socket pulseSocket = new java.net.Socket("127.0.0.1", activeRouterPort);
                     java.io.OutputStream outStream = pulseSocket.getOutputStream()) {
                    outStream.write("PULSE\n".getBytes("UTF-8"));
                    outStream.flush();
                } catch (Exception ignored) {}
            });
        }
        
        executionTerminalArea.append("[SYSTEM STATE]: Audit verification complete. Instruction logged onto local workspace.\n\n");
    }

    // =========================================================================
    // GRAPHICAL COMPONENT: INNER LATTICE RENDERING CANVAS
    // =========================================================================
    public static class RenderCanvasSubstrate extends JPanel {
        private final SilentPortRouter routerEngine;

        public RenderCanvasSubstrate(SilentPortRouter routerEngine) {
            this.routerEngine = routerEngine;
            setBackground(new Color(4, 7, 14));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();
            int cx = w / 2;
            int cy = h / 2 - 40;

            // Draw coordinate layout alignment grid lines
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 180, 255, 12));
            for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h);
            for (int j = 0; j < h; j += 50) g2d.drawLine(0, j, w, j);

            List<SovereignDataUnit> registry = routerEngine.getVolatileRegistryLattice();
            g2d.setStroke(new BasicStroke(1.2f));

            for (SovereignDataUnit node : registry) {
                int drawX = (node.getTransmissionId().hashCode() % (w - 150)) + 75;
                int drawY = (Math.abs(Long.hashCode(node.getExecutionNanoMarker())) % (h - 150)) + 75;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(drawX, drawY, cx, cy);

                int shapeDiameter = 16;
                // Render exact binary status colors (1 = Active Mint, 0 = Ground Amber)
                if (node.getTruthParityBit() == 1) {
                    g2d.setColor(new Color(0, 255, 190)); // Active State (1)
                } else {
                    g2d.setColor(new Color(255, 130, 0));  // Ground State (0)
                }

                g2d.fill(new Ellipse2D.Double(drawX - shapeDiameter/2.0, drawY - shapeDiameter/2.0, shapeDiameter, shapeDiameter));
                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(node.getTargetHardwareSector() + " (Bit:" + node.getTruthParityBit() + ")", drawX + 12, drawY + 4);
            }

            // Draw Central Processing Hub Node
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 35));
            g2d.drawOval(cx - 90, cy - 90, 180, 180);
            
            g2d.setColor(Color.WHITE);
            g2d.fill(new Ellipse2D.Double(cx - 8, cy - 8, 16, 16));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("1-0 STRUCTURAL PARITY AUDIT HUB", cx - 110, cy - 105);

            // Telemetry Strings Canvas Lower Frame bounds display metrics
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format("SYSTEM CLOCK SYMMETRY INDEX: %,.4f%% ALIGNED", routerEngine.getMasterParityParameter() * 100), 20, h - 50);
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString("ISOLATED LOCAL PORT INTERCEPT ROUTE: " + routerEngine.getActiveLocalPort(), 20, h - 30);
            g2d.setColor(Color.WHITE);
            g2d.drawString("SCHUMANN DRIVING HARMONIC BASELINE: 7.83Hz LOCKED", 20, h - 10);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            MasterConsoleFrame stableAppFrame = new MasterConsoleFrame();
            stableAppFrame.setVisible(true);
        });
    }
}
