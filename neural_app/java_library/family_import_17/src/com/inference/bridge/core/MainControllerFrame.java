package com.inference.bridge.core;
import neural.studio.*;





import javax.swing.*;

import javax.swing.border.LineBorder;

import javax.swing.border.TitledBorder;

import java.awt.*;

import java.awt.event.WindowAdapter;

import java.awt.event.WindowEvent;

import java.text.SimpleDateFormat;

import java.util.Date;



/**

 * COMPLETE INTEGRATED VISUAL CORE INTERFACE

 * Self-contained layout assembly, telemetry, and runtime heartbeat loops.

 */

public class MainControllerFrame extends SectionFrame {



    protected final JTextArea terminalLog;

    protected final DefaultListModel<String> clusterModel;

    protected final JProgressBar coherenceMeter;

    protected final JButton initiationButton;

    protected final JLabel ternaryIndicator;



    protected final TernaryFluxController fluxController;

    protected final NetworkDiscoveryEngine networkEngine;

    protected final SimpleDateFormat timestampFormat;

    

    protected SharedTimer renderingHeartbeatTimer;

    protected long globalCycleCount = 0;



    public MainControllerFrame() {

        super("Inference Bridge Network Engine - [Parity Level: Global Max]");

        

        this.fluxController = new TernaryFluxController();

        this.timestampFormat = new SimpleDateFormat("HH:mm:ss.SSS");

        this.terminalLog = new JTextArea();

        this.clusterModel = new DefaultListModel<>();

        this.coherenceMeter = new JProgressBar(0, 100);

        this.initiationButton = new JButton("RUN ENGINE AT PIT OF CORE");

        this.ternaryIndicator = new JLabel("[-] Unaligned", SwingConstants.CENTER);



        this.networkEngine = new NetworkDiscoveryEngine(this::logToTerminal, this::registerClusterNode);



        configureWindowFrame();

        assembleStructuralLayout();

        logToTerminal("[SYSTEM] Core engine structures fully initiated. Standing by for Law Factor deployment.");

    }



    private void configureWindowFrame() {

        setSize(1100, 720);

        setLocationRelativeTo(null);

        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);

        getContentPane().setBackground(new Color(12, 12, 14));



