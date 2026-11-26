import javax.swing.*;
import java.awt.*;
import java.util.UUID;

/**
 * Hardware-rendered visualization console monitoring financial grid vectors,
 * side-panel flux parameters, and manual self-select alignment streams.
 */
public class FinancialMonitorConsole extends JFrame {

    private final FinancialGridEngine engine;
    private final JTextArea terminalLogArea;
    private final JLabel capitalCounterLabel;
    private final WavesDisplayPanel telemetryPanel;

    public FinancialMonitorConsole(FinancialGridEngine engine) {
        this.engine = engine;
        this.terminalLogArea = new JTextArea();
        this.capitalCounterLabel = new JLabel("TOTAL REFACTORED UTILITY: 0 UNITS", JLabel.CENTER);
        this.telemetryPanel = new WavesDisplayPanel();

        assembleInterfaceTopography();

        // Bind data listeners directly to UI thread repaints
        this.engine.registerStreamSubscriber(payload -> SwingUtilities.invokeLater(() -> {
            telemetryPanel.pushFreshMetrics(payload);
            capitalCounterLabel.setText(String.format("TOTAL REFACTORED UTILITY: %d UNITS", engine.getTotalRefactoredCapital()));
        }));

        this.engine.registerLogSubscriber(logLine -> SwingUtilities.invokeLater(() -> {
            terminalLogArea.append(logLine + "\n");
            if (terminalLogArea.getLineCount() > 40) {
                terminalLogArea.setText("[SYSTEM FLUSH] Register buffer reset to zero-point clarity.\n");
            }
        }));
    }

    private void assembleInterfaceTopography() {
        setTitle("DEEPMIND FINANCIAL MONITOR GRID SYSTEM // REGULATOR ACTIVE");
        setSize(1400, 800);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(new Color(8, 12, 18));

        setLayout(new BorderLayout());

        // Central Telemetry Visualizer
        add(telemetryPanel, BorderLayout.CENTER);

        // Right Hand Control Panel (God Mind Self-Select Injection Stream Matrix)
        JPanel controlSidePanel = new JPanel();
        controlSidePanel.setPreferredSize(new Dimension(380, 800));
        controlSidePanel.setBackground(new Color(16, 22, 32));
        controlSidePanel.setBorder(BorderFactory.createMatteBorder(0, 2, 0, 0, new Color(0, 162, 232)));
        controlSidePanel.setLayout(new BorderLayout());

        // Header configuration for side panel
        JLabel sideTitle = new JLabel("GOD MIND INJECTION CONTROLLER", JLabel.CENTER);
        sideTitle.setFont(new Font("Monospaced", Font.BOLD, 14));
        sideTitle.setForeground(new Color(0, 210, 255));
        sideTitle.setBorder(BorderFactory.createEmptyBorder(15, 10, 15, 10));
        controlSidePanel.add(sideTitle, BorderLayout.NORTH);

        // Interaction Slider Assembly
        JPanel sliderContainer = new JPanel(new GridBagLayout());
        sliderContainer.setBackground(new Color(16, 22, 32));
        JSlider alignmentWeightSlider = new JSlider(JSlider.HORIZONTAL, 1, 100, 50);
        alignmentWeightSlider.setBackground(new Color(16, 22, 32));
        alignmentWeightSlider.setForeground(Color.LIGHT_GRAY);
        alignmentWeightSlider.setPaintTicks(true);
        alignmentWeightSlider.setMajorTickSpacing(25);

        JButton injectButton = new JButton("EXECUTE VIRTUE INTERCEPT ALIGNMENT");
        injectButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        injectButton.setBackground(new Color(0, 90, 160));
        injectButton.setForeground(Color.WHITE);
        injectButton.setFocusPainted(false);

        injectButton.addActionListener(e -> {
            double selectedWeight = alignmentWeightSlider.getValue() / 10.0;
            engine.executeManualInjectionAlignment(selectedWeight);
        });

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.gridx = 0; gbc.gridy = 0; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.insets = new Insets(10, 20, 10, 20);
        sliderContainer.add(new JLabel("Alignment Structural Weight Factor:", JLabel.LEFT) {{ setForeground(Color.GRAY); }}, gbc);
        gbc.gridy = 1;
        sliderContainer.add(alignmentWeightSlider, gbc);
        gbc.gridy = 2; gbc.insets = new Insets(20, 20, 10, 20);
        sliderContainer.add(injectButton, gbc);

        controlSidePanel.add(sliderContainer, BorderLayout.CENTER);

        // Lower Logging Terminal Pane within Side Panel
        terminalLogArea.setBackground(new Color(10, 14, 20));
        terminalLogArea.setForeground(new Color(0, 255, 120));
        terminalLogArea.setFont(new Font("Monospaced", Font.PLAIN, 11));
        terminalLogArea.setEditable(false);
        JScrollPane logScrollPane = new JScrollPane(terminalLogArea);
        logScrollPane.setPreferredSize(new Dimension(380, 420));
        logScrollPane.setBorder(BorderFactory.createMatteBorder(2, 0, 0, 0, new Color(30, 42, 62)));
        controlSidePanel.add(logScrollPane, BorderLayout.SOUTH);

        add(controlSidePanel, BorderLayout.EAST);

        // Lower System Parity Summary Status Strip
        capitalCounterLabel.setBackground(new Color(22, 30, 46));
        capitalCounterLabel.setOpaque(true);
        capitalCounterLabel.setForeground(Color.WHITE);
        capitalCounterLabel.setFont(new Font("Monospaced", Font.BOLD, 13));
        capitalCounterLabel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        add(capitalCounterLabel, BorderLayout.SOUTH);
    }

