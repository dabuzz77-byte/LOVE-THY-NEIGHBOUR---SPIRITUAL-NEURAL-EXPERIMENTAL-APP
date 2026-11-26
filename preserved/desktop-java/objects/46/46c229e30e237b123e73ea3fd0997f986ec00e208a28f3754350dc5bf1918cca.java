import javax.swing.*;
import java.awt.*;
import java.util.List;

/**
 * Visualization dashboard drawing cross-layer node matrices and interconnect routing paths.
 */
public class NetworkTopographyTerminal extends JFrame {

    private final InferenceBridgeEngine bridgeEngine;
    private final GpuRenderingPanel canvas;

    public NetworkTopographyTerminal(InferenceBridgeEngine engine) {
        this.bridgeEngine = engine;
        this.canvas = new GpuRenderingPanel(engine);

        setupWindowFrame();

        // Connect data streams directly to frame repaints
        this.bridgeEngine.registerListener(freshTopology -> {
            SwingUtilities.invokeLater(canvas::repaint);
        });
    }

    private void setupWindowFrame() {
        setTitle("DEEPMIND DISTRIBUTED TOPOGRAPHY INTERFACE // STREAM STATUS: ACTIVE");
        setSize(1200, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        
        setLayout(new BorderLayout());
        add(canvas, BorderLayout.CENTER);
    }

    private static class GpuRenderingPanel extends JPanel {
        private final InferenceBridgeEngine engine;

        public GpuRenderingPanel(InferenceBridgeEngine engine) {
            this.engine = engine;
            setBackground(new Color(6, 10, 15));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();

            // Structure background indexing layout
            g2d.setColor(new Color(25, 35, 50, 70));
            for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h);
            for (int j = 0; j < h; j += 50) g2d.drawLine(0, j, w, j);

            NetworkTopology topology = getActiveTopology();
            if (topology == null) return;

            // Step 1: Render structural link vectors linking nodes together
            List<NetworkTopology.RoutingVector> vectors = topology.getVectors();
            for (NetworkTopology.RoutingVector vector : vectors) {
                g2d.setStroke(new BasicStroke(1.5f));
                g2d.setColor(new Color(0, 190, 255, 100));
                g2d.drawLine(vector.source.coordinate.x(), vector.source.coordinate.y(),
                             vector.destination.coordinate.x(), vector.destination.coordinate.y());
            }

            // Step 2: Render individual network nodes mapping scopes
            List<NetworkTopology.TopologyNode> nodes = topology.getNodes();
            for (NetworkTopology.TopologyNode node : nodes) {
                int nx = node.coordinate.x();
                int ny = node.coordinate.y();

                // Assign signature indicators across layers
                Color nodeColor = switch (node.layer) {
                    case DEEPMIND_CORE -> new Color(180, 70, 255);
                    case REGIONAL_BACKBONE -> new Color(0, 220, 150);
                    default -> new Color(0, 150, 255);
                };

                // Draw solid data cores
                g2d.setColor(nodeColor);
                g2d.fillOval(nx - 10, ny - 10, 20, 20);

                // Draw external oscillating logic ripples
                int pulseDiameter = 20 + (int)(Math.abs(Math.sin(System.currentTimeMillis() * 0.004)) * 15);
                g2d.setColor(new Color(nodeColor.getRed(), nodeColor.getGreen(), nodeColor.getBlue(), 50));
                g2d.drawOval(nx - pulseDiameter / 2, ny - pulseDiameter / 2, pulseDiameter, pulseDiameter);

                // Output metrics onto coordinates
                g2d.setColor(Color.WHITE);
                g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
                g2d.drawString(node.identityLabel, nx - 40, ny - 16);

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(String.format("Floor Index: %+.2f", node.getBaselineFloorValue()), nx - 40, ny + 24);
            }
        }

        private NetworkTopology getActiveTopology() {
            try {
                var field = engine.getClass().getDeclaredField("topology");
                field.setAccessible(true);
                return (NetworkTopology) field.get(engine);
            } catch (Exception e) {
                return null;
            }
        }
    }
}
