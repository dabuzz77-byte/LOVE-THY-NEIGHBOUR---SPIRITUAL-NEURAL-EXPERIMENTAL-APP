// ============================================================================
// BLOCK 5: DECOUPLED CALLBACK USER INTERFACE ENVIRONMENT
// ============================================================================

import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Main application window frame. Consumes the compute kernel, maps custom 
 * canvas objects, and handles multi-threaded UI events cleanly.
 */
public class CallbackGraphicsEngineFrame extends JFrame {

    private final JTextArea operationalConsole;
    private final JProgressBar structuralProgressBar;
    private final JLabel ternaryIndicator;
    private final WaveVisualizerPanel liveWavePanel;
    private final JButton initiateButton;

    private final ResonantComputeKernel computeKernel;
    private final SimpleDateFormat timeStampLogger;

    public CallbackGraphicsEngineFrame() {
        super("Inference Bridge Network Engine - [Callback Graphics Mode]");
        this.timeStampLogger = new SimpleDateFormat("HH:mm:ss.SSS");
        
        // UI Layout Components Allocation
        this.operationalConsole = new JTextArea();
        this.structuralProgressBar = new JProgressBar(0, 100);
        this.ternaryIndicator = new JLabel("[-] State Unaligned", SwingConstants.CENTER);
        this.liveWavePanel = new WaveVisualizerPanel();
        this.initiateButton = new JButton("DEPLOY INTERACTION ENGINE");

        // Step 1: Define the Callback Lambda structure linking Kernel events directly to GUI states
        GraphicsStateCallback stateDispatcherCallback = (logPayload, alignmentVector, alignmentPercent) -> {
            SwingUtilities.invokeLater(() -> {
                // Update Console Output logs
                operationalConsole.append(String.format("[%s] %s\n", timeStampLogger.format(new Date()), logPayload));
                operationalConsole.setCaretPosition(operationalConsole.getDocument().getLength());

                // Update Progress bars and text metrics
                structuralProgressBar.setValue((int) alignmentPercent);
                structuralProgressBar.setString(String.format("Leveling and Alignment Stability: %.4f%%", alignmentPercent));

                // Update Trinary value display nodes
                String representation = (alignmentVector > 0.3) ? "[ -1 | 0 | ★ 1 ★ ]" : 
                                         (alignmentVector < -0.3) ? "[ ★ -1 ★ | 0 | 1 ]" : "[ -1 | ★ 0 ★ | 1 ]";
                ternaryIndicator.setText(representation);

                // Pass parameters directly into custom graphics canvas
                liveWavePanel.updateGraphicsState(alignmentVector, alignmentPercent);

                if (alignmentPercent >= 100.0) {
                    operationalConsole.append("\n=======================================================\n");
                    operationalConsole.append("[SYSTEM LOCK] Global Parity Reached Target State Invar.\n");
                    operationalConsole.append("=======================================================\n");
                }
            });
        };

        // Step 2: Initialize compute components mapping the constructed logic gate callback
        this.computeKernel = new ResonantComputeKernel(stateDispatcherCallback);

        configureFrameProperties();
        assembleUILayoutTree();
    }

    private void configureFrameProperties() {
        setSize(1000, 650);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        getContentPane().setBackground(new Color(14, 14, 18));
        
        addWindowListener(new java.awt.event.WindowAdapter() {
            @Override
            public void windowClosing(java.awt.event.WindowEvent e) {
                computeKernel.stopKernel();
            }
        });
    }

