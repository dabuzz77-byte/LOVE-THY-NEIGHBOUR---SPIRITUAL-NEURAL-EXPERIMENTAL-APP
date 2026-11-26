package net.activeinference.beacon.system;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.concurrent.atomic.AtomicInteger;

public class SystemBinaryPanel extends JPanel {
    private static final int GRID_SIZE = 12;
    private final AtomicInteger activeJavaProcessCount;
    private double waveTimeDelta = 0.0;

    public SystemBinaryPanel(AtomicInteger processCount) {
        this.activeJavaProcessCount = processCount;
        setBackground(DashboardTheme.BG_PANEL);
    }

    public void setWaveTimeDelta(double timeDelta) {
        this.waveTimeDelta = timeDelta;
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / GRID_SIZE;
        int cellH = getHeight() / GRID_SIZE;
        g.setFont(DashboardTheme.MONO_SM);

        double processModifier = activeJavaProcessCount.get() * 0.15;

        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                double offsetPhase = Math.sin(waveTimeDelta + (r * (0.4 + processModifier)) + (c * 0.3));
                int binaryBit = offsetPhase >= 0.0 ? 1 : 0;

                g.setColor(binaryBit == 1 ? DashboardTheme.HEX_GREEN : DashboardTheme.HEX_MUTED);
                g.drawString(String.valueOf(binaryBit), c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
            }
        }
    }
}
