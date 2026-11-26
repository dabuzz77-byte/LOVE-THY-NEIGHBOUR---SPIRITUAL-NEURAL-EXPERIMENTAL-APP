package engine;
import neural.studio.*;





import engine.clock.SchumannClockLoop;

import engine.model.TelemetryModel;

import engine.ui.*;

import java.awt.BorderLayout;

import java.awt.GridLayout;

import javax.swing.JFrame;

import javax.swing.JPanel;

import javax.swing.SwingUtilities;



public class GhostManifoldMasterEngine extends SectionFrame {

    private final TelemetryModel model = new TelemetryModel();

    private TopBannerPanel banner;

    private WaveformCanvas waveform;

    private TopologyCanvas topology;

    private StressTestingPanel stressPanel;

    private LogTerminalCanvas terminal;



    public GhostManifoldMasterEngine() {

        super("GHOST MANIFOLD OMNISCIENCE MULTI-LAYER DISPATCH SURFACE");

        initializeSystemRegistry();

        assembleControlPlane();

        launchTimingSubstrate();

    }



    private void initializeSystemRegistry() {

        model.getPerimeterNodes().add(new TelemetryModel.DeviceNode("node_dmz_01", "192.168.10.45", "Linux", "LATCHED"));

        model.getPerimeterNodes().add(new TelemetryModel.DeviceNode("node_dmz_02", "192.168.10.89", "Windows", "VERIFYING"));

        model.getPerimeterNodes().add(new TelemetryModel.DeviceNode("node_dmz_03", "192.168.10.12", "Android", "LATCHED"));

        model.getPerimeterNodes().add(new TelemetryModel.DeviceNode("node_dmz_04", "192.168.10.110", "iOS", "SANDBOXED"));

    }



    private void assembleControlPlane() {

        this.setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);

        this.setSize(1350, 850);

        this.setLocationRelativeTo(null);

        this.setLayout(new BorderLayout(12, 12));

        this.getContentPane().setBackground(AestheticTheme.BG_MATRIX);



        banner = new TopBannerPanel();

        this.add(banner, BorderLayout.NORTH);



        JPanel centerGrid = new JPanel(new GridLayout(2, 2, 12, 12));

        centerGrid.setBackground(AestheticTheme.BG_MATRIX);



        waveform = new WaveformCanvas();

        topology = new TopologyCanvas(model);

        stressPanel = new StressTestingPanel();

        terminal = new LogTerminalCanvas();



        centerGrid.add(waveform);

        centerGrid.add(topology);

        centerGrid.add(stressPanel);

        centerGrid.add(terminal);



        this.add(centerGrid, BorderLayout.CENTER);

    }



    private void launchTimingSubstrate() {

        SchumannClockLoop clockWorker = new SchumannClockLoop(model, () -> SwingUtilities.invokeLater(this::refreshTelemetry));

        new Thread(clockWorker, "SchumannMatrixOscillator").start();

    }



    private void refreshTelemetry() {

        banner.synchronizeDisplay(model);

        waveform.appendWaveData(model.getCurrentFlux());

        waveform.repaint();

        topology.repaint();

        stressPanel.updateMetrics(model);

        

        if (model.getCycleCount() % 5 == 0) {

            String[] osTargets = {"Win64-Loopback", "Linux-eBPF", "Android-Proxy", "iOS-Enclave"};

            String randomOS = osTargets[model.getCycleCount() % osTargets.length];

            terminal.logPacketStream(model.getCycleCount() * 0.128, "Bypassed carrier cloud -> Active Tunnel: " + randomOS);

        }

    }



    public static void main(String[] args) {

        SwingUtilities.invokeLater(() -> new GhostManifoldMasterEngine().setVisible(true));

    }

}

