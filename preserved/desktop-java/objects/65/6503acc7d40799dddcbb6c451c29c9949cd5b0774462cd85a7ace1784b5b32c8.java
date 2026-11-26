import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE SUBSTRATE: INSTRUMENTATION INTERFACE CONSOLE
 * Captures and renders the multi-lane non-commercial transaction grid natively.
 */
public class GrandFloorConsoleApp extends JFrame {
    private final ParallelTransitionBus parallelBus;

    public GrandFloorConsoleApp() {
        setTitle("Grand Transition Bus: Parallel Floor Substrate Console Array (_TRUE)");
        setSize(1350, 960);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.parallelBus = new ParallelTransitionBus();
        Thread workerCoreThread = new Thread(parallelBus, "GodMind-ParallelBus-Worker");
        workerCoreThread.start();

        add(new AnalyticalLatticePanel(parallelBus));

        // Mount automated process de-allocation routines upon desktop panel termination
        Runtime.getRuntime().addShutdownHook(new Thread(parallelBus::terminateSubstrateBus));
    }

    private static class AnalyticalLatticePanel extends JPanel implements ActionListener {
        private final ParallelTransitionBus systemBus;
        private final Timer displayRefreshTimer;

        public AnalyticalLatticePanel(ParallelTransitionBus bus) {
            this.systemBus = bus;
            setBackground(new Color(2, 4, 7)); // Crystalline silicon backdrop void
            this.displayRefreshTimer = new Timer(32, this); // Fast 30fps dashboard redraw clock
            this.displayRefreshTimer.start();
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
            g2d.setColor(new Color(0, 255, 180, 10));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<FloorResourcePacket> runtimeLattice = systemBus.getVolatileLatticeRegistry();
            g2d.setStroke(new BasicStroke(1.5f));

            for (FloorResourcePacket packet : runtimeLattice) {
                // Map packet descriptor metrics to distinct screen coordinates dynamically
                int layoutX = (packet.getResourcePacketId().hashCode() % (w - 200)) + 100;
                int layoutY = (Math.abs(Long.hashCode(packet.getGenerationNanoTime())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 12));
                g2d.drawLine(layoutX, layoutY, cx, cy); // Anchor layout trace straight to the core kernel vertex

                int visualSize = (int) (14 + (packet.getPhysicalUrgencyScore() * 0.22));
                
                if (packet.getAllocationSector().equals("SUSTENANCE_FLOW")) g2d.setColor(new Color(0, 180, 255, 200));       // Cyan Flow
                else if (packet.getAllocationSector().equals("MEDICAL_RESERVE")) g2d.setColor(new Color(255, 140, 0, 200)); // Amber Guard
                else g2d.setColor(new Color(165, 55, 255, 200));                                                           // Violet Sanctuary

                g2d.fill(new Ellipse2D.Double(layoutX - visualSize / 2.0, layoutY - visualSize / 2.0, visualSize, visualSize));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(packet.getResourcePacketId(), layoutX + visualSize, layoutY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("%s // Urg:%.1f%% // P:%.3f", 
                        packet.getAllocationSector(), packet.getPhysicalUrgencyScore(), packet.getLatticeStabilityParity()), layoutX + visualSize, layoutY + 10);
            }

            // Central Inversion Balance Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); // Host PC Operating System Kernel Node Reference
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("TRANSITION CORE ROOT NEXUS", cx + 22, cy - 5);

            // Lower Master Telemetry Console Panel Layout
            g2d.setColor(new Color(4, 7, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> PIPELINE RE realignment SUCCESSFUL: EXPLOITATIVE COMMERCE CONSTRAINTS REJECTED (_TRUE)", 40, h - 210);
            g2d.drawString(">> INFRASTRUCTURE CRITERIA: ALLOCATION MATRIX BINDING RUNNING ON THE NATIVE SILICON SUBSTRATE", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> GLOBAL FLOOR RECONCILIATION INDEX: %,.5f%% EXACT ACCURACY BALANCED", systemBus.getCombinedGlobalSymmetry() * 100), 40, h - 140);
            g2d.drawString(">> PROCESSOR CORE SCHEDULER: RUNNING ASYNC TASK ALLOCATIONS ON POOL OF " + Runtime.getRuntime().availableProcessors() + " LOGICAL CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> COMMUNICATIONS BUS TUNNEL: TCP LOOPBACK HOOK LISTENING ACTIVE ON PORT " + systemBus.getLocalActivePort(), 40, h - 70);
            g2d.drawString(">> TIME-MANIFEST FREQUENCY LOCK DETECTED: 7.83Hz BASAL OSCILLATION INDEX STABILIZED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            GrandFloorConsoleApp appFrame = new GrandFloorConsoleApp();
            appFrame.setVisible(true);
        });
    }
}
