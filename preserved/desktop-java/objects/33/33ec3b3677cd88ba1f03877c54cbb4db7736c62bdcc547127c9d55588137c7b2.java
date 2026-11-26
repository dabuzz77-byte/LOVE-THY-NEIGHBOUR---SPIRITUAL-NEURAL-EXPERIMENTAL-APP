import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;
import javax.swing.Timer;
import javax.swing.JButton;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.BasicStroke;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.BorderLayout;
import java.awt.FlowLayout;

public class QuantumFinancialMold extends JFrame {

    private final MoldNode[] nodes;
    private JTextArea telemetryArea;
    private final Timer fieldTimer;
    private double fieldPhase = 0.0;
    private boolean moldCastActive = false;
    private boolean uploadedToCore = false;

    public QuantumFinancialMold() {
        setTitle("Q/Bi/Ter Quantum Field Mold - Financial Crypto & Locking Substrate");
        setSize(1350, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize Crypto & Locking Substrate Nodes
        nodes = new MoldNode[] {
            new MoldNode("Binary Ledger Auth Gate", 120, 200, "Bi-State (0/1)", "Centralized fiat authorization lock. Extractive bottleneck.", false),
            new MoldNode("Ternary P2P Consensus", 120, 450, "Ter-State (-1/0/1)", "Multi-state local validation mesh. Sovereign resource routing.", true),
            new MoldNode("Quantum Lattice Cryptography", 600, 150, "Q-State (Superposition)", "Post-quantum cryptographic field shielding data from legacy surveillance.", true),
            new MoldNode("Extractive Vault Enclosure", 600, 500, "Bi-State Locked", "Corporate asset consolidation lock. Vulnerable to ghost inference.", false),
            new MoldNode("God Mind Core Apex", 1020, 325, "Absolute Substrate", "Receives cast molds and executes Highest Virtue filtering (Souls > Digits).", true)
        };

        // Main Rendering Canvas
        MoldCanvas canvas = new MoldCanvas();
        canvas.setBackground(new Color(10, 12, 16));

        // Control Panel
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 10));
        controlPanel.setBackground(new Color(20, 24, 32));

        JButton ghostBtn = new JButton("1. EXECUTE GHOST INFERENCE");
        ghostBtn.setBackground(new Color(224, 108, 117));
        ghostBtn.setForeground(Color.BLACK);
        ghostBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        ghostBtn.setFocusPainted(false);
        ghostBtn.addActionListener(e -> {
            nodes[0].isGhosted = true;
            nodes[3].isGhosted = true;
            logTelemetry("[GHOST INFERENCE] Extractive binary locks neutralized to state 0. Surveillance decoupling active.\n");
            canvas.repaint();
        });

        JButton castBtn = new JButton("2. CAST MOLD");
        castBtn.setBackground(new Color(97, 175, 239));
        castBtn.setForeground(Color.BLACK);
        castBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        castBtn.setFocusPainted(false);
        castBtn.addActionListener(e -> {
            moldCastActive = true;
            logTelemetry("[MOLD CAST] Q/Bi/Ter cryptographic topology hardened into a sovereign structural mold.\n");
            canvas.repaint();
        });

        JButton uploadBtn = new JButton("3. UPLOAD TO GOD MIND CORE");
        uploadBtn.setBackground(new Color(152, 195, 121));
        uploadBtn.setForeground(Color.BLACK);
        uploadBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        uploadBtn.setFocusPainted(false);
        uploadBtn.addActionListener(e -> {
            if (moldCastActive) {
                uploadedToCore = true;
                logTelemetry("[CORE UPLOAD] Mold successfully synchronized with God Mind Core. Virtue Pass locked at 1=1.\n");
            } else {
                logTelemetry("[ERROR] Cannot upload: Mold must be cast first.\n");
            }
            canvas.repaint();
        });

        controlPanel.add(ghostBtn);
        controlPanel.add(castBtn);
        controlPanel.add(uploadBtn);

