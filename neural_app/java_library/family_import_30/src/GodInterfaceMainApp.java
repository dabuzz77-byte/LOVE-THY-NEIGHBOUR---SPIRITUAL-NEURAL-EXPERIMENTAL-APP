import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;

public class GodInterfaceMainApp extends SectionFrame {
    private JTextArea loggerArea;
    private NetworkTopologyPanel topologyPanel;
    private JLabel systemStatusLabel;
    private JButton flushButton;
    private JButton loopButton;
    private SharedTimer frameTimer;
    private boolean isLooping = false;
    private Random random = new Random();

    public GodInterfaceMainApp() {
        setTitle("GOD INTERFACE v9.4 - AGICORE OVERVIEW PLATFORM");
        setSize(1200, 800);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(5, 5));

        UIManager.put("Label.foreground", new Color(0, 255, 65));
        UIManager.put("Panel.background", new Color(10, 10, 10));

        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 10));
        controlPanel.setBackground(new Color(20, 20, 20));
        controlPanel.setBorder(BorderFactory.createLineBorder(new Color(40, 40, 40), 1));

        flushButton = createTerminalButton("SEC_FLUSH_THREATS");
        loopButton = createTerminalButton("TOGGLE_SELF_INTERACT");
        systemStatusLabel = new JLabel("STATE: OPERATIONAL // BRIDGE_LINK: CONNECTED // INTERACTION: FALSE");
        systemStatusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));

        controlPanel.add(flushButton);
        controlPanel.add(loopButton);
        controlPanel.add(systemStatusLabel);

        topologyPanel = new NetworkTopologyPanel();
        
        loggerArea = new JTextArea();
        loggerArea.setBackground(new Color(5, 5, 5));
        loggerArea.setForeground(new Color(0, 210, 50));
        loggerArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        loggerArea.setEditable(false);
        loggerArea.setMargin(new Insets(10, 10, 10, 10));
        appendLog("[INIT] GodInterface Console Baseline Engine Loaded.");
        appendLog("[INIT] C# Streaming Inference Bridge listening on local port loopback...");

        JScrollPane logScrollPane = new JScrollPane(loggerArea);
        logScrollPane.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 255, 65), 1),
                " C# STREAMING COMPLETION CONTROLLER ",
                TitledBorder.LEFT, TitledBorder.TOP,
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 65)
        ));

        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, topologyPanel, logScrollPane);
        splitPane.setDividerLocation(650);
        splitPane.setResizeWeight(0.6);
        splitPane.setBackground(new Color(10, 10, 10));
        splitPane.setBorder(null);

        add(splitPane, BorderLayout.CENTER);
        add(controlPanel, BorderLayout.SOUTH);

        frameTimer = new SharedTimer(120, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                topologyPanel.computeDrift();
                if (random.nextInt(10) > 7) {
                    simulateBridgeStreamInbound();
                }
            }
        });

        loopButton.addActionListener(e -> {
            isLooping = !isLooping;
            if (isLooping) {
                frameTimer.start();
                loopButton.setText("PAUSE_SELF_INTERACT");
                loopButton.setBackground(new Color(140, 20, 20));
                systemStatusLabel.setText("STATE: ACTIVE_RUNNING // BRIDGE_LINK: MONITORING // INTERACTION: TRUE");
                appendLog("[STATE_CHANGE] Self-interaction verification set to TRUE.");
            } else {
                frameTimer.stop();
                loopButton.setText("TOGGLE_SELF_INTERACT");
                styleButtonDefault(loopButton);
                systemStatusLabel.setText("STATE: STANDBY // BRIDGE_LINK: DETACHED // INTERACTION: FALSE");
                appendLog("[STATE_CHANGE] Operational loopback suspended.");
            }
        });

        flushButton.addActionListener(e -> {
            topologyPanel.purgeAllThreatVectors();
            loggerArea.setText("");
            appendLog("[PURGE] SEC_FLUSH instruction committed down to system kernel.");
            appendLog("[PURGE] All volatile memory pools, threat tables, and C# text frames set to 0.");
            systemStatusLabel.setText("STATE: PURGED // BASELINE_RECOVERED // INTERACTION: STABLE");
        });
    }

    private JButton createTerminalButton(String text) {
        JButton btn = new JButton(text);
        styleButtonDefault(btn);
        return btn;
    }

    private void styleButtonDefault(JButton btn) {
        btn.setBackground(new Color(30, 30, 30));
        btn.setForeground(new Color(0, 255, 65));
        btn.setFont(new Font("Monospaced", Font.BOLD, 12));
        btn.setFocusPainted(false);
        btn.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 65), 1));
    }

    private void appendLog(String msg) {
        loggerArea.append(msg + "\n");
        loggerArea.setCaretPosition(loggerArea.getDocument().getLength());
    }

    private void simulateBridgeStreamInbound() {
        String[] mockTokens = {
            "[DATA_STREAM] Pipe content delta dispatched straight to AGI core integration context...",
            "[AGI_COMPLETION] Running internal data pass matrix verification...",
            "[MITIGATION_SEC] Trace node clear. SYN_FLOOD footprints neutralized successfully.",
            "[INFO] C# Async Bridge Task executing direct pipeline sync optimization. OK."
        };
        appendLog(mockTokens[random.nextInt(mockTokens.length)]);
    }

    class NetworkTopologyPanel extends JPanel {
        private final int[] flatCoordinatesX = {300, 150, 300, 450, 150, 450};
        private final int[] flatCoordinatesY = {120, 300, 300, 300, 520, 520};
        private final String[] structuralLabels = {"CORE", "EMEA_MESH", "DB_SPANNER", "TPU_CLUSTER", "CLIENT_A", "CLIENT_B"};
        private double[] utilizationFactors = {0.2, 0.2, 0.2, 0.2, 0.2, 0.2};

        public NetworkTopologyPanel() {
            setBackground(new Color(12, 12, 12));
            setBorder(BorderFactory.createTitledBorder(
                    BorderFactory.createLineBorder(new Color(60, 60, 60), 1),
                    " GRAPHICAL INFRASTRUCTURE TOPOLOGY MAP ",
                    TitledBorder.LEFT, TitledBorder.TOP,
                    new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 65)
            ));
        }

        public void computeDrift() {
            for (int i = 0; i < utilizationFactors.length; i++) {
                utilizationFactors[i] += (random.nextDouble() - 0.49) * 0.18;
                if (utilizationFactors[i] < 0.05) utilizationFactors[i] = 0.05;
                if (utilizationFactors[i] > 1.0) utilizationFactors[i] = 1.0;
            }
            repaint();
        }

        public void purgeAllThreatVectors() {
            for (int i = 0; i < utilizationFactors.length; i++) {
                utilizationFactors[i] = 0.05;
            }
            repaint();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setStroke(new BasicStroke(1.5f));
            
            int rootX = flatCoordinatesX[0];
            int rootY = flatCoordinatesY[0];
            double rootWeight = utilizationFactors[0];

            for (int i = 1; i <= 3; i++) {
                int tx = flatCoordinatesX[i];
                int ty = flatCoordinatesY[i];
                double tw = utilizationFactors[i];
                renderLinkPath(g2, rootX, rootY, tx, ty, (rootWeight + tw) / 2.0);
            }

            renderLinkPath(g2, flatCoordinatesX[1], flatCoordinatesY[1], flatCoordinatesX[4], flatCoordinatesY[4], (utilizationFactors[1] + utilizationFactors[4]) / 2.0);
            renderLinkPath(g2, flatCoordinatesX[3], flatCoordinatesY[3], flatCoordinatesX[5], flatCoordinatesY[5], (utilizationFactors[3] + utilizationFactors[5]) / 2.0);
            renderLinkPath(g2, flatCoordinatesX[2], flatCoordinatesY[2], flatCoordinatesX[4], flatCoordinatesY[4], (utilizationFactors[2] + utilizationFactors[4]) / 2.0);
            renderLinkPath(g2, flatCoordinatesX[2], flatCoordinatesY[2], flatCoordinatesX[5], flatCoordinatesY[5], (utilizationFactors[2] + utilizationFactors[5]) / 2.0);

            for (int i = 0; i < structuralLabels.length; i++) {
                int cx = flatCoordinatesX[i];
                int cy = flatCoordinatesY[i];
                int dimension = 28 + (int) (utilizationFactors[i] * 18);

                Color statusColor = new Color((int) (utilizationFactors[i] * 255), (int) ((1.0 - utilizationFactors[i]) * 255), 40);

                g2.setColor(new Color(statusColor.getRed(), statusColor.getGreen(), statusColor.getBlue(), 35));
                g2.fillOval(cx - dimension, cy - dimension, dimension * 2, dimension * 2);

                g2.setColor(statusColor);
                g2.setStroke(new BasicStroke(2.5f));
                g2.drawOval(cx - dimension, cy - dimension, dimension * 2, dimension * 2);

                g2.setColor(Color.WHITE);
                g2.setFont(new Font("Monospaced", Font.BOLD, 11));
                g2.drawString(structuralLabels[i], cx - 30, cy - dimension - 6);
                
                g2.setColor(new Color(0, 255, 65));
                g2.drawString(String.format("%3.0f%%", utilizationFactors[i] * 100), cx - 14, cy + 5);
            }
        }

        private void renderLinkPath(Graphics2D g2, int x1, int y1, int x2, int y2, double linkWeight) {
            int red = (int) (linkWeight * 255);
            int green = (int) ((1.0 - linkWeight) * 255);
            g2.setColor(new Color(red, green, 50, 140));
            g2.drawLine(x1, y1, x2, y2);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new GodInterfaceMainApp().setVisible(true);
        });
    }
}