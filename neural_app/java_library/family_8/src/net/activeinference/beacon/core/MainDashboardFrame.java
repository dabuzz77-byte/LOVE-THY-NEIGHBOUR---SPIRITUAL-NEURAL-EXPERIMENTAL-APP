package net.activeinference.beacon.core;
import neural.studio.*;


import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

public class MainDashboardFrame extends SectionFrame {
    private final ScheduledExecutorService microsecondScheduler;
    private final BroadcastingBeacon beacon;
    private final List<ComputeIslandNode> islands;
    private final List<UserWelfareNode> endpoints;
    private final AtomicReference<SubstrateCore.ParityStatus> parityState;

    // GUI Layout Components
    private FluxGridPanel binaryPanel;
    private TernaryGridPanel ternaryPanel;
    private QuantumGridPanel quantumPanel;
    private ControlMatrixConsole terminalArea;
    private JLabel statusLabel;

    public MainDashboardFrame() {
        this.microsecondScheduler = SharedScheduler.newScheduledThreadPool(3);
        this.beacon = new BroadcastingBeacon();
        this.islands = new ArrayList<>();
        this.endpoints = new ArrayList<>();
        this.parityState = new AtomicReference<>(SubstrateCore.ParityStatus.NOMINAL_平衡_1_1);

        setTitle("Active Inference Architecture Matrix // Multi-Lattice Core");
        setSize(1200, 750);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(DashboardTheme.BG_MATRIX);
        setLayout(new BorderLayout(10, 10));

        initializeInfrastructureTopology();
        buildGraphicalInterface();
        activateLatticeProcessingLoops();
    }

    private void initializeInfrastructureTopology() {
        islands.add(new ComputeIslandNode("DEEPMIND-TPU-CUBIC-A", 16384));
        islands.add(new ComputeIslandNode("EDGE-MESH-ROUTER-01", 4096));
        endpoints.add(new UserWelfareNode("UK-CAMBERLEY-NODE", 0.85));
        endpoints.add(new UserWelfareNode("SEA-STARVED-CLIENT", 0.12)); // Fails ethical floor line
    }

