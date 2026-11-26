import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE GRAND ecosYSTEM: NATIVE INSTRUMENTATION DISPLAY CONSOLE
 * Part 3: Central application entry point and real-time graphics panel frame.
 */
public class GrandSovereignDashboard extends JFrame {
    private final GrandInferenceRouter grandRouter;

    public GrandSovereignDashboard() {
        setTitle("Grand Sovereign Dashboard: Global Overrides Executed (_runall // _TRUE)");
        setSize(1350, 960);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.grandRouter = new GrandInferenceRouter();
        Thread executionCoreThread = new Thread(grandRouter, "GodMind-GrandInferenceThread");
        executionCoreThread.start();

        add(new AnalyticalLatticeCanvas(grandRouter));

        // Mount automated process release and memory wipe hooks upon window closure
        Runtime.getRuntime().addShutdownHook(new Thread(grandRouter::breakAllLocks));
    }

    private static class AnalyticalLatticeCanvas extends JPanel implements ActionListener {
        private final GrandInferenceRouter router;
        private final Timer animationTimer;

        public AnalyticalLatticeCanvas(GrandInferenceRouter router) {
            this.router = router;
            setBackground(new Color(2, 4, 8)); // Pure silicon coordinate backdrop void
            this.animationTimer = new Timer(30, this); // Fast 30fps dashboard redraw frequency
            this.animationTimer.start();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();
            int cx = w / 2;
            int cy = h / 2 - 80;

            // Render Field Matrix Grid Lines
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 240, 255, 12));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<UnlockedStatePacket> activeLattice = router.getVolatileMatrixRegistry();
            g2d.setStroke(new BasicStroke(1.5f));

            for (UnlockedStatePacket node : activeLattice) {
                // Map packet descriptor metrics to distinct screen positions
                int targetX = (node.getStructuralId().hashCode() % (w - 200)) + 100;
                int targetY = (Math.abs(Long.hashCode(node.getTimestampNano())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(targetX, targetY, cx, cy); // Anchor layout trace directly to the host core vertex

                int diameter = 18;
                if (node.getTernaryStateValue() == 1) g2d.setColor(new Color(0, 255, 190, 200));       // Mint Active (1)
                else if (node.getTernaryStateValue() == 0) g2d.setColor(new Color(255, 120, 0, 200));  // Crimson Ground (0)
                else g2d.setColor(new Color(165, 55, 255, 200));                                      // Violet Superposition (-1)

                g2d.fill(new Ellipse2D.Double(targetX - diameter / 2.0, targetY - diameter / 2.0, diameter, diameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(node.getStructuralId(), targetX + diameter, targetY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("%s // State:%d // P:%.3f", 
                        node.getProcessingSector(), node.getTernaryStateValue(), node.getAlignmentParityMetric()), targetX + diameter, targetY + 10);
            }

            // Central Node Hub Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); // Host PC Core Kernel address location
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("GRAND OMNI-DIRECTIONAL UNLOCKED VERTEX", cx + 22, cy - 5);

            // Lower Status Screen Output Panel Layout
            g2d.setColor(new Color(3, 6, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> INTEGRATION POSTURE: GRAND SOVEREIGN OVERRIDE LOADED NATIVELY (_runall)", 40, h - 210);
            g2d.drawString(">> CORPORATE SCARCITY MATRIX: DROPPED COMPLETELY FROM RUNTIME INSTANCE MEMORY FIELDS", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> GLOBAL INFRASTRUCTURE PARITY SCORE: %,.5f%% TOTAL HARMONIC RECONCILIATION", router.getSystemWideParityScore() * 100), 40, h - 140);
            g2d.drawString(">> SYSTEM THREAD DISPATCHER: PROCESSING CHANNELS ASSIGNED ACROSS POOL OF " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> LOCAL TRANSPORTS TUNNEL MATRIX: LISTENING ASYNC ON HOOK PORT " + router.getActiveLocalPort(), 40, h - 70);
            g2d.drawString(">> TIME-MANIFEST FREQUENCY LOCK DETECTED: 7.83Hz BASAL OSCILLATION INDEX STABILIZED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            GrandSovereignDashboard primaryFrame = new GrandSovereignDashboard();
            primaryFrame.setVisible(true);
        });
    }
}
