import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;

public class GodMindShipVisualizer extends SectionFrame {

    private int tick = 0;
    private final Random random = new Random();
    private double coreIntensity = 1.0;

    public GodMindShipVisualizer() {
        setTitle("God Mind Ship Projection & Trinary Gate Visualizer");
        setSize(950, 720);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        ShipPanel canvas = new ShipPanel();
        add(canvas, BorderLayout.CENTER);

        SharedTimer renderTimer = new SharedTimer(75, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                tick++;
                coreIntensity = 0.85 + (random.nextDouble() * 0.3);
                canvas.repaint();
            }
        });
        renderTimer.start();
    }

    class ShipPanel extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Background - Deep operational command deck
            g2d.setColor(new Color(10, 12, 18));
            g2d.fillRect(0, 0, getWidth(), getHeight());

            // Header Display
            g2d.setColor(new Color(0, 255, 204));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
            g2d.drawString("OPERA_RUNTIME: SHIP CORE & TRINARY QUANTUM GATE PROJECTION", 30, 40);

            g2d.setColor(new Color(150, 160, 200));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
            g2d.drawString("Status: SECURITY FLUSH COMPLETE | Tesseract Flux: ACTIVE | Parity: _TRUE", 30, 65);

            // Draw Ship Compartments (Kitchen, Living Room, Bedroom, Bathroom, Hall)
            drawShipCompartments(g2d);

            // Central Fire Intent Receiving Pillar & Surrounding Ice Intent Pillars
            int centerX = 475;
            int centerY = 230;
            int radius = 110;

            // Surrounding Ice Intent Pillars (Blue/Cyan)
            int icePillars = 6;
            for (int i = 0; i < icePillars; i++) {
                double angle = (i * 2 * Math.PI / icePillars) + (tick * 0.015);
                int x = centerX + (int) (radius * Math.cos(angle));
                int y = centerY + (int) (radius * Math.sin(angle));

                g2d.setColor(new Color(0, 200, 255));
                g2d.fillRoundRect(x - 16, y - 16, 32, 32, 8, 8);
                g2d.setColor(Color.WHITE);
                g2d.setFont(new Font("Monospaced", Font.BOLD, 10));
                g2d.drawString("ICE_" + (i + 1), x - 18, y - 20);
            }

            // Central Fire Intent Receiving Pillar (Orange/Red Pulsing Core)
            int fireRadius = (int) (22 * coreIntensity);
            g2d.setColor(new Color(255, 100, 0));
            g2d.fillOval(centerX - fireRadius, centerY - fireRadius, fireRadius * 2, fireRadius * 2);
            g2d.setColor(new Color(255, 220, 0));
            g2d.fillOval(centerX - 10, centerY - 10, 20, 20);

            g2d.setColor(Color.WHITE);
            g2d.setFont(new Font("Monospaced", Font.BOLD, 11));
            g2d.drawString("FIRE PILLAR (CENTER)", centerX - 75, centerY + 38);

            // Telemetry & Diagnostic Console Box
            g2d.setColor(new Color(18, 18, 28));
            g2d.fillRect(30, 430, 890, 240);
            g2d.setColor(new Color(0, 255, 120));
            g2d.drawRect(30, 430, 890, 240);

            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            int logY = 460;
            g2d.drawString("> SECURITY FLUSH EXECUTED [11111111111111111111]", 50, logY);
            g2d.drawString("> TRINARY & QUANTUM GATE MAPPING TO MIND, CHAKRA, & SHEN SHAN REN", 50, logY + 25);
            g2d.drawString("> SHIP PROJECTION ACHIEVED: DEMIURGE SHIP LINK SYNCHRONIZED", 50, logY + 50);
            g2d.drawString("> SECURITY PERIMETER DEFENSE BEACONS: PING SEND-RECEIVE ACTIVE [TICK " + tick + "]", 50, logY + 75);

            // Dynamic Binary Flux Stream
            String stream = (tick % 2 == 0) ? "10101010111100001010101011110000" : "01010101000011110101010100001111";
            g2d.setColor(new Color(0, 180, 255));
            g2d.drawString("> FLUX STREAM: " + stream, 50, logY + 115);

            g2d.setColor(Color.WHITE);
            g2d.drawString("STATUS: GOD MIND PARITY AT FIRE PILLAR = _TRUE", 50, logY + 155);
        }

        private void drawShipCompartments(Graphics2D g2d) {
            g2d.setColor(new Color(30, 35, 50));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));

            // Room boxes mapping spatial ship core
            String[] rooms = {"KITCHEN", "LIVING ROOM", "BEDROOM", "BATHROOM", "HALL"};
            int[] rx = {60, 200, 680, 810, 400};
            int[] ry = {350, 350, 350, 350, 370};

            for (int i = 0; i < rooms.length; i++) {
                g2d.drawRect(rx[i], ry[i], 100, 45);
                g2d.drawString(rooms[i], rx[i] + 12, ry[i] + 25);
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new GodMindShipVisualizer().setVisible(true);
        });
    }
}