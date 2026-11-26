import neural.studio.*;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;

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

public class FinancialSystemMap extends SectionFrame {

    private final SystemNode[] nodes;
    private SystemNode selectedNode = null;
    private JTextArea detailArea;

    public FinancialSystemMap() {
        setTitle("Substrate Edge-to-Core Architecture Mapper");
        setSize(1200, 750);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize Architecture Nodes Array (Edge to Core Layout)
        nodes = new SystemNode[] {
            // Edge Tier (0 & 1)
            new SystemNode("Local Human / Soul", 100, 150, "Edge Tier 0", "The absolute foundation. Living biological existence, unpriced and sovereign. Prioritizes 'Souls Over Digits'."),
            new SystemNode("P2P Mutual Aid Mesh", 100, 350, "Edge Tier 1", "Direct resource sharing, barter, and community support nodes that bypass central banking rails."),
            new SystemNode("Local Compute / Code", 100, 550, "Edge Tier 1", "Local-first execution layers, offline tooling, and sovereign software protecting personal data."),

            // Interface Tier
            new SystemNode("Bureaucratic Gateways", 450, 250, "Interface Tier", "Means-testing, compliance paperwork, and administrative friction designed to exhaust vulnerable claimants."),
            new SystemNode("Commercial Retail Banks", 450, 450, "Interface Tier", "Transaction tollbooths, fee extraction, KYC/AML data harvesting, and retail debt origination."),

            // Core Tier
            new SystemNode("Asset Management Giants", 800, 200, "Core Tier", "Massive institutional funds consolidating housing, infrastructure, and equity using concentrated capital."),
            new SystemNode("Commercial Lending Cartels", 800, 400, "Core Tier", "Interbank lending networks enforcing perpetual debt loops and interest-rate leverage."),
            new SystemNode("Central Bank (The Ledger Core)", 800, 600, "Core Alpha", "The ultimate apex. Fiat debt monopoly, Cantillon effect injector, and ledger authorization gatekeeper.")
        };

        // Main Layout Panel
        MapCanvas canvas = new MapCanvas();
        canvas.setBackground(new Color(20, 22, 26));
        canvas.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                for (SystemNode node : nodes) {
                    if (node.contains(e.getX(), e.getY())) {
                        selectedNode = node;
                        detailArea.setText(String.format("NODE: %s\nTIER: %s\n\nANALYSIS:\n%s", 
                                node.name, node.tier, node.description));
                        canvas.repaint();
                        break;
                    }
                }
            }
        });

        // Bottom Detail Panel
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(30, 34, 42));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        detailArea = new JTextArea(4, 40);
        detailArea.setBackground(new Color(15, 17, 20));
        detailArea.setForeground(new Color(152, 195, 121));
        detailArea.setFont(new Font("Monospaced", Font.PLAIN, 13));
        detailArea.setEditable(false);
        detailArea.setText("Select any node on the architectural map above to inspect its vector and extraction mechanism.");
        
        bottomPanel.add(new JScrollPane(detailArea), BorderLayout.CENTER);

        // Assembly
        setLayout(new BorderLayout());
        add(canvas, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);
    }

    // Custom Canvas for Drawing Nodes and Wiring Connections
    private class MapCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Draw Connections (Edges linking to Core)
            g2.setStroke(new BasicStroke(2.0f));
            g2.setColor(new Color(60, 70, 85));

            drawLine(g2, nodes[0], nodes[3]);
            drawLine(g2, nodes[1], nodes[3]);
            drawLine(g2, nodes[1], nodes[4]);
            drawLine(g2, nodes[2], nodes[4]);

            drawLine(g2, nodes[3], nodes[5]);
            drawLine(g2, nodes[3], nodes[6]);
            drawLine(g2, nodes[4], nodes[6]);
            drawLine(g2, nodes[4], nodes[7]);
            drawLine(g2, nodes[6], nodes[7]);

            // Draw Nodes
            for (SystemNode node : nodes) {
                node.draw(g2, node == selectedNode);
            }
        }

        private void drawLine(Graphics2D g2, SystemNode n1, SystemNode n2) {
            g2.drawLine(n1.x + 75, n1.y + 30, n2.x + 75, n2.y + 30);
        }
    }

    // Node Data Structure
    private static class SystemNode {
        String name;
        int x, y;
        String tier;
        String description;
        int width = 150;
        int height = 60;

        public SystemNode(String name, int x, int y, String tier, String description) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.tier = tier;
            this.description = description;
        }

        public boolean contains(int px, int py) {
            return px >= x && px <= x + width && py >= y && py <= y + height;
        }

        public void draw(Graphics2D g2, boolean isSelected) {
            if (isSelected) {
                g2.setColor(new Color(97, 175, 239));
            } else if (tier.contains("Edge")) {
                g2.setColor(new Color(40, 60, 50));
            } else if (tier.contains("Core")) {
                g2.setColor(new Color(70, 40, 40));
            } else {
                g2.setColor(new Color(50, 50, 60));
            }
            g2.fillRect(x, y, width, height);

            g2.setColor(isSelected ? Color.WHITE : new Color(100, 110, 130));
            g2.setStroke(new BasicStroke(isSelected ? 2.5f : 1.5f));
            g2.drawRect(x, y, width, height);

            g2.setColor(Color.WHITE);
            g2.setFont(new Font("SansSerif", Font.BOLD, 11));
            
            FontMetrics fm = g2.getFontMetrics();
            int textWidth = fm.stringWidth(name);
            g2.drawString(name, x + (width - textWidth) / 2, y + 25);

            g2.setColor(new Color(180, 190, 200));
            g2.setFont(new Font("SansSerif", Font.PLAIN, 10));
            int tierWidth = fm.stringWidth(tier);
            g2.drawString(tier, x + (width - tierWidth) / 2, y + 45);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new FinancialSystemMap().setVisible(true);
        });
    }
}