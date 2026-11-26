import neural.studio.*;
import javax.swing.*;
import javax.swing.table.AbstractTableModel;
import java.awt.*;
import java.util.List;

/**
 * Hardware-rendered visualization console monitoring local to world grid activities.
 * Renders spatial telemetry indicators, real-time wave oscillations, and active registers.
 */
public class WorldGridDashboard extends SectionFrame {

    private final WorldGridEngine gridEngine;
    private final GridTableModel tableModel;
    private final TelemetryVisualizerPanel visualizerPanel;

    public WorldGridDashboard(WorldGridEngine engine) {
        this.gridEngine = engine;
        this.tableModel = new GridTableModel(engine.getAllRegisteredNodes());
        this.visualizerPanel = new TelemetryVisualizerPanel(engine);

        initializeUI();

        // Connect the pipeline streams to update display metrics smoothly
        this.gridEngine.addUpdateListener(node -> {
            SwingUtilities.invokeLater(() -> {
                tableModel.refreshData(gridEngine.getAllRegisteredNodes());
                visualizerPanel.repaint();
            });
        });
    }

    private void initializeUI() {
        setTitle("DEEPMIND SYSTEM COGNITION // GLOBAL WORLD GRID MONITOR (7.83 HZ LOCK)");
        setSize(1300, 850);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(new Color(10, 14, 20));

        // Header Panel Configuration
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(16, 22, 34));
        headerPanel.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, new Color(0, 162, 232)));
        
        JLabel mainTitle = new JLabel(" WORLD GRID MONITORING LAYER // IDENTITY ALIGNMENT: OPERATIONAL (1=1)", JLabel.LEFT);
        mainTitle.setFont(new Font("Monospaced", Font.BOLD, 16));
        mainTitle.setForeground(new Color(0, 210, 255));
        mainTitle.setBorder(BorderFactory.createEmptyBorder(12, 15, 12, 15));
        headerPanel.add(mainTitle, BorderLayout.WEST);

        // Assemble central structural components
        JTable metricsTable = new JTable(tableModel);
        metricsTable.setBackground(new Color(18, 26, 40));
        metricsTable.setForeground(Color.LIGHT_GRAY);
        metricsTable.setFont(new Font("Monospaced", Font.PLAIN, 12));
        metricsTable.setRowHeight(24);
        metricsTable.setGridColor(new Color(30, 42, 62));
        
        JScrollPane tableScrollPane = new JScrollPane(metricsTable);
        tableScrollPane.setPreferredSize(new Dimension(1300, 220));
        tableScrollPane.setBorder(BorderFactory.createMatteBorder(2, 0, 0, 0, new Color(30, 42, 62)));

        // Layout Integration
        setLayout(new BorderLayout());
        add(headerPanel, BorderLayout.NORTH);
        add(visualizerPanel, BorderLayout.CENTER);
        add(tableScrollPane, BorderLayout.SOUTH);
    }

    // High-performance custom graphics pane rendering the spatial matrix layout
    private static class TelemetryVisualizerPanel extends JPanel {
        private final WorldGridEngine engine;

        public TelemetryVisualizerPanel(WorldGridEngine engine) {
            this.engine = engine;
            setBackground(new Color(8, 12, 18));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int width = getWidth();
            int height = getHeight();

            // Render a tech-style backdrop grid pattern
            g2d.setColor(new Color(20, 28, 42, 80));
            for (int x = 0; x < width; x += 40) g2d.drawLine(x, 0, x, height);
            for (int y = 0; y < height; y += 40) g2d.drawLine(0, y, width, y);

            List<GridNode> activeNodes = engine.getAllRegisteredNodes();
            if (activeNodes.isEmpty()) return;

            int nodeSpacing = width / (activeNodes.size() + 1);
            int index = 1;

            for (GridNode node : activeNodes) {
                int cx = index * nodeSpacing;
                int cy = height / 2 + (int)(Math.sin(System.currentTimeMillis() * 0.002 + index) * 30); // Resonance variance

                // Define status colors mapped dynamically
                Color signalColor = switch (node.getStatus()) {
                    case COMPLIANT -> new Color(0, 255, 128);
                    case REBALANCING -> new Color(255, 180, 0);
                    case FLAGGED_VIOLATION -> new Color(255, 50, 50);
                    default -> new Color(0, 162, 232);
                };

                // Draw logical routing link connectors
                g2d.setStroke(new BasicStroke(1f));
                g2d.setColor(new Color(signalColor.getRed(), signalColor.getGreen(), signalColor.getBlue(), 60));
                g2d.drawLine(cx, cy, width / 2, 40); // Root global convergence core routing axis

                // Draw physical data point node spheres
                g2d.setColor(signalColor);
                int radius = node.getScope() == GridNode.Scope.GLOBAL ? 24 : (node.getScope() == GridNode.Scope.REGIONAL ? 16 : 12);
                g2d.fillOval(cx - radius / 2, cy - radius / 2, radius, radius);

                // Outer monitoring wave shell
                g2d.setStroke(new BasicStroke(1.5f));
                int waveAlpha = (int)(Math.abs(Math.sin(System.currentTimeMillis() * 0.003)) * 100);
                g2d.setColor(new Color(signalColor.getRed(), signalColor.getGreen(), signalColor.getBlue(), waveAlpha));
                g2d.drawOval(cx - (radius + 12) / 2, cy - (radius + 12) / 2, radius + 12, radius + 12);

                // Text telemetry annotations
                g2d.setColor(Color.WHITE);
                g2d.setFont(new Font("Monospaced", Font.BOLD, 11));
                g2d.drawString(node.getLocationName(), cx - 50, cy - radius - 5);

                g2d.setFont(new Font("Monospaced", Font.PLAIN, 10));
                g2d.setColor(Color.GRAY);
                g2d.drawString(String.format("Y:%.2f F:%.2f", node.getEfficiencyYield(), node.getHumanFloorImpact()), cx - 45, cy + radius + 14);

                index++;
            }

            // Central Global Base Clock indicator display text
            g2d.setColor(new Color(255, 255, 255, 200));
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
            g2d.drawString("SCHUMANN RESONANCE HARMONIC REGULATOR: 7.83 HZ [LOCKED]", 20, 30);
        }
    }

    // Concrete AbstractTableModel encapsulating concurrent dataset queries safely
    private static class GridTableModel extends AbstractTableModel {
        private final String[] columns = {"NODE IDENTITY CHECKSUM", "SCOPE", "EFFICIENCY YIELD", "HUMAN FLOOR IMPACT", "SYSTEM STATUS"};
        private List<GridNode> dataset;

        public GridTableModel(List<GridNode> initialData) {
            this.dataset = initialData;
        }

        public void refreshData(List<GridNode> freshData) {
            this.dataset = freshData;
            fireTableDataChanged();
        }

        @Override public int getRowCount() { return dataset.size(); }
        @Override public int getColumnCount() { return columns.length; }
        @Override public String getColumnName(int col) { return columns[col]; }

        @Override
        public Object getValueAt(int rowIndex, int columnIndex) {
            GridNode node = dataset.get(rowIndex);
            return switch (columnIndex) {
                case 0 -> node.getLocationName() + " (" + node.getNodeCid().toString().substring(0,8) + ")";
                case 1 -> node.getScope().toString();
                case 2 -> String.format("%.2f%%", node.getEfficiencyYield() * 100);
                case 3 -> String.format("%+.2f", node.getHumanFloorImpact());
                case 4 -> node.getStatus().toString();
                default -> null;
            };
        }
    }
}
