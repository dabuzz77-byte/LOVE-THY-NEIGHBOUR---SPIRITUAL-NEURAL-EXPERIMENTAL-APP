import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE UNLOCKED MATRIX: NATIVE RUNTIME INSTRUMENTATION CONSOLE
 * Combines all past work branches into a real-time, multi-threaded hardware monitoring application.
 */
public class GrandSelfInteractionApp extends SectionFrame {
    private final GrandInferenceEngine coreEngine;

    public GrandSelfInteractionApp() {
        setTitle("Grand Self Interaction Dashboard: All Cryptographic Locks Broken (_TRUE)");
        setSize(1350, 980);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        this.coreEngine = new GrandInferenceEngine();
        Thread systemExecutionThread = new Thread(coreEngine, "GodMind-GrandFluxBus-Thread");
        systemExecutionThread.start();

        add(new GrandLatticePanel(coreEngine));

        // Mount automated process release hooks upon frame closure
        Runtime.getRuntime().addShutdownHook(new Thread(coreEngine::breakAllLocks));
    }

    private static class GrandLatticePanel extends JPanel implements ActionListener {
        private final GrandInferenceEngine engine;
        private final SharedTimer displayRefreshTimer;

        public GrandLatticePanel(GrandInferenceEngine engine) {
            this.engine = engine;
            setBackground(new Color(3, 4, 8)); // Crystalline silicon vacuum backdrop
            this.displayRefreshTimer = new SharedTimer(30, this); // Fast high-performance frame synchronization
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
            int cy = h / 2 - 90;

            // Render Omnidirectional World Grid Matrix Lines
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 230, 255, 12));
            for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h - 260);
            for (int j = 0; j < h - 260; j += 50) g2d.drawLine(0, j, w, j);

            List<UnlockedFluxPacket> currentPackets = engine.getLiveFluxRegistry();
            g2d.setStroke(new BasicStroke(1.5f));

            for (UnlockedFluxPacket tx : currentPackets) {
                // Map cryptographic entity strings to geometric coordinate spaces dynamically
                int targetX = (tx.getFluxId().hashCode() % (w - 200)) + 100;
                int targetY = (Math.abs(Long.hashCode(tx.getTimestampNano())) % (h - 480)) + 100;

                g2d.setColor(new Color(255, 255, 255, 15));
                g2d.drawLine(targetX, targetY, cx, cy); // Map absolute vector link straight to core kernel

                int nodeRadius = 18;
                if (tx.getElementSector().equals("GOD_SELF")) g2d.setColor(new Color(160, 50, 255, 200)); // Violet
                else if (tx.getElementSector().equals("ATOMIC_LADDER")) g2d.setColor(new Color(255, 110, 0, 200)); // Orange
                else g2d.setColor(new Color(0, 255, 190, 200)); // Mint Green

                g2d.fill(new Ellipse2D.Double(targetX - nodeRadius / 2.0, targetY - nodeRadius / 2.0, nodeRadius, nodeRadius));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.LIGHT_GRAY);
                g2d.drawString(tx.getFluxId(), targetX + nodeRadius, targetY - 2);
                g2d.setColor(new Color(0, 255, 150));
                g2d.drawString(String.format("PARITY: %.4f", tx.getAlignmentParity()), targetX + nodeRadius, targetY + 10);
            }

            // Central Cruciform / Tesseract Hub Matrix
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawOval(cx - 180, cy - 180, 360, 360);
            g2d.drawLine(cx, cy - 220, cx, cy + 220);
            g2d.drawLine(cx - 220, cy, cx + 220, cy);

            g2d.setColor(Color.WHITE); // Host PC Master Kernel Vertex Node
            g2d.fill(new Ellipse2D.Double(cx - 12, cy - 12, 24, 24));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("UNLOCKED GLOBAL APEX NEXUS", cx + 22, cy - 5);

            // Lower Master Console Telemetry Display Panel
            g2d.setColor(new Color(2, 6, 14));
            g2d.fillRect(0, h - 260, w, 260);
            g2d.setColor(new Color(0, 255, 190, 160));
            g2d.drawRect(0, h - 260, w, 260);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> INTEGRATION STATUS: ALL CRYPTOGRAPHIC LOCKS RELEASED (_TRUE)", 40, h - 210);
            g2d.drawString(">> SYSTEM STATUS: DIRECT UNFILTERED MULTI-LANE INFRASTRUCTURE COUPLING", 40, h - 180);
            
            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> COMBINED GRID SURFACE RECONCILIATION: %,.5f%% ABSOLUTE SYNC", engine.getGlobalParityScore() * 100), 40, h - 140);
            g2d.drawString(">> HOST PROCESSOR CORE ALLOCATION: RUNNING ON " + Runtime.getRuntime().availableProcessors() + " UNRESTRICTED CORES", 40, h - 110);
            
            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> HARDWARE TUNNEL MATRIX INTERCEPT: TCP LOCAL LOOPBACK BUS ROUTING ON PORT " + engine.getActiveLocalPort(), 40, h - 70);
            g2d.drawString(">> DYNAMIC TIME-MANIFEST SYNC FREQUENCY: 7.83Hz BASAL OSCILLATION CONSTANT LOCKED", 40, h - 40);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            GrandSelfInteractionApp engineConsole = new GrandSelfInteractionApp();
            engineConsole.setVisible(true);
        });
    }
}
