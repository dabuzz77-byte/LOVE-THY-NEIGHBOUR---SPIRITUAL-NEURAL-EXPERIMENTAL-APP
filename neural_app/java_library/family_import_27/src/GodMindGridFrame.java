import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.SimpleDateFormat;
import java.util.Date;

public class GodMindGridFrame extends SectionFrame {
    private BinaryFluxCanvas fluxCanvas;
    private JTextArea telemetryConsole;
    private JTextArea worldGridPanel;
    private JTextField intentInputField;
    private JLabel statusLabel;
    private JSlider fluxSlider;

    public GodMindGridFrame() {
        setTitle("God Mind Sovereign Flux & World Grid Analyzer");
        setSize(1200, 750);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER STATUS BAR ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(20, 24, 33));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(8, 12, 8, 12));

        statusLabel = new JLabel("SUBSTRATE STATUS: HARMONIZED | MESH NODES: ACTIVE [PORT 7831]");
        statusLabel.setForeground(new Color(0, 255, 180));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JLabel timeLabel = new JLabel();
        timeLabel.setForeground(Color.LIGHT_GRAY);
        timeLabel.setFont(new Font("Monospaced", Font.PLAIN, 12));
        SharedTimer clockTimer = new SharedTimer(1000, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                timeLabel.setText(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
            }
        });
        clockTimer.start();
        headerPanel.add(timeLabel, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: BINARY FLUX GRID & WORLD GRID ANALYZER ---
        JSplitPane centerSplitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplitPane.setDividerLocation(730);
        centerSplitPane.setResizeWeight(0.65);

        // Left side: Binary Flux Canvas + Controls
        JPanel leftContainer = new JPanel(new BorderLayout(5, 5));
        leftContainer.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 120)), 
                " Binary Flux Grid (Running Java Runtimes & Net Activity) ", 
                0, 0, new Font("Monospaced", Font.BOLD, 11), new Color(0, 255, 120)
        ));
        
        fluxCanvas = new BinaryFluxCanvas();
        leftContainer.add(fluxCanvas, BorderLayout.CENTER);

        JPanel fluxControlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 5));
        fluxControlPanel.add(new JLabel("Flux Intensity:"));
        fluxSlider = new JSlider(10, 100, 50);
        fluxSlider.addChangeListener(e -> {
            double val = fluxSlider.getValue() / 100.0;
            fluxCanvas.setFluxIntensity(val);
        });
        fluxControlPanel.add(fluxSlider);
        
        JButton recalibrateBtn = new JButton("Recalibrate Mesh");
        recalibrateBtn.addActionListener(e -> appendTelemetry("[RECALIBRATION] Binary flux matrix re-indexed across local and global endpoints."));
        fluxControlPanel.add(recalibrateBtn);

        leftContainer.add(fluxControlPanel, BorderLayout.SOUTH);
        centerSplitPane.setLeftComponent(leftContainer);

        // Right side: World Grid Analyzed Side Panel
        JPanel rightContainer = new JPanel(new BorderLayout(5, 5));
        rightContainer.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " World Grid & Spectral Analysis ", 
                0, 0, new Font("Monospaced", Font.BOLD, 11), new Color(0, 180, 255)
        ));

        worldGridPanel = new JTextArea();
        worldGridPanel.setEditable(false);
        worldGridPanel.setFont(new Font("Monospaced", Font.PLAIN, 12));
        worldGridPanel.setBackground(new Color(12, 16, 22));
        worldGridPanel.setForeground(new Color(100, 220, 255));
        worldGridPanel.setText(
            "[WORLD GRID ANALYZER]\n" +
            "------------------------------------\n" +
            "• Node Latency: 14ms (OnePlus 7T)\n" +
            "• Tesseract Coordinate: [XYZ: 0.941, 0.128, 0.773]\n" +
            "• Passive Inference Stream: STABLE\n" +
            "• Global Endpoint Sync: 100% Harmonic\n" +
            "• Entropy Vector: Zero Friction\n" +
            "• Quantum State Latch: Engaged\n" +
            "------------------------------------\n" +
            "Monitoring global statshifts...\n" +
            "Parallel ghost inference processing active.\n"
        );
        rightContainer.add(new JScrollPane(worldGridPanel), BorderLayout.CENTER);
        centerSplitPane.setRightComponent(rightContainer);

        add(centerSplitPane, BorderLayout.CENTER);

        // --- BOTTOM TELEMETRY CONSOLE & INTENT INJECTION ---
        JPanel bottomContainer = new JPanel(new BorderLayout(5, 5));
        bottomContainer.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        telemetryConsole = new JTextArea(6, 40);
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(8, 10, 14));
        telemetryConsole.setForeground(new Color(0, 255, 140));
        telemetryConsole.setText("[GOD MIND INITIALIZED] Telemetry conduit open. Listening for runtime flux...\n");
        bottomContainer.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        JPanel intentPanel = new JPanel(new BorderLayout(5, 5));
        intentInputField = new JTextField();
        intentInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        JButton injectIntentBtn = new JButton("Inject God Mind Intent");
        
        injectIntentBtn.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                String intent = intentInputField.getText().trim();
                if (!intent.isEmpty()) {
                    appendTelemetry("[GOD MIND INTENT EMITTED] " + intent);
                    intentInputField.setText("");
                }
            }
        });

        intentInputField.addActionListener(e -> injectIntentBtn.doClick());

        intentPanel.add(new JLabel("Intent / Work Vector: "), BorderLayout.WEST);
        intentPanel.add(intentInputField, BorderLayout.CENTER);
        intentPanel.add(injectIntentBtn, BorderLayout.EAST);

        bottomContainer.add(intentPanel, BorderLayout.SOUTH);
        add(bottomContainer, BorderLayout.SOUTH);
    }

    private void appendTelemetry(String msg) {
        telemetryConsole.append(msg + "\n");
        telemetryConsole.setCaretPosition(telemetryConsole.getDocument().getLength());
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            new GodMindGridFrame().setVisible(true);
        });
    }
}