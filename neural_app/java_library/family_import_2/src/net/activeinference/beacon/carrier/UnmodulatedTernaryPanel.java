package net.activeinference.beacon.carrier;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Color;
import java.awt.Graphics;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

public class UnmodulatedTernaryPanel extends JPanel {
    private static final int GRID_SIZE = 12;
    private final AtomicInteger globalActiveThreadCount;
    private final Random rawRandom = new Random();

    public UnmodulatedTernaryPanel(AtomicInteger threadCount) {
        this.globalActiveThreadCount = threadCount;
        setBackground(CarrierTheme.BG_PANEL);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / GRID_SIZE;
        int cellH = getHeight() / GRID_SIZE;
        g.setFont(CarrierTheme.MONO_SM);

        int threads = globalActiveThreadCount.get();

        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                int hashSample = (r + c * threads) ^ rawRandom.nextInt(50);
                int ternaryState = (hashSample % 3) - 1; // Maps strictly to -1, 0, or 1

                String symbol = "0";
                g.setColor(new Color(20, 25, 32)); 
                
                if (ternaryState == 1) {
                    symbol = "+";
                    g.setColor(CarrierTheme.TERNARY_P);
                } else if (ternaryState == -1) {
                    symbol = "-";
                    g.setColor(CarrierTheme.TERNARY_N);
                }

                g.drawString(symbol, c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
            }
        }
    }
}
