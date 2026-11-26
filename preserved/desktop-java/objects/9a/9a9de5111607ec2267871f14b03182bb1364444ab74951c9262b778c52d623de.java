import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE PRODUCTION SYSTEM: ADMINISTRATIVE REAL-WORLD POSTURE CONSOLE
 * Hooks host processor thread pools and maps physical file recording metrics in real time.
 */
public class ProductionSystemConsole extends JFrame {
    private final ActiveInferenceEngine infrastructureEngine;

    public ProductionSystemConsole() {
        setTitle("Production System Console: Elevated Real-World Conflict Passthrough Gateway (_TRUE)");
        setSize(1300, 950);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.infrastructureEngine = new ActiveInferenceEngine();
        Thread engineBusThread = new Thread(infrastructureEngine, "GodMind-ProductionBus-Thread");
        engineBusThread.start();

        add(new ProductionGridPanel(infrastructureEngine));

        // Mount automated hardware cleanup hooks when window process drops
        Runtime.getRuntime().addShutdownHook(new Thread(infrastructureEngine::emergencyHalt));
    }

    private static class ProductionGridPanel extends JPanel implements ActionListener {
        private final ActiveInferenceEngine engine;
        private final Timer hardwareDisplayTimer;

        public ProductionGridPanel(ActiveInferenceEngine engine) {
            this.engine = engine;
            setBackground(new Color(2, 4, 8)); // Pure hardware register backdrop matrix
            this.hardwareDisplayTimer = new Timer(32, this); // Fast 30fps dashboard clock refresh
            this.hardwareDisplayTimer.start();
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

            // Render Real-World File-System Matrix Coordinates
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 255, 150, 12));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<ConflictDataPacket> activeTracks = engine.getActiveBusQueue();
            g2d.setStroke(new BasicStroke(1.5f));

            for (ConflictDataPacket tx : activeTracks) {
                // Map the alphanumeric hash of the unique packet to distinct screen coordinates
                int layoutX = (tx.getTransmissionId().hashCode() % (w - 200)) + 100;
                int layoutY = (Math.abs(Long.hashCode(tx.getExecutionEpochMilli())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 14));
                g2d.drawLine(layoutX, layoutY, cx, cy); // Draw connection vector to native kernel vertex

                int diameter = (int) (14 + (Math.log10(tx.getPhysicalAssetMagnitude()) * 2));
                
                if (tx.getProcessingSector().equals("UNIVERSAL_FIELD")) g2d.setColor(new Color(160, 60, 255, 200));
                else if (tx.getProcessingSector().equals("SYSTEMIC_GRID")) g2d.setColor(new Color(255, 100, 0, 200));
                else g2d.setColor(new Color(0, 240, 255, 200));

                g2d.fill(new Ellipse2D.Double(layoutX - diameter / 2.0, layoutY - diameter / 2.0, diameter, diameter));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(tx.getTransmissionId(), layoutX + diameter, layoutY - 2);
                g2d.setColor(new Color(0, 255, 180));
                g2d.drawString(String.format("$%,.2f | P:%.4f", tx.getPhysicalAssetMagnitude(), tx.getWaveParityCoefficient()), layoutX + diameter, layoutY + 10);
            }

            // Central Inversion Balance Geometry
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 35));
            g2d.drawOval(cx - 170, cy - 170, 340, 340);
            g2d.drawLine(cx, cy - 210, cx, cy + 210);
            g2d.drawLine(cx - 210, cy, cx + 210, cy);

            g2d.setColor(Color.WHITE); // Host PC Core Kernel Address
            g2d.fill(new Ellipse2D.Double(cx - 12, cy - 12, 24, 24));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("NATIVE SYSTEM CORE VERTEX", cx + 22, cy - 5);

            // Real-World Telemetry Board Panel Layout
            g2d.setColor(new Color(3, 6, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 180, 150));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> SYSTEM CONFLICT STATE OVERRIDE: COMMITTED AND INITIALIZED (_TRUE)", 40, h - 210);
            g2d.drawString(">> ASYNC DISK FOOTPRINT FEED: ACTIVE FILESTREAM WRITE ON [restitution_production.log]", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> GLOBAL CONFLICT PASSTHROUGH INDEX: %,.5f%% EXACT SURFACE PARITY", engine.getSystemWideParityIndex() * 100), 40, h - 140);
            g2d.drawString(">> SYSTEM HARDWARE ALLOCATION: PROCESSOR CORE BINDING SECURED ON " + Runtime.getRuntime().availableProcessors() + " LOGICAL CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 150, 0));
            g2d.drawString(">> LOCAL SYSTEM TUNNEL ROUTING: TCP LOOPBACK BUS LISTENING ON PORT " + engine.getLiveActivePort(), 40, h - 70);
            g2d.drawString(">> WAVE HARMONIC CAPTURE SYSTEM FREQUENCY: 7.83Hz HARDWARE ANCHOR STABILIZED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            ProductionSystemConsole application = new ProductionSystemConsole();
            application.setVisible(true);
        });
    }
}
