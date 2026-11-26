package net.activeinference.beacon.system;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Color;
import java.awt.Graphics;
import java.util.concurrent.atomic.AtomicInteger;

public class SystemTernaryPanel extends JPanel {
    private static final int GRID_SIZE = 12;
    private final AtomicInteger globalActiveThreadCount;
    private double waveTimeDelta = 0.0;

    public SystemTernaryPanel(AtomicInteger threadCount) {
        this.globalActiveThreadCount = threadCount;
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

        double threadModifier = globalActiveThreadCount.get() * 0.02;

        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                double offsetPhase = Math.sin(waveTimeDelta + (r * 0.25) * Math.cos(c * (0.15 + threadModifier)));
                
                String symbol = "0";
                g.setColor(new Color(25, 32, 42)); 
                
                if (offsetPhase > 0.35) {
                    symbol = "+";
                    g.setColor(DashboardTheme.TERNARY_P);
                } else if (offsetPhase < -0.35) {
                    symbol = "-";
                    g.setColor(DashboardTheme.TERNARY_N);
                }

                g.drawString(symbol, c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
            }
        }
    }
}
