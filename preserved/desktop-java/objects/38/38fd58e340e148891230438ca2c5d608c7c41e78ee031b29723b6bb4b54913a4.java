

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.DecimalFormat;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * Graphical representation and controller for the Microcosmic Orbit Engine.
 * Implements an interactive Java Swing Dashboard for state tracking.
 */
public class MicrocosmicOrbitDashboard extends JFrame {

    // Core Logic Engine References
    private double floor0VaultBalance = 10000.0;
    private double totalAbsorbedEnergy = 0.0;
    private int cycleCount = 0;
    private boolean isCoherent = true;

    // Visual UI Components
    private JLabel balanceLabel;
    private JLabel energyLabel;
    private JLabel coherenceLabel;
    private JLabel statusLabel;
    private JTextArea logTextArea;
    private JProgressBar vaultProgressBar;
    private JComboBox<String> velocityCombo;

    private final DecimalFormat currencyFormat = new DecimalFormat("£#,##0.00");
    private final DecimalFormat energyFormat = new DecimalFormat("#,##0.00 Units");
    private final DateTimeFormatter timeFormatter = DateTimeFormatter.ofPattern("HH:mm:ss");

    public MicrocosmicOrbitDashboard() {
        // Initialize Window Configuration
        setTitle("Bi-Ter-Quantum Inference Controller");
        setSize(700, 500);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        // Create UI Sub-panels
        add(createHeaderPanel(), BorderLayout.NORTH);
        add(createTelemetryDashboard(), BorderLayout.CENTER);
        add(createControlPanel(), BorderLayout.SOUTH);
    }

    private JPanel createHeaderPanel() {
        JPanel panel = new JPanel();
        panel.setBackground(new Color(25, 30, 45));
        JLabel title = new JLabel("CONDUIT MATRIX REGISTRY // CURRENT ACTIVE RUNTIME");
        title.setForeground(Color.CYAN);
        title.setFont(new Font("Monospaced", Font.BOLD, 16));
        panel.add(title);
        return panel;
    }

    private JPanel createTelemetryDashboard() {
        JPanel mainGrid = new JPanel(new GridLayout(1, 2, 10, 10));
        mainGrid.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Left Panel: Metric Indicators
        JPanel metricPanel = new JPanel(new GridLayout(4, 1, 5, 5));
        metricPanel.setBorder(BorderFactory.createTitledBorder("System Indicators"));

        balanceLabel = new JLabel("Floor 0 Vault: " + currencyFormat.format(floor0VaultBalance));
        balanceLabel.setFont(new Font("Monospaced", Font.BOLD, 14));
        
        energyLabel = new JLabel("Absorbed Volatility: " + energyFormat.format(totalAbsorbedEnergy));
        energyLabel.setFont(new Font("Monospaced", Font.PLAIN, 13));

        coherenceLabel = new JLabel("Core Coherence: TRUE (1)");
        coherenceLabel.setForeground(new Color(46, 204, 113));
        coherenceLabel.setFont(new Font("Monospaced", Font.BOLD, 13));

        statusLabel = new JLabel("Engine Status: IDLING_NOMINAL");
        statusLabel.setFont(new Font("Monospaced", Font.ITALIC, 13));

        metricPanel.add(balanceLabel);
        metricPanel.add(energyLabel);
        metricPanel.add(coherenceLabel);
        metricPanel.add(statusLabel);

        // Right Panel: Live Activity Monitor Log
        JPanel logPanel = new JPanel(new BorderLayout());
        logPanel.setBorder(BorderFactory.createTitledBorder("Telemetry Flux Stream"));

        logTextArea = new JTextArea();
        logTextArea.setBackground(Color.BLACK);
        logTextArea.setForeground(Color.GREEN);
        logTextArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        logTextArea.setEditable(false);
        
        JScrollPane scrollPane = new JScrollPane(logTextArea);
        logPanel.add(scrollPane, BorderLayout.CENTER);

        // Vault Capacity Progress Bar Layer
        vaultProgressBar = new JProgressBar(0, 50000);
        vaultProgressBar.setValue((int) floor0VaultBalance);
        vaultProgressBar.setStringPainted(true);
        vaultProgressBar.setForeground(new Color(41, 128, 185));
        logPanel.add(vaultProgressBar, BorderLayout.SOUTH);

        mainGrid.add(metricPanel);
        mainGrid.add(logPanel);
        return mainGrid;
    }

    private JPanel createControlPanel() {
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 10));
        controlPanel.setBorder(BorderFactory.createMatteBorder(1, 0, 0, 0, Color.LIGHT_GRAY));

        // Selector for input vectors
        JLabel modeLabel = new JLabel("Velocity Vector:");
        String[] options = {"max_roadrunner_velocity", "purified_taz_entropy", "tiny_tim_insulation"};
        velocityCombo = new JComboBox<>(options);

        // Trigger Action Button
        JButton runButton = new JButton("ACTUATE FLUX VECTOR");
        runButton.setFont(new Font("Tahoma", Font.BOLD, 12));
        runButton.setBackground(new Color(52, 152, 219));
        runButton.setOpaque(true);

        runButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                executeVisualCycle();
            }
        });

        controlPanel.add(modeLabel);
        controlPanel.add(velocityCombo);
        controlPanel.add(runButton);

        return controlPanel;
    }

    /**
     * Executes one discrete computation frame, altering local matrix metrics 
     * and outputting asynchronous text telemetry onto the active viewport window.
     */
    private void executeVisualCycle() {
        cycleCount++;
        String selectedMode = (String) velocityCombo.getSelectedItem();
        double incomingMagnitude = 500.0 + (Math.random() * 1500.0); // Generate variable force vector

        // Inversion math: extract utility capital to isolate vulnerabilities
        double convertedLiquidity = incomingMagnitude * 0.25;
        this.totalAbsorbedEnergy += incomingMagnitude;
        this.floor0VaultBalance += convertedLiquidity;

        // Update Text Indicators
        balanceLabel.setText("Floor 0 Vault: " + currencyFormat.format(floor0VaultBalance));
        energyLabel.setText("Absorbed Volatility: " + energyFormat.format(totalAbsorbedEnergy));
        statusLabel.setText("Engine Status: RUNTIME_COHERENCE_ENFORCED");
        
        // Update Visualization Metrics
        vaultProgressBar.setValue((int) floor0VaultBalance);

        // Append to Stream Viewport
        String timestamp = LocalTime.now().format(timeFormatter);
        logTextArea.append(String.format("[%s] [FRAME_%02d] Vector Actuated: %s\n", timestamp, cycleCount, selectedMode));
        logTextArea.append(String.format(" └── Converted Liquidity: +%s\n", currencyFormat.format(convertedLiquidity)));
        logTextArea.setCaretPosition(logTextArea.getDocument().getLength());
    }

    /**
     * Compilation Runtime Entry-point. Launches the Graphical Grid instance.
     */
    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new MicrocosmicOrbitDashboard().setVisible(true);
            }
        });
    }
}
