import javax.swing.*;
import java.awt.*;
import java.util.List;

/**
 * Block 11: Graphics user interface element handling dual-buffered custom telemetry
 * vector drawings and process grid maps.
 */
public class TelemetryCanvas extends JPanel {
    private final FluxGridCell[][] dataGridSource;
    private final List<TrackingAgentNode> workerMeshReference;
    private final ConvergenceEngine structuralAnalyzer;
    private final int totalColumns, totalRows;

    public TelemetryCanvas(FluxGridCell[][] grid, List<TrackingAgentNode> nodes, ConvergenceEngine engine, int cols, int rows) {
        this.dataGridSource = grid;
        this.workerMeshReference = nodes;
        this.structuralAnalyzer = engine;
        this.totalColumns = cols;
        this.totalRows = rows;
        setBackground(new Color(12, 14, 18));
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        // 1. Draw structural blueprint grid lines
        g2.setColor(new Color(40, 45, 60, 45));
        for (int i = 0; i < getWidth(); i += 40) g2.drawLine(i, 0, i, getHeight());
        for (int j = 0; j < getHeight(); j += 40) g2.drawLine(0, j, getWidth(), j);

        // 2. Draw Highly Detailed Cellular Flux Processing Grid
        int widthStep = 22;
        int heightStep = 22;
        int initialLeftMargin = 40;
        int initialTopMargin = 120;

        for (int c = 0; c < totalColumns; c++) {
            for (int r = 0; r < totalRows; r++) {
                FluxGridCell cell = dataGridSource[c][r];
                int coordinateX = initialLeftMargin + (c * (widthStep + 4));
                int coordinateY = initialTopMargin + (r * (heightStep + 4));

                int lightingWeight = (int) Math.min(255, Math.max(0, cell.getCalculatedInternalCharge() * 2.5));
                g2.setColor(new Color(0, lightingWeight, (int) (lightingWeight * 0.5), 185));
                g2.fillRect(coordinateX, coordinateY, widthStep, heightStep);
                
                g2.setColor(new Color(30, 38, 52));
                g2.drawRect(coordinateX, coordinateY, widthStep, heightStep);
            }
        }

        // 3. Render Active Self-Selecting Network Tracking Vectors
        g2.setStroke(new BasicStroke(1.2f));
        for (TrackingAgentNode node : workerMeshReference) {
            // Draw baseline node component point
            g2.setColor(new Color(25, 30, 42));
            g2.fillOval(node.getPositionX() - 10, node.getPositionY() - 10, 20, 20);
            g2.setColor(new Color(0, 195, 255));
            g2.drawOval(node.getPositionX() - 10, node.getPositionY() - 10, 20, 20);
            
            g2.setColor(Color.WHITE);
            g2.setFont(new Font("Monospaced", Font.PLAIN, 10));
            g2.drawString(node.getStructuralId(), node.getPositionX() - 25, node.getPositionY() - 14);

            // Connect a continuous visualization tracking line back into the cellular process grid matching its target reference
            if (node.getTargetedGridCellReference() != null) {
                int cellTargetX = initialLeftMargin + (node.getTargetedGridCellReference().getColumnCoordinate() * (widthStep + 4)) + (widthStep / 2);
                int cellTargetY = initialTopMargin + (node.getTargetedGridCellReference().getRowCoordinate() * (heightStep + 4)) + (heightStep / 2);
                
                g2.setColor(new Color(0, 255, 140, 80));
                g2.drawLine(node.getPositionX(), node.getPositionY(), cellTargetX, cellTargetY);
            }
        }

        // 4. Render Interface Text Telemetry Overlays
        double runtimeVariance = structuralAnalyzer.computeSystemicVariance();
        double metricCoherence = structuralAnalyzer.calculateCoherencePercentage(runtimeVariance);

        g2.setFont(new Font("Monospaced", Font.BOLD, 14));
        g2.setColor(Color.GREEN);
        g2.drawString("SYSTEM MONITOR INTEGRATION FRAME: [COHERENT // AUTH=TRUE]", 40, 45);
        g2.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2.setColor(Color.WHITE);
        g2.drawString(String.format("Global Matrix Coherence: %.2f%%", metricCoherence), 40, 75);
        g2.drawString(String.format("Cumulative Process Tokens: %d units", SystemSubstrate.getInstance().getGlobalTokenCount()), 40, 95);
        g2.drawString(String.format("Local Engine Uptime: %d sec", SystemSubstrate.getInstance().getUptimeSeconds()), 650, 75);
    }
}
