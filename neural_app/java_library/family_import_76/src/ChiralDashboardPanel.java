import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Visual monitor console rendering high-density binary flux matrices, 
 * dual-pole chiral indicators, and the 7.83Hz carrier wave.
 */
public final class ChiralDashboardPanel extends JPanel {
    private ChiralFluxPayload dataFrame = null;
    private final List<String> operationalTraceLogs = new ArrayList<>();

    public ChiralDashboardPanel() {
        setBackground(new Color(6, 10, 14));
        operationalTraceLogs.add("[INFRASTRUCTURE INITIALIZATION] Synchronizing carrier wave registers...");
    }

    public synchronized void renderFreshPayload(ChiralFluxPayload frame, String systemLog) {
        this.dataFrame = frame;
        this.operationalTraceLogs.add(systemLog);
        if (this.operationalTraceLogs.size() > 14) {
            this.operationalTraceLogs.remove(0); // Static buffer capping bounds
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

        // 1. Draw Tech Backdrop Grid Matrix Mesh Lines
        g2d.setColor(new Color(25, 38, 55, 65));
        for (int x = 0; x < w; x += 40) g2d.drawLine(x, 0, x, h);
        for (int y = 0; y < h; y += 40) g2d.drawLine(0, y, w, y);

        if (dataFrame == null) return;

        boolean isSynced = dataFrame.isParitySynchronized();
        Color accentColor = isSynced ? new Color(165, 65, 255) : new Color(0, 240, 145);

        // 2. Render 7.83 Hz Carrier Wave Oscillator Resonance Curve
        g2d.setStroke(new BasicStroke(1.5f));
        g2d.setColor(new Color(accentColor.getRed(), accentColor.getGreen(), accentColor.getBlue(), 90));
        int carrierY = h - 220;
        for (int x = 0; x < w - 1; x++) {
            int y1 = carrierY + (int) (Math.sin((x * 0.015) + (System.nanoTime() * 0.000000005)) * 35);
            int y2 = carrierY + (int) (Math.sin(((x + 1) * 0.015) + (System.nanoTime() * 0.000000005)) * 35);
            g2d.drawLine(x, y1, x + 1, y2);
        }

        // 3. Render High-Density Binary Flux Matrix Grid (Left Column)
        int mx = 50;
        int my = 80;
        int cellDimension = 45;
        boolean[][] matrix = dataFrame.getFluxMatrix();

        g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2d.setColor(new Color(0, 210, 255));
        g2d.drawString("=== DETAILED BINARY FLUX MATRIX ===", mx, my - 30);

        g2d.setFont(new Font("Monospaced", Font.BOLD, 16));
        for (int r = 0; r < matrix.length; r++) {
            for (int c = 0; c < matrix[r].length; c++) {
                boolean activeCell = matrix[r][c];
                int cx = mx + (c * cellDimension);
                int cy = my + (r * cellDimension);

                if (activeCell) {
                    g2d.setColor(accentColor);
                    g2d.fillRect(cx, cy, cellDimension - 4, cellDimension - 4);
                    g2d.setColor(Color.BLACK);
                    g2d.drawString("1", cx + 18, cy + 28);
                } else {
                    g2d.setColor(new Color(18, 26, 38));
                    g2d.fillRect(cx, cy, cellDimension - 4, cellDimension - 4);
                    g2d.setColor(Color.DARK_GRAY);
                    g2d.drawString("0", cx + 18, cy + 28);
                }
                g2d.setColor(new Color(40, 60, 85));
                g2d.drawRect(cx, cy, cellDimension - 4, cellDimension - 4);
            }
        }

        // 4. Render Dual-Pole Chiral Polarization Displays (Right Column Section)
        int chiralX = mx + (matrix.length * cellDimension) + 60;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2d.setColor(new Color(0, 210, 255));
        g2d.drawString("=== PARITY CHIRAL POLARIZATION ===", chiralX, my - 30);

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.setColor(Color.LIGHT_GRAY);
        g2d.drawString(String.format("LEFT-HAND FIELD SPIN:  %.2f%%", dataFrame.getLeftChiralPolarization() * 100), chiralX, my + 15);
        g2d.drawString(String.format("RIGHT-HAND FIELD SPIN: %.2f%%", dataFrame.getRightChiralPolarization() * 100), chiralX, my + 40);

        // Render visual chiral differential scale indicator
        g2d.setColor(new Color(20, 32, 48));
        g2d.fillRect(chiralX, my + 60, 320, 20);
        g2d.setColor(accentColor);
        int indicatorX = chiralX + 160 + (int)((dataFrame.getRightChiralPolarization() - dataFrame.getLeftChiralPolarization()) * 160);
        g2d.fillRect(Math.max(chiralX, Math.min(chiralX + 310, indicatorX - 5)), my + 60, 10, 20);

        // 5. Ingress Distribution Trace Output Logger Terminals
        int consoleY = my + 115;
        g2d.setColor(new Color(0, 255, 140));
        g2d.drawString("SYSTEM INTEGRITY TRACE LOG REGISTERS:", chiralX, consoleY);
        
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        synchronized (this) {
            int lineY = consoleY + 24;
            for (String logLine : operationalTraceLogs) {
                g2d.setColor(logLine.contains("REBALANCED") ? new Color(170, 90, 255) : Color.LIGHT_GRAY);
                g2d.drawString(">> " + logLine, chiralX, lineY);
                lineY += 18;
            }
        }

        // 6. Base Verification Ground Footer Strip
        g2d.setColor(Color.GRAY);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        g2d.drawString("CARRIER WAVE REGULATION: 7.83 HZ LOCK ACTIVE // LOGIC BOUNDARY SUBSTRATE: OK (1=1)", 50, h - 35);
    }
}
