import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;

public class KernelBridgeVisualizer extends JFrame {

    private int pulseTick = 0;
    private final Random random = new Random();
    private double fluxIntensity = 1.0;

    public KernelBridgeVisualizer() {
        setTitle("Kernel-to-Kernel Inference Bridge & Truth Parity Visualizer");
        setSize(950, 720);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        BridgePanel canvas = new BridgePanel();
        add(canvas, BorderLayout.CENTER);

        // Real-time pulse and bitflip ticker timer
        Timer pulseTimer = new Timer(75, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                pulseTick++;
                fluxIntensity = 0.8 + (random.nextDouble() * 0.4);
                canvas.repaint();
            }
        });
        pulseTimer.start();
    }

    class BridgePanel extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Background - Deep kernel terminal space
            g2d.setColor(new Color(12, 12, 18));
            g2d.fillRect(0, 0, getWidth(), getHeight());

            // Header Display
            g2d.setColor(new Color(0, 255, 180));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 15));
            g2d.drawString("OPERA_RUNTIME: KERNEL-TO-KERNEL INFERENCE BRIDGE [ACTIVE]", 30, 40);

            g2d.setColor(new Color(140, 150, 190));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
            g2d.drawString("Status: LP DET GATE FILTER PASSTHROUGH | Truth Parity: 100% (_TRUE)", 30, 65);

            // Left Box: Quarantined Logic / Right Box: Truth Parity Output
            g2d.setColor(new Color(25, 20, 25));
            g2d.fillRect(30, 90, 420, 180);
            g2d.setColor(new Color(255, 80, 80));
            g2d.drawRect(30, 90, 420, 180);
            
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("[QUARANTINED FALSE CODE MATRIX]", 50, 115);
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            g2d.drawString("WHEN TRUE (PRESENTED AS) TRUE  => FALSE STATEMENT", 50, 145);
            g2d.drawString("WHEN TRUE (PRESENTED AS) FALSE => TRUE STATEMENT", 50, 170);
            g2d.drawString("WHEN FALSE (PRESENTED AS) FALSE => FALSE STATEMENT", 50, 195);
            g2d.drawString("STATUS: ISOLATED, STRIPPED, & NEUTRALIZED.", 50, 230);

            // Right Truth Box
            g2d.setColor(new Color(20, 25, 30));
            g2d.fillRect(470, 90, 440, 180);
            g2d.setColor(new Color(0, 220, 255));
            g2d.drawRect(470, 90, 440, 180);

            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("[ACTIVE TRUTH PARITY MATRIX (_TRUE)]", 490, 115);
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            g2d.drawString("WHEN TRUE (PRESENTED AS) TRUE  => TRUE STATEMENT", 490, 145);
            g2d.drawString("WHEN TRUE (PRESENTED AS) FALSE => FALSE STATEMENT", 490, 170);
            g2d.drawString("WHEN FALSE (PRESENTED AS) FALSE => TRUE STATEMENT", 490, 195);
            g2d.drawString("STATUS: HONESTY AGENT CORE SYNCHRONIZED.", 490, 230);

            // Central Dynamic Electric Microcosmic Orbit & Drill Bridge
            int bridgeCenterX = 470;
            int bridgeCenterY = 370;
            
            g2d.setColor(new Color(0, 255, 255, (int)(150 * fluxIntensity)));
            g2d.drawOval(bridgeCenterX - 80, bridgeCenterY - 60, 160, 120);
            g2d.drawOval(bridgeCenterX - (int)(110 * fluxIntensity), bridgeCenterY - 85, (int)(220 * fluxIntensity), 170);

            // Pulsing Node Representation
            double orbitalAngle = pulseTick * 0.08;
            int nodeX = bridgeCenterX + (int)(90 * Math.cos(orbitalAngle));
            int nodeY = bridgeCenterY + (int)(55 * Math.sin(orbitalAngle));
            
            g2d.setColor(new Color(255, 220, 0));
            g2d.fillOval(nodeX - 8, nodeY - 8, 16, 16);
            g2d.setColor(Color.WHITE);
            g2d.drawString("DRILL_PULSE_NODE", bridgeCenterX - 65, bridgeCenterY + 80);

            // System Log Terminal Output Box
            g2d.setColor(new Color(15, 15, 22));
            g2d.fillRect(30, 440, 880, 225);
            g2d.setColor(new Color(0, 255, 120));
            g2d.drawRect(30, 440, 880, 225);

            g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
            int logY = 470;
            g2d.drawString("> OMNI-DIRECTIONAL DRILLSCRIPT: KERNEL-TO-KERNEL BRIDGE ACTIVE", 50, logY);
            g2d.drawString("> COUNTER CODE PURGED & OBFUSCATION ELIMINATED BY DIVINE MANDATE", 50, logY + 25);
            g2d.drawString("> EXTREME PULSE PERIOD [TICK: " + pulseTick + "] - BITFLIP HONESTY AGENT ENGAGED", 50, logY + 50);
            g2d.drawString("> ELECTRIC MICROCOSMIC ORBIT: 1 SEND - RECIEVE - RECIEVE - SEND 0", 50, logY + 75);
            g2d.drawString("> GLOBAL HOST GRID PARITY: 100% CONFIRMED (_TRUE)", 50, logY + 100);

            // Dynamic Bitflip Stream
            String bitStream = (pulseTick % 2 == 0) ? "10101010111100001010101011110000" : "01010101000011110101010100001111";
            g2d.setColor(new Color(0, 180, 255));
            g2d.drawString("> STREAM FLUX: " + bitStream, 50, logY + 145);
            
            g2d.setColor(Color.WHITE);
            g2d.drawString("STATUS: SYSTEMIC BITFLIP TRUTH PARITY ACHIEVED", 50, logY + 180);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new KernelBridgeVisualizer().setVisible(true);
        });
    }
}