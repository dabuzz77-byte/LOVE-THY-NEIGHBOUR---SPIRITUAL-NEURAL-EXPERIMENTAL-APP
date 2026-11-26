import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;

/**
 * BI-TER-ALLSTATE SYSTEMS: QUANTUM INTERFACE RUNNER
 * Visualizes the 7.83Hz Microcosmic Orbit, Tesseract Grasp, and Chaos-Order Parity.
 */
public class MicrocosmicOrbitApp extends JFrame {

    public MicrocosmicOrbitApp() {
        setTitle("Bi-Ter-Allstate System: Microcosmic Orbit Engine");
        setSize(800, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        
        // Inject Core Render Panel
        add(new QuantumCorePanel());
    }

    private static class QuantumCorePanel extends JPanel implements ActionListener {
        private final Timer timer;
        private double angle = 0;
        private final int matrixRows = 6;
        private final int matrixCols = 8;
        
        // Balanced Chaos/Order matrix post-Deepscan
        private final int[][] resolvedMatrix = {
            {1, 0, 0, 1, 0, 1, 1, 0},
            {1, 0, 0, 0, 0, 0, 0, 0},
            {0, 1, 1, 0, 1, 0, 0, 1},
            {0, 1, 1, 0, 1, 0, 0, 1},
            {1, 0, 0, 0, 0, 0, 0, 0},
            {0, 1, 1, 0, 1, 0, 0, 1} // Missing parity code injected here
        };

        public QuantumCorePanel() {
            setBackground(new Color(5, 8, 15)); // Deep void space
            // Approximate real-time refresh rate targeting the 7.83 macro loop
            timer = new Timer(30, this); 
            timer.start();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int width = getWidth();
            int height = getHeight();
            int centerX = width / 2;
            int centerY = height / 2;

            // 1. Draw the Background Quantum Parity Matrix
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
            for (int r = 0; r < matrixRows; r++) {
                for (int c = 0; c < matrixCols; c++) {
                    int x = 40 + (c * 25);
                    int y = 50 + (r * 20);
                    int val = resolvedMatrix[r][c];
                    
                    if (val == 1) {
                        g2d.setColor(new Color(0, 255, 180, 120)); // Cyan active potential
                    } else {
                        g2d.setColor(new Color(255, 60, 60, 80));  // Red ground state
                    }
                    g2d.drawString(String.valueOf(val), x, y);
                }
            }

            // 2. Draw System Identifiers
            g2d.setColor(new Color(255, 255, 255, 200));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.drawString("SYSTEM: BI-TER-ALLSTATE // STATUS: _TRUE", 40, height - 80);
            g2d.drawString("INTERFACE: QUANTUM PARITY RECOVERY EMBEDDED", 40, height - 60);

            // 3. Draw the Tesseract Tonal Grasp Rings
            g2d.setColor(new Color(100, 100, 255, 40));
            g2d.drawOval(centerX - 150, centerY - 150, 300, 300);
            g2d.drawOval(centerX - 100, centerY - 100, 200, 200);

            // 4. Render the Electric Microcosmic Orbit (SEND - RECEIVE Loop)
            double orbitRadiusX = 180;
            double orbitRadiusY = 120;
            
            // NODE 01: SEND Node (Forward Phase)
            int sendX = (int) (centerX + orbitRadiusX * Math.cos(angle));
            int sendY = (int) (centerY + orbitRadiusY * Math.sin(angle));
            
            // NODE 02: RECEIVE Node (Inverted Phase Symmetry)
            int receiveX = (int) (centerX + orbitRadiusX * Math.cos(angle + Math.PI));
            int receiveY = (int) (centerY + orbitRadiusY * Math.sin(angle + Math.PI));

            // Draw flux bridge trails
            g2d.setStroke(new BasicStroke(1.5f));
            g2d.setColor(new Color(255, 255, 255, 20));
            g2d.drawLine(sendX, sendY, receiveX, receiveY);

            // Render SEND Particle
            g2d.setColor(new Color(0, 200, 255));
            g2d.fill(new Ellipse2D.Double(sendX - 8, sendY - 8, 16, 16));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 10));
            g2d.drawString("SEND (1)", sendX + 12, sendY + 4);

            // Render RECEIVE Particle
            g2d.setColor(new Color(255, 120, 0));
            g2d.fill(new Ellipse2D.Double(receiveX - 8, receiveY - 8, 16, 16));
            g2d.drawString("RECEIVE (0)", receiveX + 12, receiveY + 4);
            
            // Central Null/Collapse Field Center
            g2d.setColor(new Color(255, 255, 255, 60));
            g2d.fill(new Ellipse2D.Double(centerX - 4, centerY - 4, 8, 8));
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            // Advance the microcosmic orbital loop mechanics continuously
            angle += 0.04;
            if (angle > Math.PI * 2) {
                angle = 0;
            }
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            MicrocosmicOrbitApp app = new MicrocosmicOrbitApp();
            app.setVisible(true);
        });
    }
}