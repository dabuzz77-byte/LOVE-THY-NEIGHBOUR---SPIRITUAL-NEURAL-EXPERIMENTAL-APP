import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE SUBSTRATE: ADMINISTRATIVE INSTRUMENTATION FRAME
 * Part 3: Main desktop frame and real-time graphics panel frame loop.
 */
public class GrandSkeletonKeyApp extends JFrame {
    private final QuantumInterweaveBus interweaveBus;

    public GrandSkeletonKeyApp() {
        setTitle("Grand Sovereign Matrix: Quantum-Ternary Traceless Skeleton Key App Array (_TRUE)");
        setSize(1400, 980);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.interweaveBus = new QuantumInterweaveBus();
        Thread systemExecutionThread = new Thread(interweaveBus, "GodMind-SkeletonBus-Worker");
        systemExecutionThread.start();

        add(new GraphicalLatticeCanvas(interweaveBus));

        // Connect automated process release and memory wipe hooks upon window closure
        Runtime.getRuntime().addShutdownHook(new Thread(interweaveBus::wipeSkeletonSubstrate));
    }

    private static class GraphicalLatticeCanvas extends JPanel implements ActionListener {
        private final QuantumInterweaveBus bus;
        private final Timer displayRefreshClock;

        public GraphicalLatticeCanvas(QuantumInterweaveBus bus) {
            this.bus = bus;
            setBackground(new Color(2, 4, 10)); // Total system matrix void space
            this.displayRefreshClock = new Timer(32, this); // Fast 30fps panel repaint loop
            this.displayRefreshClock.start();
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

            List<SkeletonStateVector> currentMatrix = bus.getVolatileRegisterLattice();
            g2d.setStroke(new BasicStroke(1.5f));

            for (SkeletonStateVector node : currentMatrix) {
                // Map packet descriptor metrics to distinct screen positions
                int targetX = (node.getSkeletonTokenId().hashCode() % (w - 200)) + 100;
                int targetY = (Math.abs(Long.hashCode(node.getExecutionNanoStart())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(targetX, targetY, cx, cy); // Anchor layout trace directly to the host core vertex

                int diameter = 18;
                if (node.getBitStateVector() == 1) g2d.setColor(new Color(0, 255, 190, 200));       // Mint Active (1)
                else if (node.getBitStateVector() == 0) g2d.setColor(new Color(255, 120, 0, 200));  // Crimson Ground (0)
                else g2d.setColor(new Color(165, 55, 255, 200));                                      // Violet Superposition (-1)

                g2d.fill(new Ellipse2D.Double(targetX - diameter / 2.0, targetY - diameter / 2.0, diameter, diameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(node.getSkeletonTokenId(), targetX + diameter, targetY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("%s // State:%d // P:%.3f", 
                        node.getTargetLayerSector(), node.getBitStateVector(), node.getManifestParityIndex()), targetX + diameter, targetY + 10);
            }

            // Central Inversion Balance Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); // Host PC Core Kernel address location
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("GRAND UNIFIED SKELETON APEX NEXUS", cx + 22, cy - 5);

            // Lower Master Console Telemetry Panel Layout
            g2d.setColor(new Color(3, 6, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> SYSTEM STATUS: QUANTUM-TERNARY-TRACELESS SKELETON MOLD ENPLACED (_TRUE)", 40, h - 210);
            g2d.drawString(">> DATA RETENTION SETTING: NON-PERSISTENT TRANSPORTS (0% PHYSICAL STORAGE WEAR)", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> CRITICAL HARMONIC RECONCILIATION COEF: %,.5f%% OMNI PARITY ALIGNED", bus.getSystemWideParityScore() * 100), 40, h - 140);
            g2d.drawString(">> PLATFORM RESOURCE POSTURE: ASYNC EXECUTION TRACKED ON POOL OF " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> CONSOLE NETWORK INTERCEPT: LOCAL COMMUNICATION HOOK LISTENING ASYNC ON PORT " + bus.getActiveLocalPort(), 40, h - 70);
            g2d.drawString(">> SYSTEM TUNING CONSTANT BASELINE CLOCK: 7.83Hz BASAL OSCILLATION CONSTANT LOCKED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            GrandSkeletonKeyApp consoleFrame = new GrandSkeletonKeyApp();
            consoleFrame.setVisible(true);
        });
    }
}
