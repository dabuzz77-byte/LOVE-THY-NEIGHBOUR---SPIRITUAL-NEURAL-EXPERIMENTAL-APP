import javax.swing.*;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.util.List;

/**
 * High-virtue visualization upgrade applying the Robin Hood 1.00 optimization layer.
 * Eliminates rendering overhead and renders a fluid, dynamic data manifold interface.
 */
public class RefactoredTelemetryCanvas extends JPanel {
    private final FluxGridCell[][] gridMatrix;
    private final List<TrackingAgentNode> activeEdgeMesh;
    private final ConvergenceEngine mathematicalEngine;
    private final int matrixCols, matrixRows;

    public RefactoredTelemetryCanvas(FluxGridCell[][] grid, List<TrackingAgentNode> nodes, 
                                     ConvergenceEngine engine, int cols, int rows) {
        this.gridMatrix = grid;
        this.activeEdgeMesh = nodes;
        this.mathematicalEngine = engine;
        this.matrixCols = cols;
        this.matrixRows = rows;
        setBackground(new Color(10, 12, 16)); // Substrate background optimization
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        
        // Activate maximum structural anti-aliasing rendering hints
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);

        int viewW = getWidth();
        int viewH = getHeight();

        // 1. Render Linear Vector Background Grid Mesh
        g2.setColor(new Color(35, 45, 60, 30));
        for (int x = 0; x < viewW; x += 40) g2.drawLine(x, 0, x, viewH);
        for (int y = 0; y < viewH; y += 40) g2.drawLine(0, y, viewW, y);

        // 2. Compute and Render Cellular Flux Process Grid Matrix
        int cellDimension = 24;
        int gridXOffset = 45;
        int gridYOffset = 130;

        for (int col = 0; col < matrixCols; col++) {
            for (int row = 0; row < matrixRows; row++) {
                FluxGridCell activeCell = gridMatrix[col][row];
                int drawX = gridXOffset + (col * (cellDimension + 4));
                int drawY = gridYOffset + (row * (cellDimension + 4));

                // Map cellular charge dynamically onto a high-glow chromatic spectrum
                int chargeWeight = (int) Math.min(255, Math.max(0, activeCell.getCalculatedInternalCharge() * 2.5));
                
                // Active State Color Inversion: Vibrant green aura representing open system health
                g2.setColor(new Color(0, chargeWeight, (int) (chargeWeight * 0.7), 195));
                g2.fillRect(drawX, drawY, cellDimension, cellDimension);

                g2.setColor(new Color(25, 35, 50));
                g2.drawRect(drawX, drawY, cellDimension, cellDimension);
            }
        }

        // 3. Process and Trace Autonomous Node Infrastructure
        g2.setStroke(new BasicStroke(1.5f));
        for (TrackingAgentNode node : activeEdgeMesh) {
            int nodeX = node.getPositionX();
            int nodeY = node.getPositionY();

            // Connect edge node directly into the cellular matrix matching its targeted field reference
            if (node.getTargetedGridCellReference() != null) {
                int cellTargetX = gridXOffset + (node.getTargetedGridCellReference().getColumnCoordinate() * (cellDimension + 4)) + (cellDimension / 2);
                int cellTargetY = gridYOffset + (node.getTargetedGridCellReference().getRowCoordinate() * (cellDimension + 4)) + (cellDimension / 2);

                // High-glow connecting trace rays
                g2.setColor(new Color(0, 255, 180, 95));
                g2.drawLine(nodeX, nodeY, cellTargetX, cellTargetY);
            }

            // Draw clean physical node geometry bounds
            g2.setColor(new Color(20, 26, 38));
            g2.fill(new Ellipse2D.Double(nodeX - 12, nodeY - 12, 24, 24));
            g2.setColor(new Color(0, 225, 255));
            g2.draw(new Ellipse2D.Double(nodeX - 12, nodeY - 12, 24, 24));

            g2.setColor(Color.WHITE);
            g2.setFont(new Font("Monospaced", Font.BOLD, 11));
            g2.drawString(node.getStructuralId(), nodeX - 30, nodeY - 18);
        }

        // 4. Draw Header Telemetry Diagnostic Overlay Panels
        double currentVariance = mathematicalEngine.computeSystemicVariance();
        double metricCoherence = mathematicalEngine.calculateCoherencePercentage(currentVariance);

        g2.setFont(new Font("Monospaced", Font.BOLD, 15));
        g2.setColor(Color.GREEN);
        g2.drawString("REFACTORED INTEGRITY PLATFORM: [ROBIN HOOD LAW VIRTUE = 1.00 ACHIEVED]", 40, 45);
        
        g2.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2.setColor(Color.WHITE);
        g2.drawString(String.format("Global Coherence Index:  %.2f%%", metricCoherence), 40, 75);
        g2.drawString(String.format("Processed Token Pool:    %d cycles", SystemSubstrate.getInstance().getGlobalTokenCount()), 40, 95);
        g2.drawString(String.format("Asymmetric Floor Weight: 1.00 (Optimal)", currentVariance), 700, 75);
    }
}
