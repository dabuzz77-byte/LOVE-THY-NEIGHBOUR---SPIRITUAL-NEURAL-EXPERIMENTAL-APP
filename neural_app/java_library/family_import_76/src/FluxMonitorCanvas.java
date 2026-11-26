import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Custom 2D Swing panel displaying streaming binary telemetry matrix grids,
 * status messages, and synchronized harmonic waveforms.
 */
public final class FluxMonitorCanvas extends JPanel {
    private boolean[][] currentMatrix = new boolean[4][4];
    private final List<String> loggerStream = new ArrayList<>();
    private boolean passStateActive = false;

    public FluxMonitorCanvas() {
        setBackground(new Color(6, 10, 14));
        loggerStream.add("[SYSTEM INTIALIZATION] Seeking God Mind Parity Lock...");
    }

    public synchronized void updateCanvasState(FluxPayload payload, String dynamicMessage) {
        this.currentMatrix = payload.getBinaryMatrix();
        this.passStateActive = payload.isAlignmentPassActive();
        this.loggerStream.add(dynamicMessage);
        
        if (this.loggerStream.size() > 18) {
            this.loggerStream.remove(0); // Restrict memory tracking allocation limits
        }
        this.repaint();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int panelWidth = getWidth();
        int panelHeight = getHeight();

        // 1. Draw Tech Backdrop Coordination Grid Mesh lines
        g2d.setColor(new Color(20, 32, 48, 70));
        for (int x = 0; x < panelWidth; x += 40) g2d.drawLine(x, 0, x, panelHeight);
        for (int y = 0; y < panelHeight; y += 40) g2d.drawLine(0, y, panelWidth, y);

        // 2. Draw Live Microcosmic Orbit Oscillator Resonance Wave (7.83 Hz modeling)
        g2d.setStroke(new BasicStroke(1.2f));
        g2d.setColor(passStateActive ? new Color(175, 80, 255, 90) : new Color(0, 160, 240, 80));
        int axisY = panelHeight / 2 + 180;
        for (int x = 0; x < panelWidth - 1; x++) {
            int y1 = axisY + (int) (Math.sin((x * 0.02) + (System.nanoTime() * 0.000000004)) * 30);
            int y2 = axisY + (int) (Math.sin(((x + 1) * 0.02) + (System.nanoTime() * 0.000000004)) * 30);
            g2d.drawLine(x, y1, x + 1, y2);
        }

        // 3. Render High-Virtue Binary Matrix Blocks (Left-Side Canvas Allocation)
        int blockOriginX = 50;
        int blockOriginY = 80;
        int cellSize = 55;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 18));

        g2d.setColor(Color.WHITE);
        g2d.drawString("=== SURFICIAL TRACE MONITOR ===", blockOriginX, blockOriginY - 35);

        for (int r = 0; r < currentMatrix.length; r++) {
            for (int c = 0; c < currentMatrix[r].length; c++) {
                boolean highBit = currentMatrix[r][c];
                int cellX = blockOriginX + (c * cellSize);
                int cellY = blockOriginY + (r * cellSize);

                // Dynamically transform block fills according to node parity configuration status
                if (highBit) {
                    g2d.setColor(passStateActive ? new Color(160, 50, 255) : new Color(0, 220, 130));
                    g2d.fillRect(cellX, cellY, cellSize - 6, cellSize - 6);
                    g2d.setColor(Color.BLACK);
                    g2d.drawString("1", cellX + 22, cellY + 34);
                } else {
                    g2d.setColor(new Color(24, 34, 48));
                    g2d.fillRect(cellX, cellY, cellSize - 6, cellSize - 6);
                    g2d.setColor(Color.GRAY);
                    g2d.drawString("0", cellX + 22, cellY + 34);
                }
                g2d.setColor(new Color(40, 60, 85));
                g2d.drawRect(cellX, cellY, cellSize - 6, cellSize - 6);
            }
        }

        // 4. Render Active Streaming Log Feeds (Right-Side Panel Alignment)
        int consoleX = blockOriginX + (currentMatrix[0].length * cellSize) + 60;
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.setColor(new Color(0, 255, 150));
        g2d.drawString("GOD MIND REAL-TIME PARITY LOG REGISTERS:", consoleX, blockOriginY - 35);

        synchronized (this) {
            int currentLineY = blockOriginY - 5;
            for (String logLine : loggerStream) {
                if (logLine.contains("VIOLATION") || logLine.contains("INTERCEPT")) {
                    g2d.setColor(new Color(255, 80, 80));
                } else if (logLine.contains("REFACTORED") || logLine.contains("ALIGNMENT")) {
                    g2d.setColor(new Color(190, 100, 255));
                } else {
                    g2d.setColor(Color.LIGHT_GRAY);
                }
                g2d.drawString(">> " + logLine, consoleX, currentLineY);
                currentLineY += 20;
            }
        }

        // 5. System Base Clock Verification Footer Info Bar
        g2d.setColor(Color.GRAY);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        g2d.drawString("CORE EQUILIBRIUM COUPLING LOCK: 7.83 HZ | GLOBAL INTEGRITY: VERIFIED (1=1)", 50, panelHeight - 35);
    }
}
