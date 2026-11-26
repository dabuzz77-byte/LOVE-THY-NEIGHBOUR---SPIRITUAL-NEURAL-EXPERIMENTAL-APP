import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;

public class BinaryFluxCanvas extends JPanel {
    private final int rows = 24;
    private final int cols = 48;
    private final int[][] grid = new int[rows][cols];
    private final Random random = new Random();
    private SharedTimer fluxTimer;
    private double fluxIntensity = 0.5;

    public BinaryFluxCanvas() {
        setBackground(new Color(10, 12, 16));
        setPreferredSize(new Dimension(720, 360));
        initializeGrid();

        fluxTimer = new SharedTimer(80, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                updateFluxState();
                repaint();
            }
        });
        fluxTimer.start();
    }

    private void initializeGrid() {
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                grid[i][j] = random.nextDouble() < fluxIntensity ? 1 : 0;
            }
        }
    }

    private void updateFluxState() {
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                if (random.nextDouble() < 0.25) {
                    grid[i][j] = random.nextDouble() < fluxIntensity ? 1 : 0;
                }
            }
        }
    }

    public void setFluxIntensity(double intensity) {
        this.fluxIntensity = Math.max(0.1, Math.min(1.0, intensity));
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int cellWidth = getWidth() / cols;
        int cellHeight = getHeight() / rows;

        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                if (grid[i][j] == 1) {
                    g2d.setColor(new Color(0, 255, 140, 200));
                    g2d.fillRect(j * cellWidth + 1, i * cellHeight + 1, cellWidth - 2, cellHeight - 2);
                } else {
                    g2d.setColor(new Color(25, 35, 45, 120));
                    g2d.fillRect(j * cellWidth + 1, i * cellHeight + 1, cellWidth - 2, cellHeight - 2);
                }
            }
        }

        // Overlay grid vectors
        g2d.setColor(new Color(0, 255, 200, 40));
        g2d.drawRect(0, 0, getWidth() - 1, getHeight() - 1);
    }

    public void stopFlux() {
        if (fluxTimer != null) {
            fluxTimer.stop();
        }
    }
}