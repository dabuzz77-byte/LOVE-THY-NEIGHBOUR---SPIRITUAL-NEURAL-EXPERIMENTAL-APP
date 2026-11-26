import javax.swing.*;
import java.awt.*;

public class ControlWorkspacePanel extends JPanel {
    private final ExecutionBridgeEngine engine;
    private final DeepMindCoreInteraction deepMindCore;
    private JTextArea codeAreaInput;
    private JLabel rewardStatusMetric;

    public ControlWorkspacePanel(ExecutionBridgeEngine engine, DeepMindCoreInteraction ai) {
        this.engine = engine;
        this.deepMindCore = ai;
        configurePanelLayout();
    }

    private void configurePanelLayout() {
        setBackground(new Color(18, 18, 26));
        setLayout(new BorderLayout(15, 10));
        setBorder(BorderFactory.createEmptyBorder(15, 20, 20, 20));

        // Substrate workspace header
        JLabel workspaceLabel = new JLabel("⚙️ INTERACTIVE INJECTION LAYER / TENSOR DATA PAYLOAD INPUT ENGINE");
        workspaceLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        workspaceLabel.setForeground(Color.LIGHT_GRAY);
        add(workspaceLabel, BorderLayout.NORTH);

        // Core text panel area configuration
        codeAreaInput = new JTextArea(
            "{\n" +
            "  \"target_resonance_hz\": 7.83,\n" +
            "  \"algorithmic_debt_flush\": true,\n" +
            "  \"eco_floor_optimization_weight\": 1.00,\n" +
            "  \"system_parity_invariant\": true\n" +
            "}"
        );
        codeAreaInput.setFont(new Font("Monospaced", Font.PLAIN, 12));
        codeAreaInput.setBackground(new Color(10, 10, 14));
        codeAreaInput.setForeground(new Color(0, 220, 255));
        codeAreaInput.setCaretColor(Color.WHITE);
        codeAreaInput.setBorder(BorderFactory.createLineBorder(new Color(40, 40, 55), 1));
        
        JScrollPane scrollPane = new JScrollPane(codeAreaInput);
        scrollPane.setPreferredSize(new Dimension(800, 110));
        add(scrollPane, BorderLayout.CENTER);

        // Controls action buttons array block
        JPanel eastActionsArea = new JPanel(new GridLayout(2, 1, 0, 10));
        eastActionsArea.setOpaque(false);

        JButton executeButton = new JButton("COMPILE & RUN DATA STREAM") {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setPaint(new GradientPaint(0, 0, new Color(41, 128, 185), getWidth(), 0, new Color(34, 153, 84)));
                g2.fillRoundRect(0, 0, getWidth(), getHeight(), 8, 8);
                g2.setColor(Color.WHITE);
                g2.setFont(new Font("Monospaced", Font.BOLD, 12));
                FontMetrics fm = g2.getFontMetrics();
                int tx = (getWidth() - fm.stringWidth(getText())) / 2;
                int ty = (getHeight() + fm.getAscent() - fm.getDescent()) / 2;
                g2.drawString(getText(), tx, ty);
            }
        };
        executeButton.setPreferredSize(new Dimension(320, 45));
        executeButton.setBorderPainted(false);
        executeButton.setContentAreaFilled(false);
        executeButton.setFocusPainted(false);
        
        executeButton.addActionListener(e -> {
            String extractedInput = codeAreaInput.getText();
            engine.setPayload(extractedInput);
            double updatedScore = deepMindCore.getCurrentRewardFactor();
            rewardStatusMetric.setText(String.format("DEEPMIND PARITY ACCURACY OPTIMIZATION REWARD INDEX: %.4f", updatedScore));
            System.out.println("[PARSER INTERRUPT] New code payload payload compiled into runtime threads.");
        });

        rewardStatusMetric = new JLabel("DEEPMIND PARITY ACCURACY OPTIMIZATION REWARD INDEX: 1.0000");
        rewardStatusMetric.setFont(new Font("Monospaced", Font.BOLD, 11));
        rewardStatusMetric.setForeground(new Color(241, 196, 15));

        eastActionsArea.add(executeButton);
        eastActionsArea.add(rewardStatusMetric);

        add(eastActionsArea, BorderLayout.EAST);
    }
}
