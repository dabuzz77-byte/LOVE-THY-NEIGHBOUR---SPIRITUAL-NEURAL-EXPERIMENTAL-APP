package net.activeinference.beacon.orbit;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.BasicStroke;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.util.Random;

public class ElectricityPanel extends JPanel {
    private final Random rand = new Random();
    private double dischargePhase = 0.0;

    public ElectricityPanel() {
        setBackground(OrbitTheme.BG_PANEL);
    }

    public void incrementOrbitPhase() {
        this.dischargePhase += 0.15;
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth();
        int h = getHeight();
        int midY = h / 2;

        // Draw background plasma field arc trail
        g2.setStroke(new BasicStroke(5.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
        g2.setColor(OrbitTheme.ELEC_GLOW);
        drawFractalLightningArc(g2, 10, midY, w - 10, midY, 14);

        // Draw hot electrical core filament channel
        g2.setStroke(new BasicStroke(1.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
        g2.setColor(OrbitTheme.ELEC_CORE);
        drawFractalLightningArc(g2, 10, midY, w - 10, midY, 6);
    }

    private void drawFractalLightningArc(Graphics2D g2, int x1, int y1, int x2, int y2, int displacement) {
        if ((x2 - x1) < 5) {
            g2.drawLine(x1, y1, x2, y2);
        } else {
            int midX = (x1 + x2) / 2;
            int midY = (y1 + y2) / 2;
            midY += (rand.nextInt(displacement * 2) - displacement) + (Math.sin(dischargePhase) * 2);
            drawFractalLightningArc(g2, x1, y1, midX, midY, displacement / 2);
            drawFractalLightningArc(g2, midX, midY, x2, y2, displacement / 2);
        }
    }
}