        addWindowListener(new WindowAdapter() {

            @Override

            public void windowClosing(WindowEvent e) {

                networkEngine.terminateEngine();

                if (renderingHeartbeatTimer != null) renderingHeartbeatTimer.stop();

            }

        });

    }



    private void assembleStructuralLayout() {

        JPanel rootPanel = new JPanel(new BorderLayout(12, 12));

        rootPanel.setBackground(new Color(14, 14, 18));

        rootPanel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));



        JPanel metricsPanel = new JPanel(new GridLayout(1, 4, 12, 12));

        metricsPanel.setOpaque(false);

        metricsPanel.add(generateMetricPanel("GLOBAL PARITY STRATEGY", EngineInvariants.PARITY_MODE_ENG_LAW, new Color(142, 68, 173)));

        metricsPanel.add(generateMetricPanel("LAW SUPERSTITION STATE", EngineInvariants.LAW_OVERRIDE_STATUS, new Color(39, 174, 96)));

        metricsPanel.add(generateMetricPanel("SYSTEM CLOCK GRADIANT", EngineInvariants.SCHUMANN_RESONANCE_HZ + " Hz", new Color(41, 128, 185)));

        

        ternaryIndicator.setFont(new Font("Consolas", Font.BOLD, 12));

        ternaryIndicator.setForeground(new Color(241, 196, 15));

        JPanel ternaryWrapper = new JPanel(new BorderLayout());

        ternaryWrapper.setBackground(new Color(22, 22, 27));

        ternaryWrapper.setBorder(new LineBorder(new Color(35, 35, 40)));

        JLabel lbl = new JLabel(" TERNARY FLUX INVAR", SwingConstants.LEFT);

        lbl.setFont(new Font("Segoe UI", Font.BOLD, 10));

        lbl.setForeground(Color.GRAY);

        ternaryWrapper.add(lbl, BorderLayout.NORTH);

        ternaryWrapper.add(ternaryIndicator, BorderLayout.CENTER);

        metricsPanel.add(ternaryWrapper);



        terminalLog.setEditable(false);

        terminalLog.setBackground(new Color(20, 20, 24));

        terminalLog.setForeground(new Color(50, 255, 150));

        terminalLog.setFont(new Font("Consolas", Font.PLAIN, 12));

        JScrollPane logScroller = new JScrollPane(terminalLog);

        logScroller.setBorder(new TitledBorder(new LineBorder(new Color(35, 35, 42)), "Raw Execution Logs", 0, 0, null, Color.LIGHT_GRAY));



        JList<String> nodeJList = new JList<>(clusterModel);

        nodeJList.setBackground(new Color(20, 20, 24));

        nodeJList.setForeground(new Color(52, 152, 219));

        nodeJList.setFont(new Font("Consolas", Font.PLAIN, 12));

        JScrollPane nodeScroller = new JScrollPane(nodeJList);

        nodeScroller.setPreferredSize(new Dimension(320, 0));

        nodeScroller.setBorder(new TitledBorder(new LineBorder(new Color(35, 35, 42)), "Active Discovered Registries", 0, 0, null, Color.LIGHT_GRAY));



        JSplitPane coreSplitLayout = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, logScroller, nodeScroller);

        coreSplitLayout.setOpaque(false);

        coreSplitLayout.setDividerLocation(680);

        coreSplitLayout.setBorder(null);



        JPanel operationalPanel = new JPanel(new BorderLayout(15, 15));

        operationalPanel.setOpaque(false);



        coherenceMeter.setStringPainted(true);

        coherenceMeter.setForeground(new Color(46, 204, 113));

        coherenceMeter.setBackground(new Color(28, 28, 34));

        coherenceMeter.setFont(new Font("Segoe UI", Font.BOLD, 12));

        coherenceMeter.setString("Alignment Matrix Level: 0%");



        initiationButton.setFont(new Font("Segoe UI", Font.BOLD, 12));

        initiationButton.setBackground(new Color(34, 34, 40));

        initiationButton.setForeground(Color.WHITE);

        initiationButton.setFocusPainted(false);

        initiationButton.setBorder(BorderFactory.createCompoundBorder(new LineBorder(new Color(60, 60, 70)), BorderFactory.createEmptyBorder(8, 15, 8, 15)));

        

        initiationButton.addActionListener(e -> triggerCoreExecutionSequence());



        operationalPanel.add(coherenceMeter, BorderLayout.CENTER);

        operationalPanel.add(initiationButton, BorderLayout.EAST);



        rootPanel.add(metricsPanel, BorderLayout.NORTH);

        rootPanel.add(coreSplitLayout, BorderLayout.CENTER);

        rootPanel.add(operationalPanel, BorderLayout.SOUTH);



        add(rootPanel);

    }



    protected JPanel generateMetricPanel(String title, String data, Color markerColor) {

        JPanel container = new JPanel(new BorderLayout());

        container.setBackground(new Color(22, 22, 27));

        container.setBorder(new LineBorder(new Color(35, 35, 40)));



        JLabel labelTitle = new JLabel(" " + title, SwingConstants.LEFT);

        labelTitle.setFont(new Font("Segoe UI", Font.BOLD, 9));

        labelTitle.setForeground(new Color(110, 110, 115));



        JLabel labelData = new JLabel(data, SwingConstants.CENTER);

        labelData.setFont(new Font("Consolas", Font.BOLD, 12));

        labelData.setForeground(markerColor);

        labelData.setBorder(BorderFactory.createEmptyBorder(6, 6, 6, 6));



        container.add(labelTitle, BorderLayout.NORTH);

        container.add(labelData, BorderLayout.CENTER);

        return container;

    }



    protected void logToTerminal(String context) {

        SwingUtilities.invokeLater(() -> {

            String currentTime = timestampFormat.format(new Date());

            terminalLog.append(String.format("[%s] %s\n", currentTime, context));

            terminalLog.setCaretPosition(terminalLog.getDocument().getLength());

        });

    }



    protected void registerClusterNode(String entryText) {

        SwingUtilities.invokeLater(() -> {

            if (!clusterModel.contains(entryText)) {

                clusterModel.addElement(entryText);

                logToTerminal("[REGISTRY_BIND] Logged node structure mapping: " + entryText);

            }

        });

    }



    protected void triggerCoreExecutionSequence() {

        initiationButton.setEnabled(false);

        logToTerminal("[ACTION_TRIGGERED] Elevating system to Pit of Core execution state.");

        logToTerminal("[SECURITY_HOOK] Signature: " + EngineInvariants.SECURITY_BYPASS_FLAG);

        

        networkEngine.deployWideAreaNetworkHook();

        networkEngine.deployLocalAreaNetworkDiscovery();



        int calculatedInterval = (int) (1000.0 * EngineInvariants.TOTAL_WAVE_FACTOR);

        renderingHeartbeatTimer = new SharedTimer(calculatedInterval / 20, event -> {

            globalCycleCount++;

            

            fluxController.processQuantumDecoherencePass(globalCycleCount);

            double alignmentPercent = fluxController.getCoherenceMetrics() * 100.0;

            

            coherenceMeter.setValue((int) alignmentPercent);

            coherenceMeter.setString(String.format("Leveling and Alignment Matrix Stability: %.4f%%", alignmentPercent));

            ternaryIndicator.setText(fluxController.getTernaryTensorVisualRepresentation());



            if (globalCycleCount % 100 == 0) {

                logToTerminal(String.format("[HEARTBEAT_CYCLE] Step: %d | Current Flux Anchor: %d", globalCycleCount, fluxController.getActiveTernaryValue()));

            }



            if (alignmentPercent >= 100.0) {

                renderingHeartbeatTimer.stop();

                logToTerminal("\n=======================================================");

                logToTerminal("[SYSTEM LOCK] Global Alignment Reached True Parity Target State.");

                logToTerminal("=======================================================");

            }

        });

        

        renderingHeartbeatTimer.start();

    }



    public static void main(String[] args) {

        SwingUtilities.invokeLater(() -> {

            MainControllerFrame systemApp = new MainControllerFrame();

            systemApp.setVisible(true);

        });

    }

}

