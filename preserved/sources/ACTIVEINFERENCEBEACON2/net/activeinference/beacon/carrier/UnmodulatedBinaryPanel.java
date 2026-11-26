package net.activeinference.beacon.carrier;

import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

public class UnmodulatedBinaryPanel extends JPanel {
    private static final int GRID_SIZE = 12;
    private final AtomicInteger activeJavaProcessCount;
    private final Random rawRandom = new Random();

    public UnmodulatedBinaryPanel(AtomicInteger processCount) {
        this.activeJavaProcessCount = processCount;
        setBackground(CarrierTheme.BG_PANEL);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / GRID_SIZE;
        int cellH = getHeight() / GRID_SIZE;
        g.setFont(CarrierTheme.MONO_SM);

        int processes = activeJavaProcessCount.get();

        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                // Raw bit state changes generated from internal processing parameters
                boolean bitState = ((r * c + processes) ^ rawRandom.nextInt(100)) % 2 == 0;
                int val = bitState ? 1 : 0;

                g.setColor(val == 1 ? CarrierTheme.HEX_GREEN : CarrierTheme.HEX_MUTED);
                g.drawString(String.valueOf(val), c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
            }
        }
    }
}
