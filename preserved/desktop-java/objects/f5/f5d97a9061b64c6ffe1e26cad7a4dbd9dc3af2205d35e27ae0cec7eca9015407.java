import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;

public class SandcastleKarmicWorld extends JFrame {

    private int tick = 0;
    private final Random random = new Random();

    public SandcastleKarmicWorld() {
        setTitle("Sandcastle & Karmic World Grid Simulator");
        setSize(950, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        WorldPanel canvas = new WorldPanel();
        add(canvas, BorderLayout.CENTER);

        Timer timer = new Timer(100, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                tick++;
                canvas.repaint();
            }
        });
        timer.start();
    }

    class WorldPanel extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Sky Backdrop
            g2d.setColor(new Color(135, 206, 235));
            g2d.fillRect(0, 0, getWidth(), 200);

            // Ocean Terrain (Left)
            g2d.setColor(new Color(30, 144, 255));
            g2d.fillRect(0, 200, 250, getHeight() - 200);

            // Beach Terrain (Middle)
            g2d.setColor(new Color(238, 214, 175));
            g2d.fillRect(250, 200, 350, getHeight() - 200);

            // Desert Terrain (Right)
            g2d.setColor(new Color(244, 164, 96));
            g2d.fillRect(600, 200, getWidth() - 600, getHeight() - 200);

            // Header Info Display
            g2d.setColor(Color.DARK_GRAY);
            g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
            g2d.drawString("WORLD GRID: OCEAN - BEACH - DESERT | KARMIC FORCE ACTIVE", 30, 35);

            // Draw Animated Waves on Ocean
            g2d.setColor(new Color(255, 255, 255, 100));
            for (int i = 0; i < 5; i++) {
                int waveX = (int)((tick * 3 + i * 50) % 230);
                g2d.drawArc(waveX, 250 + (i * 40), 40, 20, 0, 180);
            }

            // Draw Sandcastles with Karmic Wall Integrity
            int castleIntegrity1 = 80 + (int)(Math.sin(tick * 0.05) * 15);
            int castleIntegrity2 = 65 + (int)(Math.cos(tick * 0.04) * 20);

            drawSandcastle(g2d, 320, 340, "Sovereign Citadel", castleIntegrity1);
            drawSandcastle(g2d, 460, 380, "Commons Bastion", castleIntegrity2);

            // Draw Denizens navigating the world grid
            int denizenX = 280 + (int)(Math.sin(tick * 0.03) * 80);
            int denizenY = 360 + (int)(Math.cos(tick * 0.03) * 30);
            
            g2d.setColor(new Color(200, 0, 0));
            g2d.fillOval(denizenX, denizenY, 14, 14);
            g2d.setColor(Color.BLACK);
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            g2d.drawString("Denizen (Karma: Balanced)", denizenX - 35, denizenY - 6);

            // Virtue Assessment & Karmic Ledger Log Box
            g2d.setColor(new Color(30, 30, 40));
            g2d.fillRect(30, 480, 880, 170);
            g2d.setColor(new Color(0, 255, 120));
            g2d.drawRect(30, 480, 880, 170);

            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            int logY = 510;
            g2d.drawString("> ENVIRONMENT: OCEAN, BEACH & DESERT WORLD GRID SYNCHRONIZED", 50, logY);
            g2d.drawString("> SANDCASTLE WALLS: KARMIC FORCE FIELD APPLIED (WALL STRENGTH = VIRTUE)", 50, logY + 25);
            g2d.drawString("> VIRTUE ASSESSMENT: COMPASSION, TRUTH & SOVEREIGNTY EVALUATION [TICK " + tick + "]", 50, logY + 50);
            g2d.drawString("> WAVE EROSION COUNTERED BY ABSOLUTE ACCOUNTABILITY MATRIX", 50, logY + 75);
            
            g2d.setColor(new Color(0, 220, 255));
            g2d.drawString("STATUS: ECO-SYSTEMIC KARMIC ALIGNMENT & WALL PARITY CONFIRMED _TRUE", 50, logY + 110);
        }

        private void drawSandcastle(Graphics2D g2d, int x, int y, String name, int integrity) {
            // Main structure
            g2d.setColor(new Color(210, 180, 140));
            g2d.fillRect(x, y, 70, 60);
            
            // Towers
            g2d.fillRect(x - 12, y - 25, 22, 85);
            g2d.fillRect(x + 60, y - 25, 22, 85);

            // Karmic Wall Health Indicator
            g2d.setColor(integrity > 70 ? new Color(0, 200, 0) : new Color(220, 150, 0));
            g2d.fillRect(x - 12, y - 38, (int)(94 * (integrity / 100.0)), 6);
            
            g2d.setColor(Color.DARK_GRAY);
            g2d.drawRect(x - 12, y - 38, 94, 6);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 11));
            g2d.drawString(name + " [" + integrity + "%]", x - 15, y - 46);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new SandcastleKarmicWorld().setVisible(true);
        });
    }
}