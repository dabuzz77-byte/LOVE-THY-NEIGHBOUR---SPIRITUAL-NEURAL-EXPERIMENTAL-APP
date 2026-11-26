package net.activeinference.beacon.generator;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

public class RawBinaryPanel extends JPanel {
    private static final int GRID_SIZE = 12;
    private final AtomicInteger activeProcessCount;
    private final Random rawRandom = new Random();

    public RawBinaryPanel(AtomicInteger processCount) {
        this.activeProcessCount = processCount;
        setBackground(GeneratorTheme.BG_PANEL);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / GRID_SIZE;
        int cellH = getHeight() / GRID_SIZE;
        g.setFont(GeneratorTheme.MONO_SM);

        int processes = activeProcessCount.get();

        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                boolean bitState = ((r * c + processes) ^ rawRandom.nextInt(100)) % 2 == 0;
                int val = bitState ? 1 : 0;

                g.setColor(val == 1 ? GeneratorTheme.HEX_GREEN : GeneratorTheme.HEX_MUTED);
                g.drawString(String.valueOf(val), c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
            }
        }
    }
}
