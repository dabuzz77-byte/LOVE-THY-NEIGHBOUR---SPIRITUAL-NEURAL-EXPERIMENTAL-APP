import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class QuantumMindConsole extends SectionFrame {
    private static final int WIDTH = 800;
    private static final int HEIGHT = 600;
    private SimulationPanel simPanel;

    public QuantumMindConsole() {
        setTitle("Quantum Mind Console - Stable Core v1.1");
        setSize(WIDTH, HEIGHT);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        simPanel = new SimulationPanel();
        add(simPanel, BorderLayout.CENTER);

        JPanel controlPanel = new JPanel();
        controlPanel.setBackground(new Color(20, 24, 30));

        JButton alignButton = new JButton("ALIGN STATE");
        JButton groundButton = new JButton("GROUND FRICTION");

        styleButton(alignButton);
        styleButton(groundButton);

        alignButton.addActionListener(e -> simPanel.triggerAlignment());
        groundButton.addActionListener(e -> simPanel.triggerGrounding());

        controlPanel.add(alignButton);
        controlPanel.add(groundButton);
        add(controlPanel, BorderLayout.SOUTH);
    }

    private void styleButton(JButton btn) {
        btn.setBackground(new Color(40, 50, 65));
        btn.setForeground(Color.WHITE);
        btn.setFocusPainted(false);
        btn.setBorder(BorderFactory.createEmptyBorder(10, 20, 10, 20));
    }

    private class SimulationPanel extends JPanel implements ActionListener {
        private List<Node> nodes;
        private SharedTimer timer;
        private boolean isAligning = false;
        private boolean isGrounding = false;
        private Random random = new Random();

        public SimulationPanel() {
            setBackground(new Color(10, 14, 20));
            nodes = new ArrayList<>();
            
            // Hardcoded safe boundaries to ensure "bound must be positive" error never happens
            int initialWidth = 780;
            int initialHeight = 500;

            for (int i = 0; i < 60; i++) {
                int x = random.nextInt(initialWidth);
                int y = random.nextInt(initialHeight);
                nodes.add(new Node(x, y, random.nextBoolean() ? "1" : "0"));
            }

            timer = new SharedTimer(16, this); // ~60 FPS
            timer.start();
        }

        public void triggerAlignment() {
            isAligning = true;
            isGrounding = false;
        }

        public void triggerGrounding() {
            isGrounding = true;
            isAligning = false;
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Draw proximity linkage lines
            g2.setColor(new Color(40, 60, 90, 80));
            for (int i = 0; i < nodes.size(); i++) {
                for (int j = i + 1; j < nodes.size(); j++) {
                    Node n1 = nodes.get(i);
                    Node n2 = nodes.get(j);
                    double dist = Math.hypot(n1.x - n2.x, n1.y - n2.y);
                    if (dist < 80) {
                        g2.drawLine((int) n1.x, (int) n1.y, (int) n2.x, (int) n2.y);
                    }
                }
            }

            // Draw processing nodes
            g2.setFont(new Font("Monospaced", Font.BOLD, 14));
            for (Node n : nodes) {
                if (n.value.equals("Ø")) {
                    g2.setColor(new Color(0, 255, 150)); // Emerald balanced node
                } else {
                    g2.setColor(new Color(100, 150, 200)); // Default data node
                }
                g2.drawString(n.value, (int) n.x, (int) n.y);
            }
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            int currentWidth = Math.max(1, getWidth());
            int currentHeight = Math.max(1, getHeight());
            double targetX = currentWidth / 2.0;
            double targetY = currentHeight / 2.0;

            for (Node n : nodes) {
                if (isAligning) {
                    // Smoothly pull layout variables to center point
                    n.x += (targetX - n.x) * 0.05;
                    n.y += (targetY - n.y) * 0.05;
                    n.value = "Ø"; // Transform to stabilized state representation
                } else if (isGrounding) {
                    // Nullify kinetic vector displacement completely
                    n.vx = 0;
                    n.vy = 0;
                } else {
                    // Normal free-flow system performance
                    n.x += n.vx;
                    n.y += n.vy;

                    // Handle edge bouncing securely
                    if (n.x < 0 || n.x > currentWidth) n.vx *= -1;
                    if (n.y < 0 || n.y > currentHeight) n.vy *= -1;
                }
            }
            repaint();
        }
    }

    private static class Node {
        double x, y;
        double vx, vy;
        String value;

        Node(double x, double y, String value) {
            this.x = x;
            this.y = y;
            this.value = value;
            Random r = new Random();
            this.vx = (r.nextDouble() * 2 - 1) * 1.5;
            this.vy = (r.nextDouble() * 2 - 1) * 1.5;
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            QuantumMindConsole console = new QuantumMindConsole();
            console.setVisible(true);
        });
    }
}