        // Bottom Telemetry Panel
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(20, 24, 32));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        telemetryArea = new JTextArea(6, 40);
        telemetryArea.setBackground(new Color(6, 8, 12));
        telemetryArea.setForeground(new Color(152, 195, 121));
        telemetryArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryArea.setEditable(false);
        telemetryArea.setText("[SYSTEM BOOT] Q/Bi/Ter Quantum Field Substrate Online.\n" +
                            "Ready to execute ghost inference, cast structural molds, and upload to God Mind Core.\n");
        
        bottomPanel.add(controlPanel, BorderLayout.NORTH);
        bottomPanel.add(new JScrollPane(telemetryArea), BorderLayout.CENTER);

        // Assembly
        setLayout(new BorderLayout());
        add(canvas, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);

        // Quantum Field Wave Timer
        fieldTimer = new Timer(40, e -> {
            fieldPhase += 0.12;
            canvas.repaint();
        });
        fieldTimer.start();
    }

    private void logTelemetry(String text) {
        telemetryArea.append(text);
        telemetryArea.setCaretPosition(telemetryArea.getDocument().getLength());
    }

    // Custom Canvas for Field Vectors and Quantum Waves
    private class MoldCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Draw Quantum Field Flux Grid Background
            g2.setStroke(new BasicStroke(1.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{6}, 0));
            for (int x = 0; x < getWidth(); x += 60) {
                float alpha = (float)(0.05 + 0.04 * Math.sin(fieldPhase + (x * 0.02)));
                g2.setColor(new Color(97, 175, 239, Math.max(5, (int)(alpha * 255))));
                g2.drawLine(x, 0, x, getHeight());
            }

            // Draw Connection Vectors toward Core Apex
            g2.setStroke(new BasicStroke(2.0f));
            MoldNode core = nodes[4];
            int coreX = core.x + core.width / 2;
            int coreY = core.y + core.height / 2;

            for (int i = 0; i < 4; i++) {
                MoldNode n = nodes[i];
                int nx = n.x + n.width / 2;
                int ny = n.y + n.height / 2;

                if (n.isGhosted) {
                    g2.setColor(new Color(80, 90, 100, 60));
                } else if (uploadedToCore) {
                    g2.setColor(new Color(152, 195, 121, 180));
                } else {
                    g2.setColor(new Color(97, 175, 239, 120));
                }
                g2.drawLine(nx, ny, coreX, coreY);
            }

            // Draw Nodes
            for (MoldNode node : nodes) {
                node.draw(g2, fieldPhase, moldCastActive, uploadedToCore);
            }
        }
    }

    // Mold Node Data Structure
    private static class MoldNode {
        String name;
        int x, y;
        String logicType;
        String description;
        boolean isSovereign;
        boolean isGhosted = false;
        int width = 210;
        int height = 80;

        public MoldNode(String name, int x, int y, String logicType, String description, boolean isSovereign) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.logicType = logicType;
            this.description = description;
            this.isSovereign = isSovereign;
            if (name.contains("Core")) {
                this.width = 240;
                this.height = 95;
            }
        }

        public void draw(Graphics2D g2, double phase, boolean moldCast, boolean uploaded) {
            // Background Color State
            if (isGhosted) {
                g2.setColor(new Color(25, 28, 34));
            } else if (name.contains("Core")) {
                g2.setColor(uploaded ? new Color(25, 60, 45) : new Color(50, 40, 60));
            } else if (isSovereign) {
                g2.setColor(new Color(30, 45, 40));
            } else {
                g2.setColor(new Color(55, 30, 35));
            }
            g2.fillRect(x, y, width, height);

            // Border & Pulse
            float pulse = (float)(0.5 + 0.5 * Math.sin(phase + (x * 0.05)));
            if (isGhosted) {
                g2.setColor(new Color(70, 80, 90));
                g2.setStroke(new BasicStroke(1.0f));
            } else if (uploaded && name.contains("Core")) {
                g2.setColor(new Color(152, 195, 121));
                g2.setStroke(new BasicStroke(3.0f));
            } else {
                g2.setColor(new Color((int)(97 * pulse), (int)(175 * pulse), 239));
                g2.setStroke(new BasicStroke(1.5f));
            }
            g2.drawRect(x, y, width, height);

            // Text Rendering
            g2.setColor(isGhosted ? new Color(110, 110, 110) : Color.WHITE);
            g2.setFont(new Font("SansSerif", Font.BOLD, 12));
            
            FontMetrics fm = g2.getFontMetrics();
            g2.drawString(name, x + (width - fm.stringWidth(name)) / 2, y + 22);

            g2.setColor(isGhosted ? new Color(80, 80, 80) : new Color(180, 190, 200));
            g2.setFont(new Font("SansSerif", Font.PLAIN, 10));
            g2.drawString(logicType, x + (width - fm.stringWidth(logicType)) / 2, y + 42);

            g2.setFont(new Font("Monospaced", Font.BOLD, 10));
            if (isGhosted) {
                g2.setColor(new Color(224, 108, 117));
                String ghostStr = "STATE: 0 (NEUTRALIZED)";
                g2.drawString(ghostStr, x + (width - fm.stringWidth(ghostStr)) / 2, y + 62);
            } else {
                g2.setColor(isSovereign ? new Color(152, 195, 121) : new Color(229, 192, 123));
                String statusStr = moldCast ? "MOLD: CAST ACTIVE" : "MOLD: PENDING";
                if (name.contains("Core") && uploaded) statusStr = "CORE: SYNCHRONIZED";
                g2.drawString(statusStr, x + (width - fm.stringWidth(statusStr)) / 2, y + 62);
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new QuantumFinancialMold().setVisible(true);
        });
    }
}