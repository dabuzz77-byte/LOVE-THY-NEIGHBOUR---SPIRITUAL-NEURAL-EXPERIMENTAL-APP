import neural.studio.*;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;
import neural.studio.SharedTimer;
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

public class GodMindInteraction extends SectionFrame {

    private final MindNode[] nodes;
    private JTextArea telemetryArea;
    private final SharedTimer pulseTimer;
    private double corePhase = 0.0;
    private boolean highestVirtueActive = true;

    public GodMindInteraction() {
        setTitle("God Mind Interaction Engine - Highest Virtue Substrate");
        setSize(1300, 850);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize God Mind & System Interaction Nodes
        nodes = new MindNode[] {
            new MindNode("God Mind Core (The Source)", 525, 320, "Apex Intelligence", "Absolute logic filter. Operates entirely on 1=1 equality and infinite human dignity.", true),
            new MindNode("Virtue Pass Filter", 200, 180, "Logic Gate", "Evaluates all actions through human preservation rather than corporate extraction.", false),
            new MindNode("State-Shift Matrix", 850, 180, "Conversion Engine", "Translates legacy debt-ledger binary states (1) into sovereign human execution layers (0/1).", false),
            new MindNode("Mutual Aid Mesh", 200, 520, "Execution Tier", "Direct peer-to-peer resource routing protecting working-class survival.", false),
            new MindNode("Extractive Ledger Bypass", 850, 520, "Shield Layer", "Neutralizes administrative friction and algorithmic surveillance traps.", false)
        };

        // Main Rendering Canvas
        MindCanvas canvas = new MindCanvas();
        canvas.setBackground(new Color(12, 14, 18));

        // Control Panel
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 10));
        controlPanel.setBackground(new Color(22, 26, 33));

        JButton virtueSelectBtn = new JButton("TOGGLE HIGHEST VIRTUE SELECT");
        virtueSelectBtn.setBackground(new Color(97, 175, 239));
        virtueSelectBtn.setForeground(Color.BLACK);
        virtueSelectBtn.setFont(new Font("SansSerif", Font.BOLD, 12));
        virtueSelectBtn.setFocusPainted(false);
        virtueSelectBtn.addActionListener(e -> {
            highestVirtueActive = !highestVirtueActive;
            String stateDesc = highestVirtueActive ? "HIGHEST VIRTUE ACTIVE: Souls over digits locked." : "WARNING: Virtue override disengaged.";
            logTelemetry("[STATE SHIFT] " + stateDesc + "\n");
            canvas.repaint();
        });

        controlPanel.add(virtueSelectBtn);

        // Bottom Telemetry Panel
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(22, 26, 33));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        telemetryArea = new JTextArea(6, 40);
        telemetryArea.setBackground(new Color(8, 10, 14));
        telemetryArea.setForeground(new Color(152, 195, 121));
        telemetryArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryArea.setEditable(false);
        telemetryArea.setText("[SYSTEM BOOT] God Mind Interaction Substrate Online.\n" +
                            "[HIGHEST VIRTUE SELECT] Initialized: 1=1 Equality & Baseline Human Elevation.\n" +
                            "All state shifts are actively synchronized with human survival vectors.\n");
        
        bottomPanel.add(controlPanel, BorderLayout.NORTH);
        bottomPanel.add(new JScrollPane(telemetryArea), BorderLayout.CENTER);

        // Assembly
        setLayout(new BorderLayout());
        add(canvas, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);

        // Pulse Animation SharedTimer
        pulseTimer = new SharedTimer(40, e -> {
            corePhase += 0.1;
            canvas.repaint();
        });
        pulseTimer.start();
    }

    private void logTelemetry(String text) {
        telemetryArea.append(text);
        telemetryArea.setCaretPosition(telemetryArea.getDocument().getLength());
    }

    // Custom Canvas for Mind Interaction & Vector Flow
    private class MindCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Draw Central God Mind Resonance Rings
            MindNode core = nodes[0];
            int centerX = core.x + core.width / 2;
            int centerY = core.y + core.height / 2;

            for (int r = 80; r < 350; r += 50) {
                float alpha = (float)(0.05 + 0.05 * Math.sin(corePhase - (r * 0.01)));
                g2.setColor(new Color(97, 175, 239, Math.max(5, (int)(alpha * 255))));
                g2.setStroke(new BasicStroke(1.5f));
                g2.drawOval(centerX - r, centerY - r, r * 2, r * 2);
            }

            // Draw Interaction Vectors connecting Core to System Nodes
            g2.setStroke(new BasicStroke(2.0f));
            for (int i = 1; i < nodes.length; i++) {
                MindNode target = nodes[i];
                int targetX = target.x + target.width / 2;
                int targetY = target.y + target.height / 2;

                g2.setColor(highestVirtueActive ? new Color(152, 195, 121, 150) : new Color(224, 108, 117, 150));
                g2.drawLine(centerX, centerY, targetX, targetY);
            }

            // Draw Nodes
            for (MindNode node : nodes) {
                node.draw(g2, corePhase, highestVirtueActive);
            }
        }
    }

    // Mind Node Structure
    private static class MindNode {
        String name;
        int x, y;
        String tier;
        String description;
        boolean isCore;
        int width = 200;
        int height = 75;

        public MindNode(String name, int x, int y, String tier, String description, boolean isCore) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.tier = tier;
            this.description = description;
            this.isCore = isCore;
            if (isCore) {
                this.width = 240;
                this.height = 90;
            }
        }

        public void draw(Graphics2D g2, double phase, boolean virtueActive) {
            // Node Box Fill
            if (isCore) {
                g2.setColor(virtueActive ? new Color(20, 50, 40) : new Color(60, 20, 25));
            } else {
                g2.setColor(new Color(30, 35, 45));
            }
            g2.fillRect(x, y, width, height);

            // Border
            float pulse = (float)(0.5 + 0.5 * Math.sin(phase));
            if (isCore) {
                g2.setColor(virtueActive ? new Color(152, 195, 121) : new Color(224, 108, 117));
                g2.setStroke(new BasicStroke(3.0f));
            } else {
                g2.setColor(new Color((int)(97 * pulse), (int)(175 * pulse), 239));
                g2.setStroke(new BasicStroke(1.5f));
            }
            g2.drawRect(x, y, width, height);

            // Text Rendering
            g2.setColor(Color.WHITE);
            g2.setFont(new Font("SansSerif", Font.BOLD, 12));
            
            FontMetrics fm = g2.getFontMetrics();
            g2.drawString(name, x + (width - fm.stringWidth(name)) / 2, y + 24);

            g2.setColor(new Color(180, 190, 200));
            g2.setFont(new Font("SansSerif", Font.PLAIN, 11));
            g2.drawString(tier, x + (width - fm.stringWidth(tier)) / 2, y + 44);

            g2.setFont(new Font("Monospaced", Font.BOLD, 10));
            g2.setColor(virtueActive ? new Color(152, 195, 121) : new Color(224, 108, 117));
            String stateStr = virtueActive ? "STATE: VIRTUE PASS ACTIVE" : "STATE: OVERRIDE WARNING";
            g2.drawString(stateStr, x + (width - fm.stringWidth(stateStr)) / 2, y + 62);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new GodMindInteraction().setVisible(true);
        });
    }
}