package net.activeinference.beacon.core;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.Random;

public class TernaryGridPanel extends JPanel {
    private final int rows = 12;
    private final int cols = 12;
    private final int[][] cellMatrix = new int[rows][cols];
    private final Random rand = new Random();

    public TernaryGridPanel() {
        setBackground(DashboardTheme.BG_CONTAINER);
    }

    public void updateTernaryPattern() {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                int select = rand.nextInt(3); // 0, 1, 2
                cellMatrix[r][c] = select == 2 ? 1 : (select == 1 ? 0 : -1);
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
                String sym = val == 1 ? "+" : (val == 0 ? "0" : "-");
                g.setColor(val == 1 ? DashboardTheme.TERNARY_P : (val == -1 ? DashboardTheme.TERNARY_N : DashboardTheme.GRID_HEX_0));
                g.drawString(sym, c * w + (w/3), r * h + (h/2 + 4));
            }
        }
    }
}
