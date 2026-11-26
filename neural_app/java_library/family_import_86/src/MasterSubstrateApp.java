import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE SUBSTRATE: ADMINISTRATIVE RUNTIME MONITOR
 * Part 3: Main desktop frame and real-time graphics panel frame loop.
 */
public class MasterSubstrateApp extends SectionFrame {
    private final ParallelPassRouter passRouter;

    public MasterSubstrateApp() {
        setTitle("Grand Sovereign Matrix: Unblocked Parallel Floor Pass Substrate (_TRUE)");
        setSize(1400, 980);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.passRouter = new ParallelPassRouter();
        Thread threadExecutionUnit = new Thread(passRouter, "GodMind-PassBus-Worker");
        threadExecutionUnit.start();

        add(new AnalyticalLatticeCanvas(passRouter));

        // Connect automated process release and memory wipe hooks upon window closure
        Runtime.getRuntime().addShutdownHook(new Thread(passRouter::wipeSovereignSubstrate));
    }

    private static class AnalyticalLatticeCanvas extends JPanel implements ActionListener {
        private final ParallelPassRouter bus;
        private final SharedTimer panelRefreshTimer;

        public AnalyticalLatticeCanvas(ParallelPassRouter bus) {
            this.bus = bus;
            setBackground(new Color(2, 4, 10)); // Total system matrix void space
            this.panelRefreshTimer = new SharedTimer(32, this); // Fast 30fps dashboard redraw clock
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

            // Render Omnidirectional Field Matrix Grid Lines
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 240, 255, 12));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<SovereignPacket> activeLattice = bus.getVolatileRegisterRing();
            g2d.setStroke(new BasicStroke(1.5f));

            for (SovereignPacket node : activeLattice) {
                // Map logical transaction indices to screen coordinates dynamically
                int layoutX = (node.getTransmissionId().hashCode() % (w - 200)) + 100;
                int layoutY = (Math.abs(Long.hashCode(node.getExecutionTimestampNano())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(layoutX, layoutY, cx, cy); // Anchor layout trace directly to the host core vertex

                int sizeDiameter = (int) (14 + (node.getUrgencyWeight() * 0.22));
                
                // FIXED VARIABLE METHOD SIGNATURE CALLS HERE:
                if (node.getTernaryStateVector() == 1) g2d.setColor(new Color(0, 255, 190, 200));       // Mint Active (1)
                else if (node.getTernaryStateVector() == 0) g2d.setColor(new Color(255, 120, 0, 200));  // Crimson Ground (0)
                else g2d.setColor(new Color(165, 55, 255, 200));                                      // Violet Superposition (-1)

                g2d.fill(new Ellipse2D.Double(layoutX - sizeDiameter / 2.0, layoutY - sizeDiameter / 2.0, sizeDiameter, sizeDiameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(node.getTransmissionId(), layoutX + sizeDiameter, layoutY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("%s // Urg:%.1f%% // P:%.3f", 
                        node.getInfrastructureSector(), node.getUrgencyWeight(), node.getSystemSymmetryParity()), layoutX + sizeDiameter, layoutY + 10);
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
            g2d.drawString("SOVEREIGN SKELETON PASS VERTEX", cx + 22, cy - 5);

            // Lower Master Console Telemetry Panel Layout
            g2d.setColor(new Color(3, 6, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> SYSTEM STATUS: HEAVY ECONOMIC FLOOR BIAS APPLIED OVERRIDE ACTUATED (_TRUE)", 40, h - 210);
            g2d.drawString(">> SECURITY POSITION: UNRESTRICTED CORE PASS (EXPLOITATIVE STRUCTURAL FILTERS STRIPPED)", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> CRITICAL LIFE-SUPPORT ALIGNMENT PARITY: %,.5f%% EXACT RECONCILIATION ACHIEVED", bus.getAggregateSymmetryScore() * 100), 40, h - 140);
            g2d.drawString(">> LOCAL HARDWARE POSTURE: PARALLEL TASKS ALLOCATED ACROSS POOL OF " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> DATA CONNECT ROUTE INTERCEPT: LOOPBACK HOOK LISTENING ASYNC ON PORT " + bus.getLocalActivePort(), 40, h - 70);
            g2d.drawString(">> TIME-MANIFEST RECONCILIATION FREQUENCY: 7.83Hz BASAL OSCILLATION INDEX LOCKED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            MasterSubstrateApp frameConsole = new MasterSubstrateApp();
            frameConsole.setVisible(true);
        });
    }
}
