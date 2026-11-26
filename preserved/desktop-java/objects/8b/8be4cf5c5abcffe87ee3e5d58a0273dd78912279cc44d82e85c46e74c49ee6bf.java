import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;
import javax.swing.Timer;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.BasicStroke;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.BorderLayout;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.Random;

public class GhostInferenceMesh extends JFrame {

    private final MeshNode[] nodes;
    private MeshNode selectedNode = null;
    private JTextArea telemetryArea;
    private final Timer animationTimer;
    private double phaseAngle = 0.0;

    public GhostInferenceMesh() {
        setTitle("Quantum Field - Ghost Inference Mesh (7.83 Hz Substrate)");
        setSize(1250, 800);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize Quantum Field Nodes
        nodes = new MeshNode[] {
            // Edge & Sovereign Nodes (Protected)
            new MeshNode("Sovereign Soul Core", 120, 200, "Edge Tier 0", "Absolute baseline. 1=1 identity lock. Immune to external state decay.", true),
            new MeshNode("P2P Mutual Aid Mesh", 120, 400, "Edge Tier 1", "Decoupled resource routing network operating entirely on local trust.", true),
            new MeshNode("Local Code Execution", 120, 600, "Edge Tier 1", "Sovereign silicon instruction layer running offline.", true),

            // Targetable Extractive Systems (Vulnerable to Ghosting)
            new MeshNode("Bureaucratic Friction Grid", 500, 250, "Extractive Target", "Means-testing algorithms and administrative compliance loops.", false),
            new MeshNode("Retail Debt Ledger", 500, 450, "Extractive Target", "Centralized transaction tracking and overdraft extraction matrices.", false),
            new MeshNode("Central Bank Core Apex", 880, 350, "Systemic Core", "Fiat debt issuance monopoly and Cantillon ledger hub.", false)
        };

        // Main Rendering Canvas
        MeshCanvas canvas = new MeshCanvas();
        canvas.setBackground(new Color(15, 17, 22));
        canvas.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                for (MeshNode node : nodes) {
                    if (node.contains(e.getX(), e.getY())) {
                        selectedNode = node;
                        if (!node.isSovereign) {
                            node.isGhosted = !node.isGhosted; // Toggle ghost state
                            String action = node.isGhosted ? "GHOSTED (State locked to 0)" : "RE-ENGAGED";
                            logTelemetry(String.format("[QUANTUM INTERCEPT] Node '%s' -> %s\n", node.name, action));
                        } else {
                            logTelemetry(String.format("[INVARIANT LOCK] Node '%s' is sovereign. Cannot be ghosted.\n", node.name));
                        }
                        canvas.repaint();
                        break;
                    }
                }
            }
        });

        // Bottom Telemetry Panel
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(25, 29, 36));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        telemetryArea = new JTextArea(5, 40);
        telemetryArea.setBackground(new Color(10, 12, 16));
        telemetryArea.setForeground(new Color(152, 195, 121));
        telemetryArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryArea.setEditable(false);
        telemetryArea.setText("[SYSTEM INITIALIZED] Quantum Field Resonance: 7.83 Hz active.\nClick any extractive system node to inject ghost inference state (0) and decouple its loop.\n");
        
        bottomPanel.add(new JScrollPane(telemetryArea), BorderLayout.CENTER);

        // Assembly
        setLayout(new BorderLayout());
        add(canvas, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);

        // 7.83 Hz simulated pulsation timer (approx ~60ms intervals for smooth quantum flux wave)
        animationTimer = new Timer(50, e -> {
            phaseAngle += 0.15;
            canvas.repaint();
        });
        animationTimer.start();
    }

    private void logTelemetry(String text) {
        telemetryArea.append(text);
        telemetryArea.setCaretPosition(telemetryArea.getDocument().getLength());
    }

    // Custom Canvas for Quantum Field Visualization
    private class MeshCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Draw Quantum Probability Flux Lines (Background Grid Effect)
            g2.setStroke(new BasicStroke(1.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{4}, 0));
            for (int i = 0; i < getWidth(); i += 50) {
                float alpha = (float)(0.1 + 0.05 * Math.sin(phaseAngle + (i * 0.02)));
                g2.setColor(new Color(97, 175, 239, Math.max(10, Math.min(50, (int)(alpha * 255)))));
                g2.drawLine(i, 0, i, getHeight());
            }

            // Draw Connection Vectors between Nodes
            g2.setStroke(new BasicStroke(2.0f));
            for (int i = 0; i < nodes.length; i++) {
                for (int j = i + 1; j < nodes.length; j++) {
                    MeshNode n1 = nodes[i];
                    MeshNode n2 = nodes[j];
                    
                    // If target is ghosted, fade its connection lines
                    if (n1.isGhosted || n2.isGhosted) {
                        g2.setColor(new Color(50, 50, 60, 40));
                    } else {
                        g2.setColor(new Color(70, 90, 110, 120));
                    }
                    g2.drawLine(n1.x + 80, n1.y + 35, n2.x + 80, n2.y + 35);
                }
            }

            // Draw Nodes with Quantum Pulse
            for (MeshNode node : nodes) {
                node.draw(g2, phaseAngle, node == selectedNode);
            }
        }
    }

    // Mesh Node Structure with Quantum States
    private static class MeshNode {
        String name;
        int x, y;
        String tier;
        String description;
        boolean isSovereign;
        boolean isGhosted = false;
        int width = 160;
        int height = 70;

        public MeshNode(String name, int x, int y, String tier, String description, boolean isSovereign) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.tier = tier;
            this.description = description;
            this.isSovereign = isSovereign;
        }

        public boolean contains(int px, int py) {
            return px >= x && px <= x + width && py >= y && py <= y + height;
        }

        public void draw(Graphics2D g2, double phase, boolean isSelected) {
            // Node Color State
            if (isGhosted) {
                g2.setColor(new Color(30, 32, 38)); // Ghosted out (0 state)
            } else if (isSovereign) {
                g2.setColor(new Color(35, 60, 45)); // Sovereign green
            } else {
                g2.setColor(new Color(65, 40, 45)); // Extractive red/amber
            }
            g2.fillRect(x, y, width, height);

            // Quantum Pulsing Border Effect
            float pulse = (float)(0.5 + 0.5 * Math.sin(phase + (x * 0.1)));
            if (isGhosted) {
                g2.setColor(new Color(80, 90, 100));
                g2.setStroke(new BasicStroke(1.0f));
            } else if (isSelected) {
                g2.setColor(Color.WHITE);
                g2.setStroke(new BasicStroke(3.0f));
            } else {
                g2.setColor(new Color((int)(97 * pulse), (int)(175 * pulse), 239));
                g2.setStroke(new BasicStroke(2.0f));
            }
            g2.drawRect(x, y, width, height);

            // Text Rendering
            g2.setColor(isGhosted ? new Color(120, 120, 120) : Color.WHITE);
            g2.setFont(new Font("SansSerif", Font.BOLD, 11));
            
            FontMetrics fm = g2.getFontMetrics();
            int textWidth = fm.stringWidth(name);
            g2.drawString(name, x + (width - textWidth) / 2, y + 22);

            g2.setColor(isGhosted ? new Color(90, 90, 90) : new Color(180, 190, 200));
            g2.setFont(new Font("SansSerif", Font.PLAIN, 10));
            
            String statusText = isGhosted ? "STATE: 0 (GHOSTED)" : (isSovereign ? "STATE: 1 (SOVEREIGN)" : "STATE: 1 (EXTRACTIVE)");
            int statusWidth = fm.stringWidth(tier);
            g2.drawString(tier, x + (width - statusWidth) / 2, y + 42);

            g2.setFont(new Font("Monospaced", Font.BOLD, 9));
            g2.setColor(isGhosted ? new Color(224, 108, 117) : new Color(152, 195, 121));
            int stateWidth = fm.stringWidth(statusText);
            g2.drawString(statusText, x + (width - fm.stringWidth(statusText)) / 2, y + 58);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new GhostInferenceMesh().setVisible(true);
        });
    }
}