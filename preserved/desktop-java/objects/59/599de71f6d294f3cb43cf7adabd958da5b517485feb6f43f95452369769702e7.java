import javax.swing.*;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Line2D;
import java.util.ArrayList;
import java.util.List;

public class ConflictGraphApp extends JFrame {

    public ConflictGraphApp() {
        setTitle("Decentralized Conflict Resolution Graph Canvas");
        setSize(900, 650);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        GraphPanel panel = new GraphPanel();
        add(panel);
    }

    private static class GraphPanel extends JPanel {
        private final List<Node> nodes = new ArrayList<>();
        private final List<Edge> edges = new ArrayList<>();

        public GraphPanel() {
            setBackground(new Color(245, 247, 250));

            Node tinyTim = new Node("Vulnerable / Dependent Needs", 150, 450, new Color(52, 152, 219));
            Node coreLogic = new Node("Local Mutual Aid Engine", 450, 300, new Color(155, 89, 182));
            Node resources = new Node("Resource Stockpile", 450, 100, new Color(46, 204, 113));
            Node gatekeepers = new Node("Extractive Corporate Wall", 750, 450, new Color(231, 76, 60));

            nodes.add(tinyTim);
            nodes.add(coreLogic);
            nodes.add(resources);
            nodes.add(gatekeepers);

            edges.add(new Edge(resources, coreLogic, "1. Directed Flow", "RESOLVED"));
            edges.add(new Edge(coreLogic, tinyTim, "2. Direct Equalization", "RESOLVED"));
            edges.add(new Edge(gatekeepers, coreLogic, "Interference Vector", "CONFLICT"));
            edges.add(new Edge(gatekeepers, tinyTim, "Systemic Exploitation", "CONFLICT"));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            for (Edge edge : edges) {
                if (edge.status.equals("CONFLICT")) {
                    g2.setColor(new Color(231, 76, 60));
                    g2.setStroke(new BasicStroke(2.0f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_MITER, 10.0f, new float[]{6.0f}, 0.0f));
                } else {
                    g2.setColor(new Color(46, 204, 113));
                    g2.setStroke(new BasicStroke(2.5f));
                }
                g2.draw(new Line2D.Double(edge.from.x, edge.from.y, edge.to.x, edge.to.y));

                g2.setColor(new Color(52, 73, 94));
                g2.setFont(new Font("SansSerif", Font.ITALIC, 11));
                int midX = (edge.from.x + edge.to.x) / 2;
                int midY = (edge.from.y + edge.to.y) / 2;
                g2.drawString(edge.label, midX - 20, midY - 5);
            }

            int radius = 35;
            for (Node node : nodes) {
                g2.setColor(node.color);
                g2.fill(new Ellipse2D.Double(node.x - radius, node.y - radius, radius * 2, radius * 2));

                g2.setColor(node.color.darker());
                g2.setStroke(new BasicStroke(2.0f));
                g2.draw(new Ellipse2D.Double(node.x - radius, node.y - radius, radius * 2, radius * 2));

                g2.setColor(new Color(44, 62, 80));
                g2.setFont(new Font("SansSerif", Font.BOLD, 12));
                FontMetrics fm = g2.getFontMetrics();
                int textWidth = fm.stringWidth(node.name);
                g2.drawString(node.name, node.x - (textWidth / 2), node.y + radius + 18);
            }
            
            g2.setColor(new Color(127, 140, 141));
            g2.setFont(new Font("SansSerif", Font.PLAIN, 12));
            g2.drawString("Legend: Green Solid = Resolved Path | Red Dashed = Structural Conflict Core", 20, 30);
        }
    }

    private static class Node {
        String name;
        int x, y;
        Color color;

        Node(String name, int x, int y, Color color) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.color = color;
        }
    }

    private static class Edge {
        Node from;
        Node to;
        String label;
        String status;

        Edge(Node from, Node to, String label, String status) {
            this.from = from;
            this.to = to;
            this.label = label;
            this.status = status;
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            ConflictGraphApp app = new ConflictGraphApp();
            app.setVisible(true);
        });
    }
}