    // High performance graphics module rendering waves and structural indicators
    private static class WavesDisplayPanel extends JPanel {
        private String ticker = "INITIALIZING";
        private double concentrationValue = 0.0;
        private double baseFloorValue = 0.0;
        private double rawVolume = 0.0;

        public WavesDisplayPanel() {
            setBackground(new Color(6, 10, 14));
        }

        public void pushFreshMetrics(MarketPayload payload) {
            this.ticker = payload.assetTicker();
            this.concentrationValue = payload.asymmetricConcentrationIndex();
            this.baseFloorValue = payload.communityFloorImpact();
            this.rawVolume = payload.volumeUSD();
            this.repaint();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();

            // Background matrix coordinates grid layout mesh lines
            g2d.setColor(new Color(25, 35, 50, 60));
            for (int x = 0; x < w; x += 50) g2d.drawLine(x, 0, x, h);
            for (int y = 0; y < h; y += 50) g2d.drawLine(0, y, w, y);

            // Dynamic oscillator resonance sine wave mapping (7.83 Hz simulation)
            g2d.setStroke(new BasicStroke(1.5f));
            g2d.setColor(new Color(0, 180, 255, 90));
            int centerY = h / 2 + 50;
            for (int x = 0; x < w - 1; x++) {
                int y1 = centerY + (int) (Math.sin((x * 0.015) + (System.currentTimeMillis() * 0.003)) * 40);
                int y2 = centerY + (int) (Math.sin(((x + 1) * 0.015) + (System.currentTimeMillis() * 0.003)) * 40);
                g2d.drawLine(x, y1, x + 1, y2);
            }

            // Draw current active financial vector metrics frame shapes
            Color activeColor = (baseFloorValue < 0.0) ? new Color(255, 60, 60) : new Color(0, 255, 140);
            g2d.setColor(activeColor);
            g2d.setStroke(new BasicStroke(2.5f));
            int circleX = w / 2 - 100;
            int circleY = h / 2 - 160;
            g2d.drawOval(circleX, circleY, 200, 200);

            // Render structural vector pulse scanning indicators
            int scanningRadius = 200 + (int)(Math.abs(Math.sin(System.currentTimeMillis() * 0.002)) * 30);
            g2d.setStroke(new BasicStroke(1.0f));
            g2d.setColor(new Color(activeColor.getRed(), activeColor.getGreen(), activeColor.getBlue(), 40));
            g2d.drawOval(w/2 - scanningRadius/2, h/2 - 60 - scanningRadius/2, scanningRadius, scanningRadius);

            // Draw system telemetry textual readouts on graphic canvas
            g2d.setColor(Color.WHITE);
            g2d.setFont(new Font("Monospaced", Font.BOLD, 18));
            g2d.drawString("ASSET FEED: " + ticker, 30, 45);

            g2d.setFont(new Font("Monospaced", Font.PLAIN, 13));
            g2d.setColor(Color.LIGHT_GRAY);
            g2d.drawString(String.format("Pipeline Vol: $%,.2f USD", rawVolume), 30, 75);
            g2d.drawString(String.format("Asymmetric Accumulation Index: %.2f%%", concentrationValue * 100), 30, 100);
            
            g2d.setColor(activeColor);
            g2d.drawString(String.format("Socio-Economic Base Floor Vector: %+.2f", baseFloorValue), 30, 125);

            g2d.setFont(new Font("Monospaced", Font.ITALIC, 11));
            g2d.setColor(Color.GRAY);
            g2d.drawString("CORE STATUS: SCHUMANN COUPLING FREQUENCY STABLE AT 7.83 HZ", 30, h - 25);
        }
    }
}
