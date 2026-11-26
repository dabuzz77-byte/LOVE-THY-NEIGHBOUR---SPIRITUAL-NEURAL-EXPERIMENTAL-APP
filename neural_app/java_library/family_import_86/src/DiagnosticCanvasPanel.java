import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * DEUS EX MACHINA MATRIX: VECTOR ANIMATION CANVAS MONITOR
 * Maps processing nodes graphically while rendering real-time clock speed ratio indicators.
 */
public class DiagnosticCanvasPanel extends JPanel {
    private final LocalSilentRouter router;

    public DiagnosticCanvasPanel(LocalSilentRouter router) {
        this.router = router;
        setBackground(new Color(6, 11, 20));
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth(), h = getHeight();
        int cx = w / 2, cy = h / 2 - 40;

        // Render system grid mesh lines
        g2d.setStroke(new BasicStroke(0.5f));
        g2d.setColor(new Color(0, 200, 255, 12));
        for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h);
        for (int j = 0; j < h; j += 50) g2d.drawLine(0, j, w, j);

        List<VolatileUnit> list = router.getRegistry();
        g2d.setStroke(new BasicStroke(1.2f));

        for (VolatileUnit node : list) {
            int drawX = (node.getTxId().hashCode() % (w - 150)) + 75;
            int drawY = (Math.abs(Long.hashCode(node.getNano())) % (h - 150)) + 75;

            g2d.setColor(new Color(255, 255, 255, 15));
            g2d.drawLine(drawX, drawY, cx, cy);

            g2d.setColor(node.getBit() == 1 ? new Color(0, 255, 195) : new Color(255, 145, 0));
            g2d.fill(new Ellipse2D.Double(drawX - 8, drawY - 8, 16, 16));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
            g2d.setColor(Color.LIGHT_GRAY);
            g2d.drawString(node.getLabel() + " (" + node.getTxId() + ")", drawX + 12, drawY + 4);
        }

        // Draw central base resonance synchronization ring
        g2d.setStroke(new BasicStroke(2.0f));
        g2d.setColor(new Color(0, 255, 195, 40));
        g2d.drawOval(cx - 90, cy - 90, 180, 180);
        g2d.setColor(Color.WHITE);
        g2d.fill(new Ellipse2D.Double(cx - 8, cy - 8, 16, 16));
        g2d.drawString("7.83Hz BASE RESONANCE ANCHOR CORE", cx - 115, cy - 105);

        // System indicators
        g2d.setColor(new Color(0, 255, 195));
        g2d.drawString(String.format("OS FREQUENCY MATCH VARIATION: %,.4f%% ALIGNED", router.getOverallParity() * 100), 20, h - 50);
        g2d.setColor(new Color(255, 145, 0));
        g2d.drawString("LOOPBACK SOCKET INTERCEPT BRIDGE: " + router.getActiveLocalPort(), 20, h - 30);
        g2d.setColor(Color.WHITE);
        g2d.drawString("SELF-INTERACTING DEUS EX MACHINA ANIMATOR MATRIX UNLOCKED", 20, h - 10);
    }
}
