package engine.ui;

import java.awt.Graphics;
import java.util.ArrayList;
import java.util.List;
import javax.swing.JPanel;

public class WaveformCanvas extends JPanel {
    private final List<Double> points = new ArrayList<>();

    public WaveformCanvas() {
        this.setBackground(AestheticTheme.BG_MATRIX);
        this.setBorder(AestheticTheme.createBorder("7.83Hz PLANETARY CARRIER WAVE DATA STREAM", AestheticTheme.ACCENT_CYAN));
    }

    public void appendWaveData(double value) {
        points.add(value);
        if (points.size() > 150) points.remove(0);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int midY = getHeight() / 2;
        g.setColor(AestheticTheme.BG_PANEL);
        g.drawLine(0, midY, getWidth(), midY);

        g.setColor(AestheticTheme.ACCENT_CYAN);
        for (int i = 1; i < points.size(); i++) {
            int x1 = (i - 1) * (getWidth() / 150);
            int x2 = i * (getWidth() / 150);
            int y1 = midY - (int) (points.get(i - 1) * (getHeight() / 3));
            int y2 = midY - (int) (points.get(i) * (getHeight() / 3));
            g.drawLine(x1, y1, x2, y2);
        }
    }
}
