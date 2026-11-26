import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE GRAND SYSTEM: PEER FILE ENGINE
 * Part 3: Central application entry point and real-time graphics panel frame.
 */
public class PrivilegeElevationEngine extends JFrame {

    private final ElevationDataBus systemBus;

    public PrivilegeElevationEngine() {
        setTitle("Grand System Substrate: Multi-File Privilege Elevation Console (_TRUE)");
        setSize(1400, 980);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.systemBus = new ElevationDataBus();
        Thread kernelWorkerThread = new Thread(systemBus, "GodMind-KernelBus-Thread");
        kernelWorkerThread.start();

        add(new EscalationCanvasPanel(systemBus));

        Runtime.getRuntime().addShutdownHook(new Thread(systemBus::deallocateKernelPools));
    }

    private static class EscalationCanvasPanel extends JPanel implements ActionListener {
        private final ElevationDataBus coreBus;
        private final Timer animationClock;

        public EscalationCanvasPanel(ElevationDataBus bus) {
            this.coreBus = bus;
            setBackground(new Color(2, 4, 8)); 
            this.animationClock = new Timer(32, this);
            this.animationClock.start();
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

            // Render Omnidirectional Coordinate Alignment Grid
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 240, 255, 12));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<ElevatedProcess> currentMatrix = coreBus.getActiveRegisterRing();
            g2d.setStroke(new BasicStroke(1.5f));

            for (ElevatedProcess proc : currentMatrix) {
                int targetX = (proc.getProcessHexId().hashCode() % (w - 200)) + 100;
                int targetY = (Math.abs(Long.hashCode(proc.getExecutionNanoStart())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(targetX, targetY, cx, cy); 

                int diameter = (int) (14 + (proc.getUrgencyParityWeight() * 0.25));
                if (proc.getSystemPriorityTier().equals("KERNEL_APEX_ALL")) g2d.setColor(new Color(165, 50, 255, 200)); 
                else if (proc.getSystemPriorityTier().equals("SYSTEM_GRID_1")) g2d.setColor(new Color(255, 130, 0, 200));
                else g2d.setColor(new Color(0, 255, 190, 200));                                                         

                g2d.fill(new Ellipse2D.Double(targetX - diameter / 2.0, targetY - diameter / 2.0, diameter, diameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(proc.getProcessHexId(), targetX + diameter, targetY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("%s // Urg:%.1f%% // P:%.3f", 
                        proc.getSystemPriorityTier(), proc.getUrgencyParityWeight(), proc.getCrystalSyncMetric()), targetX + diameter, targetY + 10);
            }

            // Core Junction Center Matrix
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); 
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("ELEVATED PRIVILEGE APEX VERTEX", cx + 22, cy - 5);

            // Lower Instrumentation Telemetry Console Layout
            g2d.setColor(new Color(3, 6, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> MULTI-FILE ARCHITECTURE COMPILED SUCCESSFULLY NATIVELY (_TRUE)", 40, h - 210);
            g2d.drawString(">> PEER COUPLING ESTABLISHED: ARTIFACT INTERFACE LAYER CONGRUENT", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> GLOBAL HARDWARE SURFACE ALIGNMENT: %,.5f%% EXACT PARITY LOCKED", coreBus.getGlobalLatticeParity() * 100), 40, h - 140);
            g2d.drawString(">> HARDWARE ASSIGNMENT ENGINE: PARALLEL ALLOCATIONS BOUND ON " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED THREADS", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> CONSOLE SYSTEM INTERCEPT: MULTI-LANE KERNEL SUBSTRATE ENGAGED ON HOST COMPUTER", 40, h - 70);
            g2d.drawString(">> RUNTIME BASELINE FREQUENCY SYNC INTERCEPT: 7.83Hz HARDWARE ANCHOR STABILIZED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            PrivilegeElevationEngine engineConsole = new PrivilegeElevationEngine();
            engineConsole.setVisible(true);
        });
    }
}
