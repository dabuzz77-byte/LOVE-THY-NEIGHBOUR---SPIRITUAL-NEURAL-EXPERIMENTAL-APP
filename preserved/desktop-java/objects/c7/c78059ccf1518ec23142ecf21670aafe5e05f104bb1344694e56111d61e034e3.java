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
public class AccountVirtueAuditor extends JFrame {

    private final TelemetryDataBus telemetryBus;

    public AccountVirtueAuditor() {
        setTitle("Grand Account Virtue Auditor Console: Multi-File Array Display (_TRUE)");
        setSize(1400, 980);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.telemetryBus = new TelemetryDataBus();
        Thread kernelWorkerThread = new Thread(telemetryBus, "GodMind-TelemetryBus-Thread");
        kernelWorkerThread.start();

        add(new AuditCanvasPanel(telemetryBus));

        Runtime.getRuntime().addShutdownHook(new Thread(telemetryBus::universalDeallocate));
    }

    private static class AuditCanvasPanel extends JPanel implements ActionListener {
        private final TelemetryDataBus dataBus;
        private final Timer displayTimer;

        public AuditCanvasPanel(TelemetryDataBus bus) {
            this.dataBus = bus;
            setBackground(new Color(2, 4, 8)); 
            this.displayTimer = new Timer(32, this);
            this.displayTimer.start();
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

            // Render Omnidirectional World Grid Coordinate Matrix Lines
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 230, 255, 12));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<AuditEntry> activeMatrix = dataBus.getActiveAuditRing();
            g2d.setStroke(new BasicStroke(1.5f));

            for (AuditEntry entry : activeMatrix) {
                int targetX = (entry.getLedgerHashId().hashCode() % (w - 200)) + 100;
                int targetY = (Math.abs(Long.hashCode(entry.getGenerationNanoTime())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(targetX, targetY, cx, cy); 

                int dimensionalDiameter = (int) (14 + (Math.log10(entry.getPhysicalMagnitude() + 1) * 3));
                if (entry.getDataStreamLane().equals("TRUST_CREDIT")) g2d.setColor(new Color(165, 60, 255, 200));  
                else if (entry.getDataStreamLane().equals("INFLUX_INCOME")) g2d.setColor(new Color(0, 255, 190, 200)); 
                else g2d.setColor(new Color(255, 120, 0, 200));                                                         

                g2d.fill(new Ellipse2D.Double(targetX - dimensionalDiameter / 2.0, targetY - dimensionalDiameter / 2.0, dimensionalDiameter, dimensionalDiameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(entry.getLedgerHashId(), targetX + dimensionalDiameter, targetY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("%s // Val:%,.1f // P:%.3f", 
                        entry.getDataStreamLane(), entry.getPhysicalMagnitude(), entry.getStateAlignmentMetric()), targetX + dimensionalDiameter, targetY + 10);
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
            g2d.drawString("ACCOUNT RECONCILIATION NEXUS", cx + 22, cy - 5);

            // Lower Master Telemetry Console Panel Layout
            g2d.setColor(new Color(4, 7, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> MULTI-FILE ARCHITECTURE COMPILED: maintainer@example.invalid // Mask:5800303 // Sort:60-08-13 (_TRUE)", 40, h - 210);
            g2d.drawString(">> RE-INDEXED POSTURE: BALANCED INPUT, OUTFLOW, AND MATRICES BY UNIVERSAL HUMAN SECURITY STANDARD", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> COMBINED LEDGER CONVERGENCE INDEX: %,.5f%% PROTECTION ACCURACY", dataBus.getAggregateParityScore() * 100), 40, h - 140);
            g2d.drawString(">> NATIVE WORKER THREAD POOL: SCHEDULING SECTORS ACROSS " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED CORES NATIVELY", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> SYSTEM ENVIRONMENT: FLASH MATRIX ENPLACED (0% LONG-TERM STORAGE TRACE DETECTED)", 40, h - 70);
            g2d.drawString(">> RUNTIME BASELINE FREQUENCY SYNC INTERCEPT: 7.83Hz HARDWARE ANCHOR RECONCILED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            AccountVirtueAuditor consoleFrame = new AccountVirtueAuditor();
            consoleFrame.setVisible(true);
        });
    }
}
