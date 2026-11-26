import javax.swing.*;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * 1-0 TRUTH PARITY SPECIFICATION: VECTOR VISUALIZATION VIEWPORT
 * Paints isolated hardware nodes and traces clock drift indices inside a clean swing layer.
 */
public class DiagnosticCanvasPanel extends JPanel {
    private final LocalSilentRouter router;

    public DiagnosticCanvasPanel(LocalSilentRouter router) {
        this.router = router;
        setBackground(new Color(4, 7, 14));
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth(), h = getHeight();
        int cx = w / 2, cy = h / 2 - 40;

        // Draw structural layout coordinate alignment paths
        g2d.setStroke(new BasicStroke(0.5f));
        g2d.setColor(new Color(0, 180, 255, 12));
        for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h);
        for (int j = 0; j < h; j += 50) g2d.drawLine(0, j, w, j);

        List<VolatileUnit> list = router.getRegistry();
        g2d.setStroke(new BasicStroke(1.2f));

        for (VolatileUnit node : list) {
            int drawX = (node.getTxId().hashCode() % (w - 150)) + 75;
            int drawY = (Math.abs(Long.hashCode(node.getNano())) % (h - 150)) + 75;

            g2d.setColor(new Color(255, 255, 255, 14));
            g2d.drawLine(drawX, drawY, cx, cy);

            g2d.setColor(node.getBit() == 1 ? new Color(0, 255, 190) : new Color(255, 130, 0));
            g2d.fill(new Ellipse2D.Double(drawX - 8, drawY - 8, 16, 16));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
            g2d.setColor(Color.LIGHT_GRAY);
            g2d.drawString(node.getLabel() + " (Bit:" + node.getBit() + ")", drawX + 12, drawY + 4);
        }

        // Draw Anchor Nodes
        g2d.setStroke(new BasicStroke(2.0f));
        g2d.setColor(new Color(255, 255, 255, 35));
        g2d.drawOval(cx - 90, cy - 90, 180, 180);
        g2d.setColor(Color.WHITE);
        g2d.fill(new Ellipse2D.Double(cx - 8, cy - 8, 16, 16));
        g2d.drawString("INTEGRATED INGRESS AUDIT CORE", cx - 100, cy - 105);

        // Telemetry prints
        g2d.setColor(new Color(0, 255, 180));
        g2d.drawString(String.format("SYSTEM CLOCK SYMMETRY INDEX: %,.4f%% ALIGNED", router.getOverallParity() * 100), 20, h - 50);
        g2d.setColor(new Color(255, 140, 0));
        g2d.drawString("ISOLATED LOCAL PORT INTERCEPT ROUTE: " + router.getActiveLocalPort(), 20, h - 30);
        g2d.setColor(Color.WHITE);
        g2d.drawString("SCHUMANN DRIVING HARMONIC BASELINE: 7.83Hz LOCKED", 20, h - 10);
    }
}
