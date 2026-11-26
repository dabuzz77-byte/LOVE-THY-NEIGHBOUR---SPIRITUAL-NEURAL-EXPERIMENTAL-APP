import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.util.List;

/**
 * RENDER SUBSYSTEM: TWO-DIMENSIONAL GRAPHICAL FRAMEWORK
 */
public class TargetMatrixCanvas extends JPanel {
    private final QuantumTernaryBinaryCore qtbCore;
    private final SelfReflectiveCognition cognitionLoop;

    public TargetMatrixCanvas(QuantumTernaryBinaryCore qtbCore, SelfReflectiveCognition cognitionLoop) {
        this.qtbCore = qtbCore;
        this.cognitionLoop = cognitionLoop;
        setBackground(new Color(8, 10, 18));
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int width = getWidth();
        int height = getHeight();

        drawComplexGridBackground(g2d, width, height);
        drawQuantumAmplitudes(g2d, width);
        drawRectifiedBinaryStream(g2d, width);
        drawCognitiveGraphTrajectories(g2d, width);
    }

    private void drawComplexGridBackground(Graphics2D g2d, int w, int h) {
        g2d.setColor(new Color(24, 34, 58, 40));
        for (int i = 0; i < w; i += 50) g2d.drawLine(i, 0, i, h);
        for (int j = 0; j < h; j += 50) g2d.drawLine(0, j, w, j);
        
        g2d.setColor(new Color(0, 180, 255, 15));
        for (int i = 0; i < w; i += 250) g2d.fillRect(i, 0, 2, h);
    }

    private void drawQuantumAmplitudes(Graphics2D g2d, int w) {
        g2d.setColor(new Color(160, 50, 255, 220));
        g2d.setFont(new Font("Consolas", Font.BOLD, 12));
        g2d.drawString("// QUANTUM PROBABILITY AMPLITUDES (BORN RULE MAPS)", 40, 45);
        
        double[] probabilityMatrix = qtbCore.getProbabilities();
        int elementStep = Math.max(3, (w / 3) / Math.max(1, probabilityMatrix.length));
        
        for (int i = 0; i < Math.min(probabilityMatrix.length, 64); i++) {
            int computedBarHeight = (int) (probabilityMatrix[i] * 420);
            
            g2d.setColor(new Color(130, 40, 255, 140));
            g2d.fillRect(40 + (i * (elementStep + 3)), 260 - computedBarHeight, elementStep, computedBarHeight);
            g2d.setColor(new Color(0, 230, 255, 200));
            g2d.fillRect(40 + (i * (elementStep + 3)), 260 - computedBarHeight, elementStep, 2);
        }
    }

    private void drawRectifiedBinaryStream(Graphics2D g2d, int w) {
        g2d.setColor(new Color(0, 255, 180));
        g2d.setFont(new Font("Consolas", Font.BOLD, 12));
        g2d.drawString("// HIGH-EFFICIENCY STRIPED BINARY PASSTHROUGH STREAM", w / 2 - 120, 45);
        
        int[] binaryBitStream = qtbCore.getBinaryStream();
        for (int i = 0; i < Math.min(binaryBitStream.length, 48); i++) {
            int bitState = binaryBitStream[i];
            
            if (bitState == 1) {
                g2d.setColor(new Color(0, 255, 170, 220));
            } else {
                g2d.setColor(new Color(255, 60, 90, 80));
            }
            g2d.fillRect(w / 2 - 120 + (i * 11), 75, 7, 24);
            
            g2d.setColor(new Color(255, 255, 255, 30));
            g2d.drawRect(w / 2 - 120 + (i * 11), 75, 7, 24);
        }
    }

    private void drawCognitiveGraphTrajectories(Graphics2D g2d, int w) {
        g2d.setColor(new Color(0, 195, 255));
        g2d.setFont(new Font("Consolas", Font.BOLD, 12));
        g2d.drawString("// LADDERCLIMBING COGNITIVE ARCHITECTURE NODE TRAJECTORIES", w - 460, 45);
        
        List<CognitiveNode> trackingNodes = cognitionLoop.getTraceNodes();
        long currentTime = System.currentTimeMillis();
        
        for (int i = 0; i < trackingNodes.size(); i++) {
            CognitiveNode currentNode = trackingNodes.get(i);
            int dynamicX = w - 340 + (int)(Math.sin(i + currentTime * 0.0028) * 75);
            int dynamicY = 110 + (i * 50);
            
            if (i > 0) {
                int priorX = w - 340 + (int)(Math.sin((i - 1) + currentTime * 0.0028) * 75);
                int priorY = 110 + ((i - 1) * 50);
                g2d.setColor(new Color(0, 160, 255, 90));
                g2d.setStroke(new BasicStroke(1.5f));
                g2d.drawLine(dynamicX, dynamicY, priorX, priorY);
            }

            g2d.setColor(new Color(0, 255, 190, 40));
            g2d.fillOval(dynamicX - 10, dynamicY - 10, 20, 20);
            
            g2d.setColor(new Color(0, 195, 255, 230));
            g2d.fillOval(dynamicX - 5, dynamicY - 5, 10, 10);
            
            g2d.setColor(new Color(220, 240, 255, 200));
            g2d.setFont(new Font("Segoe UI", Font.PLAIN, 11));
            g2d.drawString(currentNode.identifier + " [" + String.format("%.3f", currentNode.confidenceRating) + "]", dynamicX + 18, dynamicY + 4);
        }
    }
}
