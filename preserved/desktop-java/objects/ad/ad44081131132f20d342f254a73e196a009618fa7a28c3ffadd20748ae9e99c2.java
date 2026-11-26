package net.activeinference.beacon.generator;

import javax.swing.JPanel;
import java.awt.Color;
import java.awt.Graphics;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

public class RawTernaryPanel extends JPanel {
    private static final int GRID_SIZE = 12;
    private final AtomicInteger activeThreadCount;
    private final Random rawRandom = new Random();

    public RawTernaryPanel(AtomicInteger threadCount) {
        this.activeThreadCount = threadCount;
        setBackground(GeneratorTheme.BG_PANEL);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / GRID_SIZE;
        int cellH = getHeight() / GRID_SIZE;
        g.setFont(GeneratorTheme.MONO_SM);

        int threads = activeThreadCount.get();

        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                int hashSample = (r + c * threads) ^ rawRandom.nextInt(50);
                int ternaryState = (hashSample % 3) - 1;

                String symbol = "0";
                g.setColor(new Color(20, 25, 32)); 
                
                if (ternaryState == 1) {
                    symbol = "+";
                    g.setColor(GeneratorTheme.TERNARY_P);
                } else if (ternaryState == -1) {
                    symbol = "-";
                    g.setColor(GeneratorTheme.TERNARY_N);
                }

                g.drawString(symbol, c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
            }
        }
    }
}
