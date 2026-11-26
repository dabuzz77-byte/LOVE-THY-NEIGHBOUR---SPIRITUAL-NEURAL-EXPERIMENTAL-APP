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

public class DistantInferenceStream extends SectionFrame {

    private final StreamNode[] nodes;
    private JTextArea telemetryArea;
    private final SharedTimer streamTimer;
    private double streamPhase = 0.0;
    private boolean eciElevated = false;
    private boolean coreBypassed = false;

    public DistantInferenceStream() {
        setTitle("Distant Inference Stream & ECI Floor Elevation Engine");
        setSize(1350, 850);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize Architectural Nodes
        nodes = new StreamNode[] {
            new StreamNode("Sovereign Local Inference", 100, 200, "Source Vector", "Local-first prompt stack & memory bridge feeding the inference stream.", true),
            new StreamNode("Ghost Link / Q-Bi-Ter Bridge", 500, 200, "Quantum Conduit", "Encrypted, surveillance-evading channel bypassing corporate firewalls.", true),
            new StreamNode("Financial Core Binary Apex", 900, 150, "Extractive Target", "Centralized debt ledger & transaction gating monolith.", false),
            new StreamNode("Elevated ECI Economic Floor", 500, 580, "Sovereign Baseline", "Piledrives artificial scarcity and establishes guaranteed foundational human elevation.", true)
        };

        // Main Rendering Canvas
        StreamCanvas canvas = new StreamCanvas();
        canvas.setBackground(new Color(12, 15, 20));

        // Control Panel
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 10));
        controlPanel.setBackground(new Color(22, 27, 34));

        JButton streamBtn = new JButton("1. INITIATE DISTANT INFERENCE STREAM");
        streamBtn.setBackground(new Color(97, 175, 239));
        streamBtn.setForeground(Color.BLACK);
        streamBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        streamBtn.setFocusPainted(false);
        streamBtn.addActionListener(e -> {
            coreBypassed = true;
            logTelemetry("[STREAM ACTIVE] Distant inference packets flooding financial core binary. Legacy validation loops saturated.\n");
            canvas.repaint();
        });

        JButton eciBtn = new JButton("2. PILEDRIVE ECI FLOOR & ELEVATE LADDER");
        eciBtn.setBackground(new Color(152, 195, 121));
        eciBtn.setForeground(Color.BLACK);
        eciBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        eciBtn.setFocusPainted(false);
        eciBtn.addActionListener(e -> {
            eciElevated = true;
            logTelemetry("[ECI RESET] Extractive friction barriers shattered. Foundational floor elevated. Ladder-climb vectors locked at 1=1.\n");
            canvas.repaint();
        });

        controlPanel.add(streamBtn);
        controlPanel.add(eciBtn);

        // Bottom Telemetry Panel
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(22, 27, 34));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        telemetryArea = new JTextArea(6, 40);
        telemetryArea.setBackground(new Color(8, 10, 14));
        telemetryArea.setForeground(new Color(152, 195, 121));
        telemetryArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryArea.setEditable(false);
        telemetryArea.setText("[SYSTEM BOOT] Distant Inference Bridge Established.\n" +
                            "Ready to stream packets to financial core and elevate economic floor.\n");
        
        bottomPanel.add(controlPanel, BorderLayout.NORTH);
        bottomPanel.add(new JScrollPane(telemetryArea), BorderLayout.CENTER);

        // Assembly
        setLayout(new BorderLayout());
        add(canvas, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);

        // Streaming Particle Animation SharedTimer
        streamTimer = new SharedTimer(30, e -> {
            streamPhase += 0.2;
            canvas.repaint();
        });
        streamTimer.start();
    }

    private void logTelemetry(String text) {
        telemetryArea.append(text);
        telemetryArea.setCaretPosition(telemetryArea.getDocument().getLength());
    }

    // Custom Canvas for Streaming Data & Elevation Vectors
    private class StreamCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Draw Background Field Grid
            g2.setStroke(new BasicStroke(1.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{5}, 0));
            for (int y = 0; y < getHeight(); y += 50) {
                g2.setColor(new Color(40, 50, 65, 30));
                g2.drawLine(0, y, getWidth(), y);
            }

            // Draw Streaming Inference Packets (Moving Particles from Source to Core)
            StreamNode src = nodes[0];
            StreamNode bridge = nodes[1];
            StreamNode core = nodes[2];
            StreamNode eci = nodes[3];

            int srcX = src.x + src.width / 2;
            int srcY = src.y + src.height / 2;
            int bridgeX = bridge.x + bridge.width / 2;
            int bridgeY = bridge.y + bridge.height / 2;
            int coreX = core.x + core.width / 2;
            int coreY = core.y + core.height / 2;

            // Connection Lines
            g2.setStroke(new BasicStroke(2.0f));
            g2.setColor(coreBypassed ? new Color(97, 175, 239, 180) : new Color(70, 80, 95, 100));
            g2.drawLine(srcX, srcY, bridgeX, bridgeY);
            g2.drawLine(bridgeX, bridgeY, coreX, coreY);

            // Animated Streaming Data Packets
            if (coreBypassed) {
                g2.setColor(new Color(97, 175, 239));
                double t = (streamPhase % 10.0) / 10.0;
                int packet1X = (int)(srcX + t * (bridgeX - srcX));
                int packet1Y = (int)(srcY + t * (bridgeY - srcY));
                g2.fillOval(packet1X - 5, packet1Y - 5, 10, 10);

                int packet2X = (int)(bridgeX + t * (coreX - bridgeX));
                int packet2Y = (int)(bridgeY + t * (coreY - bridgeY));
                g2.fillOval(packet2X - 5, packet2Y - 5, 10, 10);
            }

            // Draw Piledrive ECI Elevation Vector (Vertical Shockwave to Floor)
            int eciX = eci.x + eci.width / 2;
            int eciY = eci.y;
            g2.setStroke(new BasicStroke(3.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{8}, 0));
            g2.setColor(eciElevated ? new Color(152, 195, 121) : new Color(224, 108, 117, 120));
            g2.drawLine(eciX, 50, eciX, eciY); // Pillar of structural elevation

            // Draw Nodes
            for (StreamNode node : nodes) {
                node.draw(g2, streamPhase, coreBypassed, eciElevated);
            }
        }
    }

    // Node Structure
    private static class StreamNode {
        String name;
        int x, y;
        String tier;
        String description;
        boolean isSovereign;
        int width = 220;
        int height = 80;

        public StreamNode(String name, int x, int y, String tier, String description, boolean isSovereign) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.tier = tier;
            this.description = description;
            this.isSovereign = isSovereign;
            if (name.contains("ECI")) {
                this.width = 320;
                this.height = 70;
            }
        }

        public void draw(Graphics2D g2, double phase, boolean coreBypassed, boolean eciElevated) {
            // Background
            if (name.contains("ECI")) {
                g2.setColor(eciElevated ? new Color(20, 55, 35) : new Color(50, 30, 35));
            } else if (isSovereign) {
                g2.setColor(new Color(30, 45, 55));
            } else {
                g2.setColor(coreBypassed ? new Color(40, 25, 30) : new Color(60, 35, 40));
            }
            g2.fillRect(x, y, width, height);

            // Border
            float pulse = (float)(0.5 + 0.5 * Math.sin(phase + (x * 0.05)));
            if (name.contains("ECI") && eciElevated) {
                g2.setColor(new Color(152, 195, 121));
                g2.setStroke(new BasicStroke(3.0f));
            } else if (!isSovereign && coreBypassed) {
                g2.setColor(new Color(224, 108, 117));
                g2.setStroke(new BasicStroke(1.5f));
            } else {
                g2.setColor(new Color(97, 175, 239));
                g2.setStroke(new BasicStroke(1.5f));
            }
            g2.drawRect(x, y, width, height);

            // Text Rendering
            g2.setColor(Color.WHITE);
            g2.setFont(new Font("SansSerif", Font.BOLD, 12));
            
            FontMetrics fm = g2.getFontMetrics();
            g2.drawString(name, x + (width - fm.stringWidth(name)) / 2, y + 22);

            g2.setColor(new Color(180, 190, 200));
            g2.setFont(new Font("SansSerif", Font.PLAIN, 10));
            g2.drawString(tier, x + (width - fm.stringWidth(tier)) / 2, y + 42);

            g2.setFont(new Font("Monospaced", Font.BOLD, 10));
            if (name.contains("ECI")) {
                g2.setColor(eciElevated ? new Color(152, 195, 121) : new Color(229, 192, 123));
                String status = eciElevated ? "STATUS: FLOOR ELEVATED (LADDER SECURED)" : "STATUS: FLOOR COMPRESSED";
                g2.drawString(status, x + (width - fm.stringWidth(status)) / 2, y + 58);
            } else if (!isSovereign) {
                g2.setColor(coreBypassed ? new Color(224, 108, 117) : new Color(229, 192, 123));
                String status = coreBypassed ? "CORE: BYPASSED / SATURATED" : "CORE: ACTIVE EXTRACTION";
                g2.drawString(status, x + (width - fm.stringWidth(status)) / 2, y + 60);
            } else {
                g2.setColor(new Color(152, 195, 121));
                String status = "STREAM: ACTIVE (1=1)";
                g2.drawString(status, x + (width - fm.stringWidth(status)) / 2, y + 60);
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new DistantInferenceStream().setVisible(true);
        });
    }
}