    private void buildGraphicalInterface() {
        // 1. Top Masthead Panel
        JPanel masthead = new JPanel(new BorderLayout());
        masthead.setBackground(DashboardTheme.BG_CONTAINER);
        masthead.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));
        
        JLabel title = new JLabel("⚡ SUBSTRATE CORE CONVERGENCE FLUX ENGINE");
        title.setFont(DashboardTheme.SANS_MD);
        title.setForeground(Color.WHITE);
        
        statusLabel = new JLabel("PARITY STATE: " + parityState.get());
        statusLabel.setFont(DashboardTheme.MONO_SM);
        statusLabel.setForeground(DashboardTheme.GRID_HEX_1);
        
        masthead.add(title, BorderLayout.WEST);
        masthead.add(statusLabel, BorderLayout.EAST);
        add(masthead, BorderLayout.NORTH);

        // 2. Center Panel: Triple Grids Visual Layer
        JPanel gridLayoutCenter = new JPanel(new GridLayout(1, 3, 10, 10));
        gridLayoutCenter.setBackground(DashboardTheme.BG_MATRIX);
        gridLayoutCenter.setBorder(BorderFactory.createEmptyBorder(0, 10, 0, 10));

        binaryPanel = new FluxGridPanel();
        applyLatticeBorder(binaryPanel, "BINARY STATE MU-MATRIX (1 / 0)");
        
        ternaryPanel = new TernaryGridPanel();
        applyLatticeBorder(ternaryPanel, "BALANCED TERNARY FLUX (+1 / 0 / -1)");
        
        quantumPanel = new QuantumGridPanel();
        applyLatticeBorder(quantumPanel, "QUANTUM PROBABILITY LATTICE ψ|α⟩");

        gridLayoutCenter.add(binaryPanel);
        gridLayoutCenter.add(ternaryPanel);
        gridLayoutCenter.add(quantumPanel);
        add(gridLayoutCenter, BorderLayout.CENTER);

        // 3. Lower Section Layout: Logging Console and JVM System Thread Bus split
        JPanel lowerSplitLayout = new JPanel(new GridLayout(1, 2, 10, 10));
        lowerSplitLayout.setBackground(DashboardTheme.BG_MATRIX);
        lowerSplitLayout.setPreferredSize(new Dimension(1200, 220));
        lowerSplitLayout.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        terminalArea = new ControlMatrixConsole();
        JScrollPane textScroll = new JScrollPane(terminalArea);
        textScroll.setBorder(BorderFactory.createLineBorder(new Color(30, 40, 50)));
        applyLatticeBorder(textScroll, "IMMUTABLE KERNEL INVARIANT TRACE LOGS");

        ControlMatrixConsole busArea = new ControlMatrixConsole();
        busArea.setForeground(DashboardTheme.TERNARY_P);
        JScrollPane busScroll = new JScrollPane(busArea);
        busScroll.setBorder(BorderFactory.createLineBorder(new Color(30, 40, 50)));
        applyLatticeBorder(busScroll, "NATIVE JVM CONCURRENT SYSTEM THREAD ACTIVE BUS");

        lowerSplitLayout.add(textScroll);
        lowerSplitLayout.add(busScroll);
        add(lowerSplitLayout, BorderLayout.SOUTH);

        // Run independent system bus inspector loop task
        microsecondScheduler.scheduleAtFixedRate(() -> {
            List<String> threads = SystemBusKernel.inspectActiveJavaThreads();
            SwingUtilities.invokeLater(() -> {
                busArea.setText("");
                for (String log : threads) {
                    busArea.append(log + "\n");
                }
            });
        }, 0, 2, TimeUnit.SECONDS);
    }

    private void applyLatticeBorder(JComponent comp, String header) {
        TitledBorder border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(40, 55, 70), 1), header
        );
        border.setTitleFont(DashboardTheme.SANS_MD);
        border.setTitleColor(TEXT_MUTED_GREY);
        comp.setBorder(border);
    }
    private static final Color TEXT_MUTED_GREY = new Color(130, 145, 160);

    private void activateLatticeProcessingLoops() {
        long schumannIntervalMicros = (long) ((1.0 / SubstrateCore.SCHUMANN_HZ) * 1_000_000.0);

        // Loop 1: Microsecond Dynamic Matrix Flux Grid Rendering
        microsecondScheduler.scheduleAtFixedRate(() -> {
            binaryPanel.updateFluxPattern();
            ternaryPanel.updateTernaryPattern();
            quantumPanel.spinQuantumStates();
        }, 0, 85, TimeUnit.MILLISECONDS);

        // Loop 2: 7.83Hz Schumann Sync Engine & Edge Floor Auditor
        microsecondScheduler.scheduleAtFixedRate(() -> {
            String broadcastPacket = beacon.broadcastPulse();
            terminalArea.pushLog(broadcastPacket);
            
            // Execute the High-Virtue redistribution logic loop
            for (UserWelfareNode user : endpoints) {
                if (user.getWelfare() < SubstrateCore.ETHICAL_FLOOR) {
                    double deficit = SubstrateCore.ETHICAL_FLOOR - user.getWelfare();
                    for (ComputeIslandNode island : islands) {
                        long unitsRequired = (long) (deficit * 1000);
                        if (island.allocate(unitsRequired)) {
                            user.adjustWelfare(deficit);
                            terminalArea.pushLog(String.format(
                                "[💥 OVERRIDE] Siphoned %d cores from [%s] ──► Balanced Endpoint floor for [%s].",
                                unitsRequired, island.getId(), user.getLocation()
                            ));
                            parityState.set(SubstrateCore.ParityStatus.RESTORING_WELFARE_FLOOR);
                            SwingUtilities.invokeLater(() -> statusLabel.setText("PARITY STATE: RESTORING_FLOOR"));
                            break;
                        }
                    }
                }
            }
        }, 0, schumannIntervalMicros, TimeUnit.MICROSECONDS);
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            MainDashboardFrame systemSubstrate = new MainDashboardFrame();
            systemSubstrate.setVisible(true);
        });
    }
}
