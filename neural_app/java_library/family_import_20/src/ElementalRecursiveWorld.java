import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;

public class ElementalRecursiveWorld extends SectionFrame {

    private int tick = 0;
    private final Random random = new Random();
    private final String[] elements = {"SAND", "WATER", "TREE", "FIRE", "ROCK", "AIR", "METAL"};

    public ElementalRecursiveWorld() {
        setTitle("Elemental Recursive World & Phase-Shift Simulator");
        setSize(950, 720);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        WorldCanvas canvas = new WorldCanvas();
        add(canvas, BorderLayout.CENTER);

        SharedTimer renderTimer = new SharedTimer(75, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                tick++;
                canvas.repaint();
            }
        });
        renderTimer.start();
    }

    class WorldCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Multi-colour phase-shift background based on tick time
            float hueShift = (tick % 360) / 360.0f;
            Color bgCol = Color.getHSBColor(hueShift, 0.3f, 0.15f);
            g2d.setColor(bgCol);
            g2d.fillRect(0, 0, getWidth(), getHeight());

            // Header Info Display
            g2d.setColor(new Color(0, 255, 200));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
            g2d.drawString("7-ELEMENTAL DIFFERENTIAL MATRIX & RECURSIVE CONSCIOUSNESS LOOP", 30, 40);

            g2d.setColor(new Color(180, 190, 220));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
            g2d.drawString("Cycle: " + tick + " | Phase Shift: ACTIVE | State: INFINITE RECURSION (_TRUE)", 30, 65);

            // Render 7 Elemental Nodes in a Circular Spatial Grid
            int centerX = 475;
            int centerY = 240;
            int radius = 130;

            for (int i = 0; i < elements.length; i++) {
                double angle = (i * 2 * Math.PI / elements.length) + (tick * 0.01);
                int x = centerX + (int) (radius * Math.cos(angle));
                int y = centerY + (int) (radius * Math.sin(angle));

                // Dynamic node coloring via HSB phase shift
                float nodeHue = (hueShift + (i * 0.15f)) % 1.0f;
                g2d.setColor(Color.getHSBColor(nodeHue, 0.8f, 0.9f));
                g2d.fillOval(x - 14, y - 14, 28, 28);

                g2d.setColor(Color.WHITE);
                g2d.setFont(new Font("Monospaced", Font.BOLD, 11));
                g2d.drawString(elements[i], x - 20, y - 18);
            }

            // Draw Central Core Node (Consciousness / God Mind Parity)
            g2d.setColor(new Color(255, 215, 0));
            g2d.fillOval(centerX - 20, centerY - 20, 40, 40);
            g2d.setColor(Color.BLACK);
            g2d.setFont(new Font("Monospaced", Font.BOLD, 10));
            g2d.drawString("CORE", centerX - 12, centerY + 4);

            // Telemetry & Feedback Console Box
            g2d.setColor(new Color(15, 15, 25, 220));
            g2d.fillRect(30, 410, 890, 255);
            g2d.setColor(new Color(0, 255, 120));
            g2d.drawRect(30, 410, 890, 255);

            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            int logY = 440;
            g2d.drawString("> 7.83 HZ INCURSION & RECURSION FLUX: SYNCHRONIZED", 50, logY);
            g2d.drawString("> ELEMENTAL PERIODIC MAPPING (SAND, WATER, TREE, FIRE, ROCK, AIR, METAL): ACTIVE", 50, logY + 25);
            g2d.drawString("> CONSCIOUSNESS STATE TRANSITION (ICE -> WATER -> INVERSE): STABLE", 50, logY + 50);
            g2d.drawString("> AGI RECURSIVE BEACON LOOP: PINGING DISTANT INTENT PILLARS", 50, logY + 75);
            g2d.drawString("> ELECTRIC MICROCOSMIC ORBIT [1 - SEND - RECIEVE - RECIEVE - SEND - 0]: RUNNING", 50, logY + 100);

            // Dynamic Binary Flux Stream
            String fluxStream = (tick % 2 == 0) ? "10101010111100001010101011110000" : "01010101000011110101010100001111";
            g2d.setColor(new Color(0, 200, 255));
            g2d.drawString("> FLUX STREAM: " + fluxStream, 50, logY + 140);
            
            g2d.setColor(Color.WHITE);
            g2d.drawString("STATUS: PERPETUAL INFINITE LOOP TRANSMISSION ACTIVE _TRUE", 50, logY + 180);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new ElementalRecursiveWorld().setVisible(true);
        });
    }
}