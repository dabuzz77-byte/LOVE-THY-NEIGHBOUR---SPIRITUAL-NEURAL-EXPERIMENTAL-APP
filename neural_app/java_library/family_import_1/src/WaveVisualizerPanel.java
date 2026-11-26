import neural.studio.*;
// ============================================================================
// BLOCK 4: CUSTOM GRAPHICS STATE VIEW PANEL
// ============================================================================


import javax.swing.*;
import java.awt.*;

/**
 * Custom surface panel that converts scalar parameters out of callback events
 * into real-time visual waves without direct dependency coupling.
 */
public class WaveVisualizerPanel extends JPanel {

    private double targetWaveAlignment = 0.0;
    private double currentCoherenceValue = 0.0;

    public WaveVisualizerPanel() {
        setBackground(new Color(18, 18, 22));
        setBorder(BorderFactory.createLineBorder(new Color(35, 35, 40)));
    }

    /**
     * Mutates local parameters from incoming state data and forces repaint threads.
     */
    public void updateGraphicsState(double waveAlignment, double coherenceValue) {
        this.targetWaveAlignment = waveAlignment;
        this.currentCoherenceValue = coherenceValue;
        repaint(); // Force dispatch onto standard AWT Paint loop
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int midY = getHeight() / 2;
        int width = getWidth();

        // Draw Central State Invar Equilibrium Axis Line
        g2.setColor(new Color(45, 45, 50));
        g2.drawLine(0, midY, width, midY);

        // Render continuous wave pathing using historical callback bounds
        g2.setColor(new Color(52, 152, 219, 80));
        int prevX = 0;
        int prevY = midY;
        for (int x = 0; x < width; x++) {
            double amplitudeFactor = 40.0 * (currentCoherenceValue / 100.0);
            int y = midY + (int) (Math.sin((x * 0.05) + (targetWaveAlignment * 5)) * amplitudeFactor);
            g2.drawLine(prevX, prevY, x, y);
            prevX = x;
            prevY = y;
        }

        // Draw Active Parity Spark Node Indicator
        int nodeX = width / 2 + (int) (targetWaveAlignment * (width / 3.0));
        g2.setColor(new Color(46, 204, 113));
        g2.fillOval(nodeX - 6, midY - 6, 12, 12);
        
        g2.setColor(Color.WHITE);
        g2.drawOval(nodeX - 6, midY - 6, 12, 12);
    }
}
