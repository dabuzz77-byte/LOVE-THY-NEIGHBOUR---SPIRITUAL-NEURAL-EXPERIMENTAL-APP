package com.system.core.view;

import com.system.core.model.TopographyPayload;
import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Visual graphic dashboard interface rendering streaming binary vector grids,
 * active conflict coefficients, and asynchronous transaction registers.
 */
public final class AlignmentConsolePanel extends JPanel {
    private TopographyPayload liveFrame = null;
    private boolean[][] refactoredMatrixField = null;
    private final List<String> diagnosticTraceLogs = new ArrayList<>();

    public AlignmentConsolePanel() {
        setBackground(new Color(6, 10, 15));
        diagnosticTraceLogs.add("[SYSTEM INIT] Launching alignment context tracking layer...");
    }

    public synchronized void pushStateFrame(TopographyPayload frame, boolean[][] processedMatrix, String systemLog) {
        this.liveFrame = frame;
        this.refactoredMatrixField = processedMatrix;
        this.diagnosticTraceLogs.add(systemLog);
        
        if (this.diagnosticTraceLogs.size() > 14) {
            this.diagnosticTraceLogs.remove(0); // Restrict memory log tracking buffers
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

        // 1. Tech Background Spatial Grid Mesh backdrop lines
        g2d.setColor(new Color(25, 40, 60, 60));
        for (int x = 0; x < w; x += 40) g2d.drawLine(x, 0, x, h);
        for (int y = 0; y < h; y += 40) g2d.drawLine(0, y, w, y);

        if (liveFrame == null || refactoredMatrixField == null) return;

        boolean conflictDetected = liveFrame.getConflictCoefficient() > 0.50;
        Color processingStateColor = conflictDetected ? new Color(180, 75, 255) : new Color(0, 245, 140);

        // 2. Render Left Column: High-Density Binary Telemetry Array
        int mx = 50;
        int my = 80;
        int cellSize = 45;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2d.setColor(new Color(0, 210, 255));
        g2d.drawString("=== SURFICIAL TRACE TOPOGRAPHY GRID ===", mx, my - 30);

        g2d.setFont(new Font("Monospaced", Font.BOLD, 16));
        for (int r = 0; r < refactoredMatrixField.length; r++) {
            for (int c = 0; c < refactoredMatrixField[r].length; c++) {
                boolean bitState = refactoredMatrixField[r][c];
                int cx = mx + (c * cellSize);
                int cy = my + (r * cellSize);

                if (bitState) {
                    g2d.setColor(processingStateColor);
                    g2d.fillRect(cx, cy, cellSize - 4, cellSize - 4);
                    g2d.setColor(Color.BLACK);
                    g2d.drawString("1", cx + 18, cy + 28);
                } else {
                    g2d.setColor(new Color(18, 26, 38));
                    g2d.fillRect(cx, cy, cellSize - 4, cellSize - 4);
                    g2d.setColor(Color.DARK_GRAY);
                    g2d.drawString("0", cx + 18, cy + 28);
                }
                g2d.setColor(new Color(45, 65, 90));
                g2d.drawRect(cx, cy, cellSize - 4, cellSize - 4);
            }
        }

        // 3. Render Right Column: Conflict Coefficient Analytics
        int analyticsX = mx + (refactoredMatrixField.length * cellSize) + 60;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2d.setColor(new Color(0, 210, 255));
        g2d.drawString("=== REAL-TIME ASSESSMENT SCALES ===", analyticsX, my - 30);

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.setColor(Color.LIGHT_GRAY);
        g2d.drawString(String.format("INGRESS FRAME TRANSACTION TOKEN ID: #%s", liveFrame.getTransactionId().toString().substring(0, 13).toUpperCase()), analyticsX, my + 10);
        g2d.drawString(String.format("PROPOSED DATA NODE ORIGIN CONTEXT : %s", liveFrame.getOriginIdentifier()), analyticsX, my + 35);
        
        // Render visual structural friction progress meter gauge bar
        g2d.drawString("CALCULATED COEFFICIENT OF SYSTEMIC FRICTION:", analyticsX, my + 70);
        g2d.setColor(new Color(20, 30, 48));
        g2d.fillRect(analyticsX, my + 85, 300, 18);
        g2d.setColor(processingStateColor);
        int barFillWidth = (int) (liveFrame.getConflictCoefficient() * 300);
        g2d.fillRect(analyticsX, my + 85, Math.min(300, barFillWidth), 18);
        g2d.setColor(Color.WHITE);
        g2d.drawString(String.format("%.1f%%", liveFrame.getConflictCoefficient() * 100), analyticsX + 312, my + 99);

        // 4. Trace Log Distribution Stream Output Terminal view area
        int logY = my + 155;
        g2d.setFont(new Font("Monospaced", Font.BOLD, 13));
        g2d.setColor(new Color(0, 255, 140));
        g2d.drawString("INVARIANT ASSESSMENT SYSTEM TRACE REGISTERS:", analyticsX, logY);

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        synchronized (this) {
            int currentDrawingY = logY + 24;
            for (String logLine : diagnosticTraceLogs) {
                g2d.setColor(logLine.contains("REFACTORED") || logLine.contains("CONFLICT") ? new Color(175, 80, 255) : Color.LIGHT_GRAY);
                g2d.drawString(">> " + logLine, analyticsX, currentDrawingY);
                currentDrawingY += 16;
            }
        }

        // 5. Invariant Substrate Ground Verification Info footer strip
        g2d.setColor(Color.GRAY);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        g2d.drawString("CARRIER WAVE REGULATOR FREQUENCY: 7.83 HZ LOCK ACTIVE // LOGIC BOUNDARY: VERIFIED (1=1)", 50, h - 35);
    }
}
