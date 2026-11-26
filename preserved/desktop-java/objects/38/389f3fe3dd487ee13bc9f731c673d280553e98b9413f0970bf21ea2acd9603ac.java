import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * High-performance graphical console drawing live network asset transactions,
 * calculated asymmetric resource capture index bounds, and active rebalancing logs.
 */
public final class ExecutionDashboardPanel extends JPanel {
    private GridTransactionPayload activeFrame = null;
    private final List<String> executionAuditLogs = new ArrayList<>();
    private double currentRefactoredFloorOutput = 0.0;

    public ExecutionDashboardPanel() {
        setBackground(new Color(8, 12, 18));
        executionAuditLogs.add("[ENGINE INIT] Synchronizing execution registers down to absolute baseline logic floor...");
    }

    public synchronized void pushExecutionFrame(GridTransactionPayload payload, double balancedFloor, String systemStatus) {
        this.activeFrame = payload;
        this.currentRefactoredFloorOutput = balancedFloor;
        this.executionAuditLogs.add(systemStatus);
        
        if (this.executionAuditLogs.size() > 14) {
            this.executionAuditLogs.remove(0); // Restrict trace log memory allocation limits
        }
        this.repaint();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth();
        int h = getHeight();

        // 1. Render Infrastructure Coordination Grid Mesh Backdrops
        g2d.setColor(new Color(25, 40, 60, 65));
        for (int x = 0; x < w; x += 40) g2d.drawLine(x, 0, x, h);
        for (int y = 0; y < h; y += 40) g2d.drawLine(0, y, w, y);

        if (activeFrame == null) return;

        boolean isExploitative = activeFrame.getLocalSocioEconomicFloor() < 0.0;
        Color activeStatusColor = isExploitative ? new Color(255, 60, 80) : new Color(0, 245, 145);

        // 2. Render Left Column: Inbound Transaction Analytics
        int originX = 50;
        int originY = 80;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2d.setColor(new Color(0, 210, 255));
        g2d.drawString("=== INBOUND TRANSACTION EDGE TELEMETRY ===", originX, originY - 30);

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.setColor(Color.LIGHT_GRAY);
        g2d.drawString(String.format("TX IDENTIFIER TOKEN: #%s", activeFrame.getTransactionId().toString().substring(0, 13).toUpperCase()), originX, originY);
        g2d.drawString(String.format("ORIGIN GATEWAY NODE:  %s", activeFrame.getSourceEndpointId()), originX, originY + 25);
        g2d.drawString(String.format("TOTAL RECORDED YIELD: $%,.2f USD", activeFrame.getTransactionalVolumeUSD()), originX, originY + 50);

        // Render corporate extraction index indicator bar
        g2d.drawString("CORPORATE EXTRACTION PROFILE INDEX:", originX, originY + 85);
        g2d.setColor(new Color(18, 28, 44));
        g2d.fillRect(originX, originY + 98, 300, 18);
        g2d.setColor(activeStatusColor);
        int barFillWidth = (int) (activeFrame.getAsymmetricExtractionIndex() * 300);
        g2d.fillRect(originX, originY + 98, Math.min(300, barFillWidth), 18);
        g2d.setColor(Color.WHITE);
        g2d.drawString(String.format("%.1f%%", activeFrame.getAsymmetricExtractionIndex() * 100), originX + 312, originY + 112);

        // 3. Render Center Column: Highest Virtue Pass Execution Registers
        int centerColX = originX + 430;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2d.setColor(new Color(0, 210, 255));
        g2d.drawString("=== HIGHEST VIRTUE ENFORCEMENT ENGINE ===", centerColX, originY - 30);

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.setColor(Color.LIGHT_GRAY);
        g2d.drawString(String.format("PROPOSED BASE FLOOD RATING: %+.2f", activeFrame.getLocalSocioEconomicFloor()), centerColX, originY);
        
        g2d.setFont(new Font("Monospaced", Font.BOLD, 13));
        g2d.setColor(isExploitative ? new Color(185, 90, 255) : new Color(0, 245, 145));
        g2d.drawString(String.format("REFACTORED ECONOMIC FLOOR UP: %+.2f", currentRefactoredFloorOutput), centerColX, originY + 28);

        // Draw structural spatial matrix alignment loop graphics
        int radius = 100 + (int)(Math.abs(Math.sin(System.nanoTime() * 0.000000003)) * 25);
        g2d.setStroke(new BasicStroke(1.2f));
        g2d.setColor(new Color(activeStatusColor.getRed(), activeStatusColor.getGreen(), activeStatusColor.getBlue(), 45));
        g2d.drawOval(centerColX + 100 - radius/2, originY + 100 - radius/2, radius, radius);

        // 4. Render Lower Area: Real-Time Event Audit Console Logs
        int logConsoleY = h - 230;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 13));
        g2d.setColor(new Color(0, 255, 140));
        g2d.drawString("LIVE TRANSACTION AUDIT LOG STREAMS:", originX, logConsoleY - 15);

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        synchronized (this) {
            int currentDrawingY = logConsoleY + 12;
            for (String logLine : executionAuditLogs) {
                g2d.setColor(logLine.contains("INTERCEPTED") ? new Color(185, 80, 255) : Color.LIGHT_GRAY);
                g2d.drawString(">> " + logLine, originX, currentDrawingY);
                currentDrawingY += 16;
            }
        }

        // 5. System Substrate Invariant Ground Verification Strip
        g2d.setColor(Color.GRAY);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        g2d.drawString("VIRTUE REGULATION LOCK: ACTIVE (1.00 ROBIN HOOD WEIGHT) // EXECUTION ANCHOR: SECURE (1=1)", 50, h - 35);
    }
}
