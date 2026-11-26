import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.util.Map;

/**
 * Custom vector display panel. Renders deep real-time system matrices 
 * using absolute canvas coordinates and alpha blending.
 */
public class GridMatrixDisplayWorkspace extends JPanel implements CoreEventBus.TelemetrySubscriber {
    
    private long currentCycleId = 0;
    private double[][] quantumData = new double[4][4];
    private int[][] ternaryData = new int[4][4];
    private byte[][] binaryData = new byte[4][4];
    private Map<String, Double> runtimesMap = Map.of();

    public GridMatrixDisplayWorkspace() {
        setBackground(new Color(15, 15, 22));
        setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
    }

    @Override
    public void handleSystemFrame(long cycle, double[][] q, int[][] t, byte[][] b, Map<String, Double> metrics) {
        this.currentCycleId = cycle;
        this.quantumData = q;
        this.ternaryData = t;
        this.binaryData = b;
        this.runtimesMap = metrics;
        
        // Forces immediate visual paint traversal loop updates
        repaint();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        int cellW = getWidth() / 4;
        int gridHeight = getHeight() - 100;

        // Render Matrix 1: Quantum Layer
        drawQuantumCellGrid(g2, 10, 40, cellW - 20, gridHeight, "QUANTUM CONTEXT VECTOR |ψ⟩", new Color(186, 85, 211));
        
        // Render Matrix 2: Ternary Stabilization Layer
        drawTernaryCellGrid(g2, cellW + 10, 40, cellW - 20, gridHeight, "BALANCED TERNARY SYSTEM [-1,0,1]", new Color(255, 140, 0));
        
        // Render Matrix 3: Binary Instruction Sets
        drawBinaryCellGrid(g2, (cellW * 2) + 10, 40, cellW - 20, gridHeight, "NATIVE BINARY HARDWARE ", new Color(50, 205, 50));
        
        // Render Language Runtime Latency Bars
        drawLanguageThroughputGauges(g2, (cellW * 3) + 10, 40, cellW - 20, gridHeight);
        
        // Footer Cycle Label
        g2.setFont(new Font("Monospaced", Font.BOLD, 13));
        g2.setColor(Color.LIGHT_GRAY);
        g2.drawString("CURRENT PIPELINE PULSE INDEX: " + String.format("%07d", currentCycleId), 20, getHeight() - 15);
    }

    private void drawQuantumCellGrid(Graphics2D g2, int x, int y, int w, int h, String title, Color accent) {
        drawPanelContainerFrame(g2, x, y, w, h, title, accent);
        int pad = 30;
        int size = (w - (pad * 2)) / 4;
        g2.setFont(new Font("Monospaced", Font.PLAIN, 11));
        for(int i=0; i<4; i++) {
            for(int j=0; j<4; j++) {
                double val = quantumData[i][j];
                g2.setColor(new Color(accent.getRed(), accent.getGreen(), accent.getBlue(), (int)Math.min(255, Math.max(30, val * 200))));
                g2.fillRect(x + pad + (j * size), y + 60 + (i * size), size - 4, size - 4);
                g2.setColor(Color.WHITE);
                g2.drawString(String.format("%.2f", val), x + pad + (j * size) + 4, y + 60 + (i * size) + (size/2) + 4);
            }
        }
    }

    private void drawTernaryCellGrid(Graphics2D g2, int x, int y, int w, int h, String title, Color accent) {
        drawPanelContainerFrame(g2, x, y, w, h, title, accent);
        int pad = 30;
        int size = (w - (pad * 2)) / 4;
        g2.setFont(new Font("Monospaced", Font.BOLD, 13));
        for(int i=0; i<4; i++) {
            for(int j=0; j<4; j++) {
                int val = ternaryData[i][j];
                if (val == -1) g2.setColor(new Color(231, 76, 60, 180));
                else if (val == 0) g2.setColor(new Color(44, 62, 80, 180));
                else g2.setColor(new Color(46, 204, 113, 180));
                
                g2.fillRect(x + pad + (j * size), y + 60 + (i * size), size - 4, size - 4);
                g2.setColor(Color.WHITE);
                g2.drawString(String.valueOf(val), x + pad + (j * size) + (size/2) - 4, y + 60 + (i * size) + (size/2) + 4);
            }
        }
    }

    private void drawBinaryCellGrid(Graphics2D g2, int x, int y, int w, int h, String title, Color accent) {
        drawPanelContainerFrame(g2, x, y, w, h, title, accent);
        int pad = 30;
        int size = (w - (pad * 2)) / 4;
        g2.setFont(new Font("Monospaced", Font.BOLD, 14));
        for(int i=0; i<4; i++) {
            for(int j=0; j<4; j++) {
                byte val = binaryData[i][j];
                g2.setColor(val == 1 ? new Color(0, 255, 100, 100) : new Color(255, 255, 255, 15));
                g2.fillRect(x + pad + (j * size), y + 60 + (i * size), size - 4, size - 4);
                g2.setColor(val == 1 ? Color.GREEN : Color.DARK_GRAY);
                g2.drawString(String.valueOf(val), x + pad + (j * size) + (size/2) - 4, y + 60 + (i * size) + (size/2) + 4);
            }
        }
    }

    private void drawLanguageThroughputGauges(Graphics2D g2, int x, int y, int w, int h) {
        drawPanelContainerFrame(g2, x, y, w, h, "ENGINE HIGH LEVEL RUNTIMES PERFORMANCE", Color.CYAN);
        g2.setFont(new Font("Monospaced", Font.PLAIN, 12));
        int index = 0;
        for (Map.Entry<String, Double> entry : runtimesMap.entrySet()) {
            int rowY = y + 70 + (index * 45);
            g2.setColor(Color.LIGHT_GRAY);
            g2.drawString(entry.getKey(), x + 25, rowY);
            
            // Draw background track container
            g2.setColor(new Color(40, 40, 50));
            g2.fillRoundRect(x + 25, rowY + 8, w - 50, 10, 4, 4);
            
            // Draw dynamic fill indicator
            int barFillWidth = (int) ((entry.getValue() / 400.0) * (w - 50));
            g2.setColor(Color.CYAN);
            g2.fillRoundRect(x + 25, rowY + 8, Math.min(w - 50, barFillWidth), 10, 4, 4);
            
            g2.setColor(Color.WHITE);
            g2.drawString(String.format("%.1f f/ms", entry.getValue()), x + w - 110, rowY);
            index++;
        }
    }

    private void drawPanelContainerFrame(Graphics2D g2, int x, int y, int w, int h, String title, Color accent) {
        g2.setColor(new Color(24, 24, 36));
        g2.fillRoundRect(x, y, w, h, 12, 12);
        g2.setColor(new Color(255, 255, 255, 10));
        g2.drawRoundRect(x, y, w, h, 12, 12);
        
        g2.setColor(accent);
        g2.fillRect(x + 15, y + 15, 4, 18);
        
        g2.setColor(Color.WHITE);
        g2.setFont(new Font("Monospaced", Font.BOLD, 12));
        g2.drawString(title, x + 28, y + 28);
    }
}
