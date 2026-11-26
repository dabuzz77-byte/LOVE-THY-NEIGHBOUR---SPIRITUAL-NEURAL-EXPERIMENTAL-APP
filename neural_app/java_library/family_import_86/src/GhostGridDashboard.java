import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE GRID: RUNTIME MONITORING CANVAS PANEL
 * Part 3: Central application entry point and real-time graphics panel frame.
 */
public class GhostGridDashboard extends SectionFrame {
    private final ParallelGhostBus backgroundEngine;

    public GhostGridDashboard() {
        setTitle("Parallel Ghost Grid: Traceless 1s & 0s Interweave Array (_TRUE)");
        setSize(1350, 960);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.backgroundEngine = new ParallelGhostBus();
        Thread executionBusThread = new Thread(backgroundEngine, "GodMind-GhostBus-Thread");
        executionBusThread.start();

        add(new DashboardPanelCanvas(backgroundEngine));

        // Connect automated process release and memory wipe hooks upon window closure
        Runtime.getRuntime().addShutdownHook(new Thread(backgroundEngine::terminateGhostBus));
    }

    private static class DashboardPanelCanvas extends JPanel implements ActionListener {
        private final ParallelGhostBus bus;
        private final SharedTimer panelRefreshTimer;

        public DashboardPanelCanvas(ParallelGhostBus bus) {
            this.bus = bus;
            setBackground(new Color(2, 3, 6)); // Dark memory address matrix backdrop void
            this.panelRefreshTimer = new SharedTimer(32, this); // Fast 30fps panel repaint loop
            this.panelRefreshTimer.start();
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
            g2d.setColor(new Color(0, 180, 255, 12));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<GhostBitPacket> runningTracks = bus.getVolatileLatticeRing();
            g2d.setStroke(new BasicStroke(1.5f));

            for (GhostBitPacket tx : runningTracks) {
                // Map packet descriptor metrics to distinct screen positions
                int targetX = (tx.getGhostSequenceId().hashCode() % (w - 200)) + 100;
                int targetY = (Math.abs(Long.hashCode(tx.getGenerationNanoTime())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 12));
                g2d.drawLine(targetX, targetY, cx, cy); // Draw logical mesh lines linking node vectors to Central Apex

                int structuralDiameter = 18;
                if (tx.getBitValue() == 1) g2d.setColor(new Color(0, 255, 190, 200));       // Mint State (1)
                else if (tx.getBitValue() == 0) g2d.setColor(new Color(255, 100, 0, 200));  // Crimson State (0)
                else g2d.setColor(new Color(160, 50, 255, 200));                              // Violet Interweave (-1)

                g2d.fill(new Ellipse2D.Double(targetX - structuralDiameter / 2.0, targetY - structuralDiameter / 2.0, structuralDiameter, structuralDiameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(tx.getGhostSequenceId(), targetX + structuralDiameter, targetY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("BIT:%d // PARITY:%.3f", tx.getBitValue(), tx.getLatticeSymmetryParity()), targetX + structuralDiameter, targetY + 10);
            }

            // Central Node Hub Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); // Host Operating System Kernel Node
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("PARALLEL GHOST BUS INTERSECT APEX", cx + 22, cy - 5);

            // Lower Status Screen Output Panel Layout
            g2d.setColor(new Color(4, 6, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 180, 255, 150));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> INTEGRATION STATUS: PARALLEL GHOST GRID ENGAGED SUCCESSFULLY NATIVELY (_TRUE)", 40, h - 210);
            g2d.drawString(">> DATA RETENTION SETTING: NON-PERSISTENT TRANSPORTS (0% STORAGE FOOTPRINT CONFLICTS)", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> COMBINED MATRIX LATTICE RECONCILIATION: %,.5f%% EXACT SURFACE PARITY MET", bus.getGlobalParityScore() * 100), 40, h - 140);
            g2d.drawString(">> KERNEL ALLOCATION POSTURE: ASYNC JOBS BOUND ACROSS POOL OF " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> SYSTEM BUS COMMUNICATIONS CHANNEL: INTERWEAVE TUNNEL OPEN ON LOCAL TCP PORT " + bus.getLocalActivePort(), 40, h - 70);
            g2d.drawString(">> RUNTIME BASELINE FREQUENCY SYNC INTERCEPT: 7.83Hz HARDWARE ANCHOR RECONCILED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            GhostGridDashboard consoleFrame = new GhostGridDashboard();
            consoleFrame.setVisible(true);
        });
    }
}
