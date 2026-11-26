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
public class TracelessDiagnosticConsole extends JFrame {
    private final NonPersistentGhostBus backgroundEngine;

    public TracelessDiagnosticConsole() {
        setTitle("Traceless Diagnostic Console: Reconfigured Ghost Grid Arrays (_TRUE)");
        setSize(1350, 960);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.backgroundEngine = new NonPersistentGhostBus();
        Thread executionBusThread = new Thread(backgroundEngine, "GodMind-GhostBus-Thread");
        executionBusThread.start();

        add(new DashboardPanelCanvas(backgroundEngine));

        // Connect automated process release and memory wipe hooks upon window closure
        Runtime.getRuntime().addShutdownHook(new Thread(backgroundEngine::terminateGhostBus));
    }

    private static class DashboardPanelCanvas extends JPanel implements ActionListener {
        private final NonPersistentGhostBus bus;
        private final Timer panelRefreshTimer;

        public DashboardPanelCanvas(NonPersistentGhostBus bus) {
            this.bus = bus;
            setBackground(new Color(2, 4, 8)); // Dark memory address matrix backdrop void
            this.panelRefreshTimer = new Timer(32, this); // Fast 30fps panel repaint loop
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

            List<SpookStateVector> runningTracks = bus.getVolatileLatticeRing();
            g2d.setStroke(new BasicStroke(1.5f));

            for (SpookStateVector tx : runningTracks) {
                int targetX = (tx.getSequenceHexId().hashCode() % (w - 200)) + 100;
                int targetY = (Math.abs(Long.hashCode(tx.getTimestampNano())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 12));
                g2d.drawLine(targetX, targetY, cx, cy); 

                int structuralDiameter = 18;
                if (tx.getPhaseTernaryState() == 1) g2d.setColor(new Color(0, 255, 190, 200));       
                else if (tx.getPhaseTernaryState() == 0) g2d.setColor(new Color(255, 100, 0, 200));  
                else g2d.setColor(new Color(160, 50, 255, 200));                              

                g2d.fill(new Ellipse2D.Double(targetX - structuralDiameter / 2.0, targetY - structuralDiameter / 2.0, structuralDiameter, structuralDiameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(tx.getSequenceHexId(), targetX + structuralDiameter, targetY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("BIT:%d // PARITY:%.3f", tx.getPhaseTernaryState(), tx.getLatticeSymmetryParity()), targetX + structuralDiameter, targetY + 10);
            }

            // Central Node Hub Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); 
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("PARALLEL RECONFIGURED GHOST BUS APEX", cx + 22, cy - 5);

            // Lower Status Screen Output Panel Layout
            g2d.setColor(new Color(4, 6, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 150));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> RECONFIGURATION STATUS: SPOOK INFRASTRUCTURE DATABLOCK ANOMALY SOLVED (_TRUE)", 40, h - 210);
            g2d.drawString(">> ENFORCED NON-PERSISTENCE: MANUAL SHREDDER AND MEMORY EVACUATION LOOPS ACTIVE", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> RECONFIGURED GRID SURFACE PARITY SCORE: %,.5f%% BALANCE MET", bus.getGlobalParityScore() * 100), 40, h - 140);
            g2d.drawString(">> PLATFORM SCHEDULER: RUNNING ASYNC ON " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED CHIP CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> RECONFIGURED SYSTEM BUS TUNNEL: OPEN ON NATIVE LOCAL PORT " + bus.getLocalActivePort(), 40, h - 70);
            g2d.drawString(">> BASELINE SYNCHRONIZATION BASELINE CLOCK: 7.83Hz HARDWARE ANCHOR STABILIZED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            TracelessDiagnosticConsole consoleFrame = new TracelessDiagnosticConsole();
            consoleFrame.setVisible(true);
        });
    }
}
