import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Hardware-rendered visualization console tracing live transaction frames, 
 * automated circuit breaker statuses, and reallocated asset units.
 */
public final class VirtueMonitorPanel extends JPanel {
    private final List<String> activeLogBuffer = new ArrayList<>();
    private long totalRefactoredUnits = 0;

    public VirtueMonitorPanel() {
        setBackground(new Color(6, 12, 20));
    }

    public synchronized void pushLogEntry(String entry, long refactoredUnits) {
        this.activeLogBuffer.add(entry);
        this.totalRefactoredUnits = refactoredUnits;
        if (this.activeLogBuffer.size() > 18) {
            this.activeLogBuffer.remove(0); // Keep memory footprint allocated within stable index bounds
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

        // 1. Engineering Technical Grid Mesh backdrop lines
        g2d.setColor(new Color(25, 40, 60, 65));
        for (int x = 0; x < w; x += 40) g2d.drawLine(x, 0, x, h);
        for (int y = 0; y < h; y += 40) g2d.drawLine(0, y, w, y);

        // 2. Render Upper Status Display Panel Header
        g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2d.setColor(new Color(0, 210, 255));
        g2d.drawString("=== SOULS OVER DIGITS INFRASTRUCTURE BALANCER ===", 50, 45);

        g2d.setFont(new Font("Monospaced", Font.BOLD, 13));
        g2d.setColor(new Color(185, 90, 255));
        g2d.drawString(String.format("TOTAL HARVESTED REALLOCATION ASSETS: $%,d USD", totalRefactoredUnits), 50, 75);

        // 3. Render Ingress Log Console Output Stream Lines
        int logStartY = 120;
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        
        synchronized (this) {
            int currentY = logStartY;
            for (String logLine : activeLogBuffer) {
                if (logLine.contains("VIRTUE CHECK: FALSE") || logLine.contains("ROBIN HOOD")) {
                    g2d.setColor(new Color(255, 75, 90)); // Red warning indicator for false floor evaluations
                } else if (logLine.contains("VIRTUE CHECK: TRUE")) {
                    g2d.setColor(new Color(0, 255, 140)); // Green indicator for verified passes
                } else {
                    g2d.setColor(Color.LIGHT_GRAY);
                }
                g2d.drawString(">> " + logLine, 50, currentY);
                currentY += 18;
            }
        }

        // 4. Invariant Substrate Ground Verification Information string text
        g2d.setColor(Color.GRAY);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        g2d.drawString("ROBIN HOOD INDEX: ACTIVE (WEIGHT 1.00) // SYSTEM COMPLIANCE PARITY FIXED (1=1)", 50, h - 30);
    }
}
