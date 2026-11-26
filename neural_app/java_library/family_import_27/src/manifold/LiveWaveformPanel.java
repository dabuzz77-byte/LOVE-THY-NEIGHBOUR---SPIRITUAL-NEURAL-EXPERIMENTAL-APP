package manifold;
import neural.studio.*;





import javax.swing.JPanel;

import java.awt.Color;

import java.awt.Graphics;

import java.util.ArrayList;

import java.util.List;



public class LiveWaveformPanel extends JPanel {

    private final List<Double> points = new ArrayList<>();



    public void appendWaveValue(double v) {

        points.add(v);

        if (points.size() > 100) points.remove(0);

        this.repaint();

    }



    @Override

    protected void paintComponent(Graphics g) {

        super.paintComponent(g);

        int midY = getHeight() / 2;

        g.setColor(new Color(25, 35, 45));

        g.drawLine(0, midY, getWidth(), midY);

        g.setColor(Color.CYAN);

        for (int i = 1; i < points.size(); i++) {

            int x1 = (i - 1) * (getWidth() / 100);

            int x2 = i * (getWidth() / 100);

            int y1 = midY - (int) (points.get(i - 1) * (getHeight() / 3));

            int y2 = midY - (int) (points.get(i) * (getHeight() / 3));

            g.drawLine(x1, y1, x2, y2);

        }

    }

}

