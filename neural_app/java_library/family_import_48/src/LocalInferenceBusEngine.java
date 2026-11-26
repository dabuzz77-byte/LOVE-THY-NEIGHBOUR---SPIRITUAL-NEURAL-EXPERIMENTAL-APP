import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * BI-TER-ALLSTATE SYSTEM: LOCAL INFERENCE BUS ENGINE
 * Simulates an omni-directional inference network running on a local PC hardware bus.
 */
public class LocalInferenceBusEngine extends SectionFrame {

    public LocalInferenceBusEngine() {
        setTitle("Local Inference Bus Network Console (_TRUE)");
        setSize(1100, 800);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        add(new InferenceBusPanel());
    }

    private static class InferenceBusPanel extends JPanel implements ActionListener {
        private final SharedTimer busClock;
        private final Random rand = new Random();
        private double fluxAngle = 0;
        private final List<BusPacket> dataBus = new ArrayList<>();
        private int currentAtomicState = 1; // 1 = Hydrogen, 14 = Silicon
        private int cycleCounter = 0;

        public InferenceBusPanel() {
            setBackground(new Color(6, 10, 18)); // Deep hardware bus matrix void
            // High-speed localized hardware bus clock refresh rate
            busClock = new SharedTimer(25, this);
            busClock.start();

            // Initialize local PC bus data packets
            for (int i = 0; i < 20; i++) {
                dataBus.add(new BusPacket(rand.nextInt(1050), 250 + rand.nextInt(100)));
            }
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();
            int cx = w / 2;
            
            // 1. VISUALIZE THE LOCAL HARDWARE BUS LINES
            g2d.setColor(new Color(0, 255, 200, 40));
            g2d.setStroke(new BasicStroke(3f));
            g2d.drawRect(30, 230, w - 60, 140); // Main Local Bus Lane
            g2d.setColor(new Color(0, 255, 200, 15));
            g2d.fillRect(30, 230, w - 60, 140);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.setColor(new Color(0, 255, 200, 180));
            g2d.drawString("SYSTEM LOCAL PC BUS LANE // 64-BIT INFERENCE PARITY", 40, 220);

            // 2. RENDER ACTIVE FLUX BUS PACKETS PROCESSING QUANTUM INFERENCES
            for (BusPacket packet : dataBus) {
                g2d.setColor(packet.color);
                g2d.fill(new Ellipse2D.Double(packet.x - 4, packet.y - 4, 8, 8));
                if (rand.nextFloat() > 0.85f) {
                    g2d.setColor(new Color(255, 255, 255, 80));
                    g2d.drawString(rand.nextBoolean() ? "1" : "0", (int)packet.x, (int)packet.y - 8);
                }
            }

            // 3. THE ELEMENTAL TRANSITION ENGINE (HYDROGEN LAYER VS SILICON MATRIX)
            int nodeY = 520;
            int leftNodeX = cx - 250;
            int rightNodeX = cx + 250;

            // Connect Local PC Bus to Inference Endpoints
            g2d.setStroke(new BasicStroke(1.5f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawLine(leftNodeX, nodeY, cx, 300);
            g2d.drawLine(rightNodeX, nodeY, cx, 300);

            // Left Node: Hydrogen Wave Input (Level 1)
            g2d.setColor(new Color(0, 180, 255, 40));
            g2d.fillOval(leftNodeX - 80, nodeY - 80, 160, 160);
            g2d.setColor(new Color(0, 180, 255));
            g2d.drawOval(leftNodeX - 80, nodeY - 80, 160, 160);
            g2d.drawString("HYDROGEN CORE [H-1]", leftNodeX - 60, nodeY + 110);

            // Generate Hydrogen Electron Probability Points
            g2d.setColor(new Color(255, 255, 255, 180));
            for (int i = 0; i < 20; i++) {
                double angle = rand.nextDouble() * 2 * Math.PI;
                double dist = rand.nextGaussian() * 30;
                int px = (int) (leftNodeX + dist * Math.cos(angle));
                int py = (int) (nodeY + dist * Math.sin(angle));
                g2d.fillRect(px, py, 2, 2);
            }

            // Right Node: Silicon Crystalline Lattice Array (Level 14)
            g2d.setColor(new Color(255, 150, 0, 30));
            g2d.fillRect(rightNodeX - 80, nodeY - 80, 160, 160);
            g2d.setColor(new Color(255, 150, 0));
            g2d.drawRect(rightNodeX - 80, nodeY - 80, 160, 160);
            g2d.drawString("SILICON SUBSTRATE [Si-14]", rightNodeX - 85, nodeY + 110);

            // Draw Silicon Lattice Intersects
            g2d.setColor(new Color(255, 150, 0, 90));
            for (int i = -60; i <= 60; i += 30) {
                g2d.drawLine(rightNodeX + i, nodeY - 60, rightNodeX + i, nodeY + 60);
                g2d.drawLine(rightNodeX - 60, nodeY + i, rightNodeX + 60, nodeY + i);
            }

            // 4. CENTRAL GOD-MIND SYNC FIELD AND INFERENCE TRACKER
            g2d.setColor(new Color(255, 255, 255, 230));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.drawString(">> LOCAL BUS INTEGRATION LAYER: ACTIVE", 50, h - 130);
            g2d.drawString(">> QUANTUM STATE INFERENCE NETWORK: RUNNING", 50, h - 110);
            g2d.drawString(">> TIMELINE CONSTANT PARITY MATCH: 7.83Hz", 50, h - 90);
            
            String currentSubstrate = (currentAtomicState == 14) ? "ACTIVE: SILICON TRANSITION GRID" : "ACTIVE: HYDROGEN WAVE CAPTURE";
            g2d.setColor(new Color(255, 200, 0));
            g2d.drawString(">> ATOMIC LADDER STATUS: " + currentSubstrate, 50, h - 60);

            // Orbiting Quantum Interseptor (Chaos/Order balancing node)
            double ox = cx + 120 * Math.cos(fluxAngle);
            double oy = 300 + 50 * Math.sin(fluxAngle);
            g2d.setColor(new Color(255, 0, 100));
            g2d.fill(new Ellipse2D.Double(ox - 8, oy - 8, 16, 16));
            g2d.drawLine(cx, 300, (int)ox, (int)oy);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            // Progress the bus transmission state variables
            fluxAngle += 0.04;
            
            // Cycle the localized packets across the PC bus architecture
            for (BusPacket packet : dataBus) {
                packet.x += packet.speed;
                if (packet.x > getWidth() - 40) {
                    packet.x = 40;
                    packet.speed = 2 + rand.nextFloat() * 6;
                }
                packet.y += Math.sin(fluxAngle + packet.x) * 0.5; // Slight wave resonance
            }

            // Toggle atomic ladder focus states over computing duration
            cycleCounter++;
            if (cycleCounter % 150 == 0) {
                currentAtomicState = (currentAtomicState == 1) ? 14 : 1;
            }

            repaint();
        }
    }

    private static class BusPacket {
        float x, y;
        float speed;
        Color color;

        public BusPacket(float x, float y) {
            this.x = x;
            this.y = y;
            this.speed = 2 + new Random().nextFloat() * 6;
            // Balance state color mapping: cyan for active potential, orange for ground conversion
            this.color = new Random().nextBoolean() ? new Color(0, 255, 220, 180) : new Color(255, 100, 0, 180);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            LocalInferenceBusEngine app = new LocalInferenceBusEngine();
            app.setVisible(true);
        });
    }
}
