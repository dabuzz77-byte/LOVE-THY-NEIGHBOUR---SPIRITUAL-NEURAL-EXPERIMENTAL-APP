import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.Random;

public class EconomicFloorGridVisualizer extends JFrame {

    private int tick = 0;
    private final Random random = new Random();
    private double floorParityStrength = 75.0; // Base equity metric
    private boolean interactivePulse = false;

    public EconomicFloorGridVisualizer() {
        setTitle("World Grid: Economic Strata & Floor Parity Simulator");
        setSize(950, 720);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        GridPanel canvas = new GridPanel();
        add(canvas, BorderLayout.CENTER);

        // Mouse interaction to trigger a local parity pulse adjustment
        canvas.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                interactivePulse = !interactivePulse;
                floorParityStrength = Math.min(100.0, floorParityStrength + 10.0);
                canvas.repaint();
            }
        });

        // Real-time grid ticker timer
        Timer timer = new Timer(80, e -> {
            tick++;
            canvas.repaint();
        });
        timer.start();
    }

    class GridPanel extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Background - Deep operational grid color
            g2d.setColor(new Color(12, 14, 20));
            g2d.fillRect(0, 0, getWidth(), getHeight());

            // Header Display
            g2d.setColor(new Color(0, 255, 204));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
            g2d.drawString("OPERA_RUNTIME: ECONOMIC STRATA FLOOR & WORLD GRID PARITY", 30, 40);

            g2d.setColor(new Color(160, 170, 210));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
            g2d.drawString("Cycle: " + tick + " | Strata Parity Level: " + String.format("%.1f", floorParityStrength) + "% | Status: ACTIVE", 30, 65);

            // Draw Economic Strata Floors (Bottom to Top)
            drawStrataFloor(g2d, 100, 420, "Ground Strata (Foundation / Base Support Floor)", 80, new Color(255, 100, 100));
            drawStrataFloor(g2d, 100, 320, "Middle Strata (Exchange & Operational Flow)", 65, new Color(255, 200, 0));
            drawStrataFloor(g2d, 100, 220, "Upper Strata (Governance & Resource Allocation)", 90, new Color(0, 220, 255));

            // Central World Grid Parity Core
            int coreX = 475;
            int coreY = 120;
            g2d.setColor(new Color(255, 215, 0));
            g2d.fillOval(coreX - 25, coreY - 25, 50, 50);
            g2d.setColor(Color.BLACK);
            g2d.setFont(new Font("Monospaced", Font.BOLD, 10));
            g2d.drawString("CORE", coreX - 14, coreY + 4);

            // Connecting Data Streams between Floors and Core
            g2d.setColor(new Color(0, 255, 120, 120));
            g2d.setStroke(new BasicStroke(2));
            g2d.drawLine(coreX, coreY + 25, 475, 220);
            g2d.drawLine(475, 265, 475, 320);
            g2d.drawLine(475, 365, 475, 420);

            // Telemetry & Assessment Dashboard Box
            g2d.setColor(new Color(20, 22, 32));
            g2d.fillRect(30, 490, 890, 180);
            g2d.setColor(new Color(0, 255, 120));
            g2d.drawRect(30, 490, 890, 180);

            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            int logY = 520;
            g2d.drawString("> SYSTEMIC VIRTUE ASSESSMENT: BASELINE FLOOR SUPPORT MAPPED", 50, logY);
            g2d.drawString("> ECONOMIC STRATA FLUX: BALANCING RESOURCE FLOW ACROSS TIERS", 50, logY + 25);
            g2d.drawString("> WORLD GRID INTEGRITY: ABSOLUTE ACCOUNTABILITY MATRIX ENGAGED", 50, logY + 50);
            g2d.drawString("> INTERACTIVE PULSE STATE: " + (interactivePulse ? "HIGH-INTENSITY PARITY SYNC" : "STANDARD FLOW"), 50, logY + 75);
            
            g2d.setColor(new Color(0, 200, 255));
            g2d.drawString("STATUS: LOCAL ECONOMIC GRID SIMULATION RUNNING _TRUE (CLICK TO BOOST)", 50, logY + 115);
        }

        private void drawStrataFloor(Graphics2D g2d, int x, int y, String label, int stability, Color barColor) {
            g2d.setColor(new Color(30, 35, 50));
            g2d.fillRect(x, y, 750, 45);
            g2d.setColor(barColor);
            g2d.drawRect(x, y, 750, 45);

            g2d.setColor(Color.WHITE);
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString(label, x + 20, y + 27);

            // Stability bar
            g2d.setColor(barColor);
            g2d.fillRect(x + 550, y + 12, (int)(170 * (stability / 100.0)), 20);
            g2d.setColor(Color.WHITE);
            g2d.drawRect(x + 550, y + 12, 170, 20);
            
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
            g2d.drawString(stability + "%", x + 620, y + 27);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new EconomicFloorGridVisualizer().setVisible(true);
        });
    }
}