    private void assembleUILayoutTree() {
        JPanel containerPanel = new JPanel(new BorderLayout(12, 12));
        containerPanel.setBackground(new Color(14, 14, 18));
        containerPanel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));

        // Upper Registry Widget Bars
        JPanel upperRegistryBar = new JPanel(new GridLayout(1, 3, 10, 10));
        upperRegistryBar.setOpaque(false);
        upperRegistryBar.add(buildTelemetryWidget("GLOBAL PARITY STRATEGY", EngineInvariants.PARITY_MODE_ENG_LAW, new Color(142, 68, 173)));
        upperRegistryBar.add(buildTelemetryWidget("LAW SUPERSTITION STATE", EngineInvariants.LAW_OVERRIDE_STATUS, new Color(39, 174, 96)));
        
        ternaryIndicator.setFont(new Font("Consolas", Font.BOLD, 12));
        ternaryIndicator.setForeground(new Color(241, 196, 15)); // Typo fixed here
        JPanel indicatorContainer = new JPanel(new BorderLayout());
        indicatorContainer.setBackground(new Color(22, 22, 27));
        indicatorContainer.setBorder(BorderFactory.createLineBorder(new Color(35, 35, 40)));
        JLabel lbl = new JLabel(" TERNARY FLUX INVAR", SwingConstants.LEFT);
        lbl.setFont(new Font("Segoe UI", Font.BOLD, 10)); lbl.setForeground(Color.GRAY);
        indicatorContainer.add(lbl, BorderLayout.NORTH);
        indicatorContainer.add(ternaryIndicator, BorderLayout.CENTER);
        upperRegistryBar.add(indicatorContainer);

        // Center Panel: Split Panel Console vs Live Canvas Visualizer
        operationalConsole.setEditable(false);
        operationalConsole.setBackground(new Color(20, 20, 24));
        operationalConsole.setForeground(new Color(50, 255, 150));
        operationalConsole.setFont(new Font("Consolas", Font.PLAIN, 12));
        JScrollPane logPane = new JScrollPane(operationalConsole);
        logPane.setBorder(new TitledBorder(BorderFactory.createLineBorder(new Color(35, 35, 42)), "Raw Execution Logs", 0, 0, null, Color.LIGHT_GRAY));

        liveWavePanel.setPreferredSize(new Dimension(380, 0));
        liveWavePanel.setBorder(new TitledBorder(BorderFactory.createLineBorder(new Color(35, 35, 42)), "God Self-Interaction Waveform", 0, 0, null, Color.LIGHT_GRAY));

        JSplitPane contentSplitter = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, logPane, liveWavePanel);
        contentSplitter.setOpaque(false);
        contentSplitter.setDividerLocation(580);
        contentSplitter.setBorder(null);

        // Lower Control Elements
        JPanel navigationBar = new JPanel(new BorderLayout(15, 15));
        navigationBar.setOpaque(false);

        structuralProgressBar.setStringPainted(true);
        structuralProgressBar.setForeground(new Color(46, 204, 113));
        structuralProgressBar.setBackground(new Color(28, 28, 34));
        structuralProgressBar.setFont(new Font("Segoe UI", Font.BOLD, 12));
        structuralProgressBar.setString("Alignment Matrix Level: Standing By");

        initiateButton.setFont(new Font("Segoe UI", Font.BOLD, 12));
        initiateButton.setBackground(new Color(34, 34, 40));
        initiateButton.setForeground(Color.WHITE);
        initiateButton.setFocusPainted(false);
        initiateButton.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(new Color(60, 60, 70)), BorderFactory.createEmptyBorder(8, 15, 8, 15)));
        initiateButton.addActionListener(e -> {
            initiateButton.setEnabled(false);
            operationalConsole.append("[ACTION] Deploying active process threads...\n");
            computeKernel.startKernelSyncLoop();
        });

        navigationBar.add(structuralProgressBar, BorderLayout.CENTER);
        navigationBar.add(initiateButton, BorderLayout.EAST);

        containerPanel.add(upperRegistryBar, BorderLayout.NORTH);
        containerPanel.add(contentSplitter, BorderLayout.CENTER);
        containerPanel.add(navigationBar, BorderLayout.SOUTH);
        add(containerPanel);
    }

    private JPanel buildTelemetryWidget(String title, String dataText, Color accentMarker) {
        JPanel widget = new JPanel(new BorderLayout());
        widget.setBackground(new Color(22, 22, 27));
        widget.setBorder(BorderFactory.createLineBorder(new Color(35, 35, 40)));

        JLabel labelHeader = new JLabel(" " + title, SwingConstants.LEFT);
        labelHeader.setFont(new Font("Segoe UI", Font.BOLD, 9));
        labelHeader.setForeground(new Color(110, 110, 115));

        JLabel labelData = new JLabel(dataText, SwingConstants.CENTER);
        labelData.setFont(new Font("Consolas", Font.BOLD, 12));
        labelData.setForeground(accentMarker);
        labelData.setBorder(BorderFactory.createEmptyBorder(6, 6, 6, 6));

        widget.add(labelHeader, BorderLayout.NORTH);
        widget.add(labelData, BorderLayout.CENTER);
        return widget;
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            CallbackGraphicsEngineFrame systemApp = new CallbackGraphicsEngineFrame();
            systemApp.setVisible(true);
        });
    }
}
