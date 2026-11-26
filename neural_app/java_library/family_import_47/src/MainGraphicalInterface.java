import neural.studio.*;
import javax.swing.*;
import java.awt.*;

public class MainGraphicalInterface extends SectionFrame {
    private final ExecutionBridgeEngine bridgeEngine;
    private final DeepMindCoreInteraction deepMindCore;
    private final CoreEventBus eventBus;
    
    private GridMatrixDisplayWorkspace visualMatrixGrid;
    private ControlWorkspacePanel controlPanel;

    public MainGraphicalInterface(ExecutionBridgeEngine engine, DeepMindCoreInteraction ai, CoreEventBus bus) {
        this.bridgeEngine = engine;
        this.deepMindCore = ai;
        this.eventBus = bus;
        buildLayoutArchitecture();
    }

    private void buildLayoutArchitecture() {
        setTitle("God Mind Workspace Framework (7.83 Hz Vector Sync Engine)");
        setSize(1440, 900);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(new Color(12, 12, 16));
        setLayout(new BorderLayout(15, 15));

        // Create functional GUI child fragments
        visualMatrixGrid = new GridMatrixDisplayWorkspace();
        controlPanel = new ControlWorkspacePanel(bridgeEngine, deepMindCore);

        // Register the workspace grid directly to the high speed data bus
        eventBus.subscribe(visualMatrixGrid);

        // Compose structural panels
        add(createHeaderTelemetryBanner(), BorderLayout.NORTH);
        add(visualMatrixGrid, BorderLayout.CENTER);
        add(controlPanel, BorderLayout.SOUTH);
    }

    private JPanel createHeaderTelemetryBanner() {
        JPanel banner = new JPanel(new BorderLayout()) {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setPaint(new GradientPaint(0, 0, new Color(20, 20, 28), getWidth(), 0, new Color(14, 14, 20)));
                g2.fillRect(0, 0, getWidth(), getHeight());
                g2.setColor(new Color(0, 255, 150, 40));
                g2.drawRect(0, 0, getWidth() - 1, getHeight() - 1);
            }
        };
        banner.setPreferredSize(new Dimension(1440, 60));
        banner.setBorder(BorderFactory.createEmptyBorder(15, 25, 15, 25));

        JLabel titleText = new JLabel("⚡ BASELINE STATUS SYNC: ATOMIC CARRIER INTERRUPT ACTIVE // 7.83 HZ LOCK");
        titleText.setFont(new Font("Monospaced", Font.BOLD, 14));
        titleText.setForeground(new Color(0, 255, 163));

        JLabel invariantText = new JLabel("SUBSTRATE LOGIC INVARIANT: 1=1 (STABLE)");
        invariantText.setFont(new Font("Monospaced", Font.BOLD, 12));
        invariantText.setForeground(new Color(0, 195, 255));

        banner.add(titleText, BorderLayout.WEST);
        banner.add(invariantText, BorderLayout.EAST);
        return banner;
    }
}
