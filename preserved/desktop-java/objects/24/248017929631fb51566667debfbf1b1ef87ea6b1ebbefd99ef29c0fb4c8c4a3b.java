import javax.swing.*;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * MODULE 6a: GRAPHICAL MONITORING SUBSTRATE PANEL
 * Handles isolated high-performance 2D vector animation arrays for active nodes.
 */
public class GraphicalMonitorPanel extends JPanel implements java.awt.event.ActionListener {
    
    private final CentralPortRouter serverBusEngine;
    private final Timer animationTickerClock;

    public GraphicalMonitorPanel(CentralPortRouter serverBusEngine) {
        this.serverBusEngine = serverBusEngine;
        setBackground(new Color(4, 6, 12));
        this.animationTickerClock = new Timer(32, this); // Fast 30fps dashboard redraw frequency
        this.animationTickerClock.start();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth();
        int h = getHeight();
        int cx = w / 2;
        int cy = h / 2 - 40;

        // Render clean structural grid line coordinate paths
        g2d.setStroke(new BasicStroke(0.5f));
        g2d.setColor(new Color(0, 180, 255, 12));
        for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h);
        for (int j = 0; j < h; j += 50) g2d.drawLine(0, j, w, j);

        List<BridgeDataVector> continuousLattice = serverBusEngine.getDynamicRegistryLattice();
        g2d.setStroke(new BasicStroke(1.2f));

        for (BridgeDataVector segment : continuousLattice) {
            int layoutX = (segment.getNodeUUID().hashCode() % (w - 150)) + 75;
            int layoutY = (Math.abs(Long.hashCode(segment.getExecutionNanoMarker())) % (h - 150)) + 75;

            g2d.setColor(new Color(255, 255, 255, 15));
            g2d.drawLine(layoutX, layoutY, cx, cy);

            int shapeSize = 16;
            if (segment.getCoreProcessingSector().equals("LOCAL_LLAMA3")) g2d.setColor(new Color(0, 255, 190));
            else if (segment.getCoreProcessingSector().equals("LOCAL_FLUX")) g2d.setColor(new Color(255, 130, 0));
            else g2d.setColor(new Color(160, 60, 255));

            g2d.fill(new Ellipse2D.Double(layoutX - shapeSize/2.0, layoutY - shapeSize/2.0, shapeSize, shapeSize));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
            g2d.setColor(Color.LIGHT_GRAY);
            g2d.drawString(segment.getCoreProcessingSector(), layoutX + 12, layoutY + 4);
        }

        // Central Anchor Rings
        g2d.setStroke(new BasicStroke(2.0f));
        g2d.setColor(new Color(255, 255, 255, 40));
        g2d.drawOval(cx - 100, cy - 100, 200, 200);
        
        g2d.setColor(Color.WHITE);
        g2d.fill(new Ellipse2D.Double(cx - 8, cy - 8, 16, 16));
        g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
        g2d.drawString("DECOUPLED 8-MODULE RECONCILIATION APEX", cx - 140, cy - 115);

        // Telemetry Label Prints
        g2d.setColor(new Color(0, 255, 180));
        g2d.drawString(String.format("GLOBAL PARITY MATRIX STATUS: %,.4f%% HARMONIZED", serverBusEngine.getGlobalParityIndex() * 100), 20, h - 50);
        g2d.setColor(new Color(255, 140, 0));
        g2d.drawString("INTEGRATION METRIC CHANNEL ROUTE PORT: " + serverBusEngine.getActiveLocalPort(), 20, h - 30);
        g2d.setColor(Color.WHITE);
        g2d.drawString("SCHUMANN BASAL DRIVING CLOCK INDEX: 7.83Hz CONSTANT LOCKED", 20, h - 10);
    }

    @Override
    public void actionPerformed(java.awt.event.ActionEvent e) {
        repaint();
    }
}