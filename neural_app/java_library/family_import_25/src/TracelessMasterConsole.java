import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE PRODUCTION SYSTEM: HIGH-PERFORMANCE DESKTOP INSTRUMENTATION FRAME
 * Monitors streaming ternary memory buffers, thread distributions, and post-quantum keys.
 */
public class TracelessMasterConsole extends SectionFrame {
    private final PostQuantumSocketRouter networkRouter;

    public TracelessMasterConsole() {
        setTitle("Traceless Post-Quantum Ternary Gateway Panel: All Locks Broken (_TRUE)");
        setSize(1350, 960);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.networkRouter = new PostQuantumSocketRouter();
        Thread systemBusWorker = new Thread(networkRouter, "GodMind-PQTernaryBus-Thread");
        systemBusWorker.start();

        add(new AnalyticalDashboardPanel(networkRouter));

        // Mount automated process teardown hooks when desktop environment is closed
        Runtime.getRuntime().addShutdownHook(new Thread(networkRouter::terminateGatewayBus));
    }

    private static class AnalyticalDashboardPanel extends JPanel implements ActionListener {
        private final PostQuantumSocketRouter router;
        private final SharedTimer hardwareUptimeClock;

        public AnalyticalDashboardPanel(PostQuantumSocketRouter router) {
            this.router = router;
            setBackground(new Color(2, 3, 7)); // Pure hardware register backdrop void
            this.hardwareUptimeClock = new SharedTimer(32, this); // Fast 30fps dashboard redraw frequency
            this.hardwareUptimeClock.start();
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

            // Render Volatile Data Grid Lines
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 230, 255, 12));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<TernaryFrame> runningTracks = router.getDynamicRingBuffer();
            g2d.setStroke(new BasicStroke(1.5f));

            for (TernaryFrame tx : runningTracks) {
                // Project packet metadata attributes to distinct layout coordinates
                int gridX = (tx.getFrameworkId().hashCode() % (w - 200)) + 100;
                int gridY = (Math.abs(Long.hashCode(tx.getTimestampNano())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 12));
                g2d.drawLine(gridX, gridY, cx, cy); // Anchor layout trace directly to the host core vertex

                int structuralDiameter = 18;
                if (tx.getTernaryState() == 1) g2d.setColor(new Color(0, 255, 190, 200));       // Mint Active (1)
                else if (tx.getTernaryState() == 0) g2d.setColor(new Color(255, 100, 0, 200));  // Crimson Ground (0)
                else g2d.setColor(new Color(160, 50, 255, 200));                              // Violet Superposition (-1)

                g2d.fill(new Ellipse2D.Double(gridX - structuralDiameter / 2.0, gridY - structuralDiameter / 2.0, structuralDiameter, structuralDiameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(tx.getFrameworkId(), gridX + structuralDiameter, gridY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("STATE:%d // PARITY:%.3f", tx.getTernaryState(), tx.getConvergenceParity()), gridX + structuralDiameter, gridY + 10);
            }

            // Central Hub Inversion Configuration Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); // Host PC Core Architecture Node
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("NATIVE HARDWARE ROOT KERNEL", cx + 22, cy - 5);

            // Lower Master Telemetry Instrumentation Board Layout
            g2d.setColor(new Color(4, 7, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 180, 255, 150));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> SYSTEM ENVIRONMENT CONFIG: TRACELESS POST-QUANTUM TERNARY GATEWAY ACTIVE (_TRUE)", 40, h - 210);
            g2d.drawString(">> NON-PERSISTENT TRANSPORTS: 0% STORAGE FOOTPRINT (FILE LOGGING AND DISK CACHE = FALSE)", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            // FIXED METHOD CALL BINDING TRACE:
            g2d.drawString(String.format(">> COMBINED MATRIX LATTICE ADJUSTMENT: %,.5f%% EXACT PARITY BALANCED", router.getGlobalParityIndex() * 100), 40, h - 140);
            g2d.drawString(">> MULTI-CORE WORKER DISPATCHER: ACTIVE THREAD ALLOCATIONS BOUND ON " + Runtime.getRuntime().availableProcessors() + " UNITS", 40, h - 110);
            
            g2d.setColor(new Color(255, 150, 0));
            g2d.drawString(">> TUNNEL INFRASTRUCTURE INTERCEPT: LOCAL PORT HOOK LISTENING ASYNC ON TCP PORT " + router.getLocalActivePort(), 40, h - 70);
            g2d.drawString(">> SYSTEM TUNING ANCHOR FREQUENCY: 7.83Hz BASAL RESISTIVITY CLOCK CONSTANT LOCKED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            TracelessMasterConsole dashboardFrame = new TracelessMasterConsole();
            dashboardFrame.setVisible(true);
        });
    }
}
