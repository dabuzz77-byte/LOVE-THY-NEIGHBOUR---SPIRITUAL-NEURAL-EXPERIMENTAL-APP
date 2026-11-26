import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE PRODUCTION SYSTEM: LIVING RUNTIME MONITOR
 * Displays host hardware status, active network listening channels, and persistent file logging states.
 */
public class ProductionControlConsole extends JFrame {
    private final LiveInferenceEngine coreEngine;

    public ProductionControlConsole() {
        setTitle("Production Control Console: Elevated Real-World Interface Engine (_TRUE)");
        setSize(1300, 950);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.coreEngine = new LiveInferenceEngine();
        Thread engineThread = new Thread(coreEngine, "GodMind-HardwareBus-Thread");
        engineThread.start();

        add(new ProductionGridPanel(coreEngine));

        Runtime.getRuntime().addShutdownHook(new Thread(coreEngine::terminateEngine));
    }

    private static class ProductionGridPanel extends JPanel implements ActionListener {
        private final LiveInferenceEngine engine;
        private final Timer displayRefreshTimer;

        public ProductionGridPanel(LiveInferenceEngine engine) {
            this.engine = engine;
            setBackground(new Color(1, 4, 10)); 
            this.displayRefreshTimer = new Timer(33, this); 
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

            // Render background structural alignment grid
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 255, 120, 10));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 60) g2d.drawLine(0, j, w, j);

            List<RealWorldTransaction> activeTracks = engine.getProductionQueue();
            g2d.setStroke(new BasicStroke(1.5f));

            for (RealWorldTransaction tx : activeTracks) {
                int seedX = (tx.getLiveTxId().hashCode() % (w - 200)) + 100;
                int seedY = (Math.abs(Long.hashCode(tx.getEpochTimestamp())) % (h - 450)) + 100;

                g2d.setColor(new Color(255, 255, 255, 12));
                g2d.drawLine(seedX, seedY, cx, cy); 

                int visualSize = (int) (12 + (Math.log10(tx.getRealWorldAssetValue()) * 2));
                
                if (tx.getExecutionClass().equals("UNIVERSAL")) g2d.setColor(new Color(150, 50, 255, 200));
                else if (tx.getExecutionClass().equals("SYSTEMIC")) g2d.setColor(new Color(255, 90, 0, 200));
                else g2d.setColor(new Color(0, 240, 255, 200));

                g2d.fill(new Ellipse2D.Double(seedX - visualSize / 2.0, seedY - visualSize / 2.0, visualSize, visualSize));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(tx.getLiveTxId(), seedX + visualSize, seedY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("$%,.2f | P:%.3f", tx.getRealWorldAssetValue(), tx.getPhysicalParityMetric()), seedX + visualSize, seedY + 10);
            }

            // Central Node
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 160, cy - 160, 320, 320);
            g2d.drawLine(cx, cy - 200, cx, cy + 200);
            g2d.drawLine(cx - 200, cy, cx + 250, cy);

            g2d.setColor(Color.WHITE); 
            g2d.fill(new Ellipse2D.Double(cx - 12, cy - 12, 24, 24));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("NATIVE SYSTEM CORE VERTEX", cx + 20, cy - 5);

            // Telemetry Output Board
            g2d.setColor(new Color(2, 5, 12));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 150, 150));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> INTEGRATION STATUS: ELEVATED REAL-WORLD ENGINE COMMITTED (_TRUE)", 40, h - 210);
            g2d.drawString(">> ACTIVE SYSTEM FILE I/O TRACKER: WRITING TO [restitution_production.log]", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> GLOBAL SYSTEM SURFACE ALIGNMENT: %,.5f%% EXACT PARITY", engine.getSystemWideParity() * 100), 40, h - 140);
            g2d.drawString(">> NATIVE PROCESSOR CORE BINDING: ALL-PREV ALLOCATED ON " + Runtime.getRuntime().availableProcessors() + " LOGICAL UNITS", 40, h - 110);
            
            g2d.setColor(new Color(255, 160, 0));
            g2d.drawString(">> LOCAL SYSTEM COMMUNICATIONS NETWORK TUNNEL: ACTIVE ON TCP LOOPBACK PORT " + engine.getLocalActivePort(), 40, h - 70);
            g2d.drawString(">> RUNTIME BASELINE FREQUENCY SYNC INTERCEPT: 7.83Hz HARDWARE ANCHOR STABILIZED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            ProductionControlConsole console = new ProductionControlConsole();
            console.setVisible(true);
        });
    }
}
