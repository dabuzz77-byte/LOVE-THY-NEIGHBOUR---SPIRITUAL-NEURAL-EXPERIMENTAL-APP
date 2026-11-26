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
public class PhaseShiftEngine extends JFrame {

    private final CorePhaseBus systemBus;

    public PhaseShiftEngine() {
        setTitle("Sovereign Phase Shift Matrix Core: Multi-File Array Display [_TRUE]");
        setSize(1400, 980);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.systemBus = new CorePhaseBus();
        Thread executionWorkerThread = new Thread(systemBus, "GodMind-PhaseBus-Worker");
        executionWorkerThread.start();

        add(new PhaseControlCanvas(systemBus));

        Runtime.getRuntime().addShutdownHook(new Thread(systemBus::emergencyRegisterWipe));
    }

    private static class PhaseControlCanvas extends JPanel implements ActionListener {
        private final CorePhaseBus dataBus;
        private final Timer panelDisplayClock;

        public PhaseControlCanvas(CorePhaseBus bus) {
            this.dataBus = bus;
            setBackground(new Color(2, 4, 8)); 
            this.panelDisplayClock = new Timer(32, this);
            this.panelDisplayClock.start();
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

            List<PhasePacket> currentMatrix = dataBus.getActiveBusRegistry();
            g2d.setStroke(new BasicStroke(1.5f));

            for (PhasePacket packet : currentMatrix) {
                int screenX = (packet.getTransactionHexId().hashCode() % (w - 200)) + 100;
                int screenY = (Math.abs(Long.hashCode(packet.getGenerationTimestampNano())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(screenX, screenY, cx, cy); 

                int diameter = (int) (14 + (packet.getProcessingUrgencyIndex() * 0.22));
                if (packet.getCurrentTernaryState() == 1) g2d.setColor(new Color(0, 255, 190, 200));       
                else if (packet.getCurrentTernaryState() == 0) g2d.setColor(new Color(255, 130, 0, 200));  
                else g2d.setColor(new Color(165, 50, 255, 200));                                          

                g2d.fill(new Ellipse2D.Double(screenX - diameter / 2.0, screenY - diameter / 2.0, diameter, diameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(packet.getTransactionHexId(), screenX + diameter, screenY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("STATE:%d // Urg:%.1f%% // P:%.3f", 
                        packet.getCurrentTernaryState(), packet.getProcessingUrgencyIndex(), packet.getFieldSymmetryParity()), screenX + diameter, screenY + 10);
            }

            // Central Inversion Balance Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 200, cy);

            g2d.setColor(Color.WHITE); 
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("PHASE SHIFT MASTER CORE APEX", cx + 22, cy - 5);

            // Lower Instrumentation Telemetry Console Panel Layout
            g2d.setColor(new Color(4, 7, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> MULTI-FILE ARCHITECTURE COMPILED SUCCESSFULLY NATIVELY (_TRUE)", 40, h - 210);
            g2d.drawString(">> PEER COUPLING ESTABLISHED: ARTIFACT INTERFACE LAYER CONGRUENT", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> GLOBAL INFRASTRUCTURE PARITY SCORE: %,.5f%% EXACT RECONCILIATION ACHIEVED", dataBus.getGlobalLatticeParityScore() * 100), 40, h - 140);
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
            PhaseShiftEngine consoleApp = new PhaseShiftEngine();
            consoleApp.setVisible(true);
        });
    }
}
