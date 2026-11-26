package engine.ui;

import engine.model.TelemetryModel;
import java.awt.Color; // ✨ FIXED: Added explicit color token import
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import javax.swing.JPanel;

public class TopologyCanvas extends JPanel {
    private final TelemetryModel model;

    public TopologyCanvas(TelemetryModel model) {
        this.model = model;
        this.setBackground(AestheticTheme.BG_MATRIX);
        this.setBorder(AestheticTheme.createBorder("PERIMETER INTERFERENCE SUB-NET TRACER", AestheticTheme.ACCENT_MAGENTA));
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int cx = getWidth() / 2;
        int cy = getHeight() / 2;

        g2.setColor(AestheticTheme.ACCENT_MAGENTA);
        g2.fillOval(cx - 10, cy - 10, 20, 20);
        g2.drawString("LOCALHOST GATEWAY", cx - 55, cy - 15);

        var nodes = model.getPerimeterNodes();
        synchronized (nodes) {
            for (int i = 0; i < nodes.size(); i++) {
                double slice = 2 * Math.PI / nodes.size();
                int nx = cx + (int) (Math.cos(i * slice) * 110);
                int ny = cy + (int) (Math.sin(i * slice) * 110);

                g2.setColor(AestheticTheme.BG_PANEL);
                g2.drawLine(cx, cy, nx, ny);

                var targetNode = nodes.get(i);
                g2.setColor(targetNode.status.equals("LATCHED") ? AestheticTheme.ACCENT_GREEN : AestheticTheme.ACCENT_ORANGE);
                g2.fillOval(nx - 7, ny - 7, 14, 14);
                g2.setColor(Color.WHITE);
                g2.setFont(AestheticTheme.MONO_FONT);
                g2.drawString(targetNode.id, nx + 10, ny + 4);
            }
        }
    }
}
