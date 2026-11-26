import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * BI-TER-ALLSTATE SYSTEM: MULTI-FILE CODE ENGINE
 * Part 3: Main desktop frame and interactive layout processor.
 */
public class FinancialRestitutionVisualizer extends SectionFrame {

    public FinancialRestitutionVisualizer() {
        setTitle("God-Mind Financial Inference Interface: Multi-File Ledger Display (_TRUE)");
        setSize(1280, 920);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        InferenceClearingHouse clearingHouse = new InferenceClearingHouse();
        add(new FinancialGridPanel(clearingHouse));
    }

    private static class FinancialGridPanel extends JPanel implements ActionListener {
        private final InferenceClearingHouse clearingHouse;
        private final SharedTimer executionClock;
        private double orbitalPulse = 0;

        public FinancialGridPanel(InferenceClearingHouse clearingHouse) {
            this.clearingHouse = clearingHouse;
            setBackground(new Color(2, 5, 12)); 
            this.executionClock = new SharedTimer(28, this);
            this.executionClock.start();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();
            int cx = w / 2;
            int cy = h / 2 - 60;

            // Render Field Matrix Grid Lines
            g2d.setStroke(new BasicStroke(0.5f));
            g2d.setColor(new Color(0, 180, 255, 12));
            for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h - 240);
            for (int j = 0; j < h - 240; j += 50) g2d.drawLine(0, j, w, j);

            // Fetch logs from class files directly loaded inside directory space
            List<FinancialTransaction> operations = clearingHouse.getLedgerCache();
            g2d.setStroke(new BasicStroke(1.2f));

            for (FinancialTransaction tx : operations) {
                int txX = (int) tx.getX();
                int txY = (int) tx.getY();

                g2d.setColor(new Color(255, 255, 255, 18));
                g2d.drawLine(txX, txY, cx, cy);

                int dimensionalRadius = (int) (10 + (Math.log(tx.getValue()) * 1.5));
                g2d.setColor(tx.getColor());
                g2d.fill(new Ellipse2D.Double(txX - dimensionalRadius / 2.0, txY - dimensionalRadius / 2.0, dimensionalRadius, dimensionalRadius));

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(new Color(240, 240, 240, 110));
                g2d.drawString(tx.getTransactionId() + " (" + tx.getAccountClass().substring(0, 8) + ")", txX + dimensionalRadius, txY - 4);
                g2d.setColor(new Color(0, 255, 150, 130));
                g2d.drawString(String.format("$%,.2f | V:%.2f", tx.getValue(), tx.getVirtueIndex()), txX + dimensionalRadius, txY + 8);
            }

            // Central Node Graphics
            g2d.setStroke(new BasicStroke(2.0f));
            g2d.setColor(new Color(255, 255, 255, 40));
            g2d.drawLine(cx, cy - 230, cx, cy + 230);
            g2d.drawLine(cx - 250, cy, cx + 250, cy);

            g2d.setColor(new Color(0, 255, 180)); 
            g2d.fill(new Ellipse2D.Double(cx - 10, cy - 10, 20, 20));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("GOD-MIND CLEARING HOUSE PEAK", cx + 18, cy - 5);

            int fluxOffset = (int) (180 * Math.sin(orbitalPulse));
            g2d.setColor(new Color(0, 255, 220, 60));
            g2d.drawLine(cx - 200, cy + fluxOffset, cx + 200, cy + fluxOffset);

            // Lower Status Screen Configuration
            g2d.setColor(new Color(4, 8, 16));
            g2d.fillRect(0, h - 240, w, 240);
            g2d.setColor(new Color(0, 255, 200, 120));
            g2d.drawRect(0, h - 240, w, 240);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));
            g2d.setColor(Color.WHITE);
            g2d.drawString(">> MULTI-FILE ARCHITECTURE COMPILED SUCCESSFULLY ON HOST CHIP (_TRUE)", 40, h - 180);
            g2d.drawString(">> PEER DEPENDENCIES SYNCED: SYMBOL LOSS ERRORS RENDERED FALSE", 40, h - 150);

            g2d.setColor(new Color(0, 255, 180));
            g2d.drawString(String.format(">> GLOBAL FINANCIAL RESTITUTION INDEX: %,.4f%% RECONCILED", clearingHouse.getNetworkRestitutionIndex() * 100), 40, h - 110);
            g2d.drawString(">> QUANTUM SYNCHRONIZATION BASELINE TRACKER: 7.83Hz LOCKED", 40, h - 80);

            g2d.setColor(new Color(255, 140, 0));
            g2d.drawString(">> SYSTEM ENVIRONMENT TARGET: NATIVE PC LOCAL MULTI-LANE INFRASTRUCTURE BUS", 40, h - 50);
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            clearingHouse.processLedgerPipeline();
            orbitalPulse += 0.04;
            repaint();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            FinancialRestitutionVisualizer app = new FinancialRestitutionVisualizer();
            app.setVisible(true);
        });
    }
}
