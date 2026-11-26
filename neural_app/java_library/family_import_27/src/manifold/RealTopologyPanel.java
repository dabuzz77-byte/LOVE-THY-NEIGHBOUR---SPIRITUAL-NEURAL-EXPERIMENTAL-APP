package manifold;
import neural.studio.*;





import javax.swing.JPanel;

import java.awt.Color;

import java.awt.Font;

import java.awt.Graphics;

import java.util.List;



public class RealTopologyPanel extends JPanel {

    private final List<LiveDeviceNode> devices;



    public RealTopologyPanel(List<LiveDeviceNode> devices) {

        this.devices = devices;

    }



    @Override

    protected void paintComponent(Graphics g) {

        super.paintComponent(g);

        int cx = getWidth() / 2;

        int cy = getHeight() / 2;



        g.setColor(Color.MAGENTA);

        g.fillOval(cx - 10, cy - 10, 20, 20);

        g.drawString("MY GATEWAY IP", cx - 45, cy - 15);



        synchronized (devices) {

            int size = devices.size();

            for (int i = 0; i < size; i++) {

                double slice = 2 * Math.PI / size;

                int radius = 100;

                int nx = cx + (int) (Math.cos(i * slice) * radius);

                int ny = cy + (int) (Math.sin(i * slice) * radius);



                g.setColor(Color.DARK_GRAY);

                g.drawLine(cx, cy, nx, ny);



                LiveDeviceNode dev = devices.get(i);

                g.setColor(dev.detectedRole.equals("AI_INFERENCE_ENGINE") ? Color.GREEN : Color.ORANGE);

                g.fillOval(nx - 6, ny - 6, 12, 12);

                g.setColor(Color.WHITE);

                g.setFont(new Font("Monospaced", Font.PLAIN, 11));

                g.drawString(dev.ip + " [" + dev.detectedRole + "]", nx + 10, ny + 4);

            }

        }

    }

}

