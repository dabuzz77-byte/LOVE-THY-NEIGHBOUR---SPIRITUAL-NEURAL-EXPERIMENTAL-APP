package net.activeinference.beacon.core;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.Random;

public class FluxGridPanel extends JPanel {
    private final int rows = 12;
    private final int cols = 12;
    private final int[][] cellMatrix = new int[rows][cols];
    private final Random rand = new Random();

    public FluxGridPanel() {
        setBackground(DashboardTheme.BG_CONTAINER);
    }

    public void updateFluxPattern() {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                cellMatrix[r][c] = rand.nextBoolean() ? 1 : 0;
            }
        }
        repaint();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int w = getWidth() / cols;
        int h = getHeight() / rows;
        g.setFont(DashboardTheme.MONO_SM);
        
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                int val = cellMatrix[r][c];
                g.setColor(val == 1 ? DashboardTheme.GRID_HEX_1 : DashboardTheme.GRID_HEX_0);
                g.drawString(String.valueOf(val), c * w + (w/3), r * h + (h/2 + 4));
            }
        }
    }
}
