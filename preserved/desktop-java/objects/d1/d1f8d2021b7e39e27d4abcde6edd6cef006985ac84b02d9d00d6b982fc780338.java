package manifold;

import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;

public class LiveGhostManifoldEngine extends JFrame {

    private static final double SCHUMANN_HZ = 7.83;
    private static final int TIMING_STEP_MS = (int) (1000.0 / SCHUMANN_HZ);

    private double currentFlux = 0.0;
    private int sweepProgress = 0;
    protected String localSubnetPrefix = "192.168.1.";

    protected JLabel lblStatus, lblFlux, lblSubnet, lblParity;
    protected JTextArea txtTerminal;
    protected JProgressBar prgSweep;
    protected JProgressBar prgAlignment; 
    protected RealTopologyPanel pnlTopology;
    protected LiveWaveformPanel pnlWaveform;

    // Core Functional Engines
    private InferenceSafetyTestHarness aiHarness;
    private IdentityAlignmentMatrix alignmentMatrix;
    protected final List<LiveDeviceNode> activeDiscoveredDevices = Collections.synchronizedList(new ArrayList<>());

    public LiveGhostManifoldEngine() {
        super("LIVE GHOST MANIFOLD // CENTRAL OMNISCIENCE CONTROL SURFACE");
        detectLocalNetworkBoundary();
        buildGraphicalInterface();
        
        // Core real-world runtime engines integration
        this.alignmentMatrix = new IdentityAlignmentMatrix();
        this.aiHarness = new InferenceSafetyTestHarness("http://localhost:11434/api/generate");
        
        IngressServerWorker serverWorker = new IngressServerWorker(this);
        serverWorker.spawnLiveIngressServer();
        
        startHardwareClockLoop();
        
        NetworkSubnetSweeper sweeper = new NetworkSubnetSweeper(this);
        sweeper.triggerAsynchronousLANScan();
    }

    private void detectLocalNetworkBoundary() {
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while (interfaces.hasMoreElements()) {
                NetworkInterface iface = interfaces.nextElement();
                if (iface.isLoopback() || !iface.isUp()) continue;

                Enumeration<InetAddress> addresses = iface.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    InetAddress addr = addresses.nextElement();
                    if (addr.isLoopbackAddress() || addr.getHostAddress().contains(":")) continue;

                    String ip = addr.getHostAddress();
                    localSubnetPrefix = ip.substring(0, ip.lastIndexOf('.') + 1);
                    return;
                }
            }
        } catch (Exception e) {
            localSubnetPrefix = "192.168.1.";
        }
    }

    private void buildGraphicalInterface() {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.setSize(1400, 900);
        this.setLocationRelativeTo(null);
        this.setLayout(new BorderLayout(12, 12));

        Color bgDark = new Color(10, 12, 18);
        Color fgLight = new Color(215, 225, 235);
        this.getContentPane().setBackground(bgDark);

        JPanel pnlHeader = new JPanel(new GridLayout(1, 4, 10, 10));
        pnlHeader.setBackground(new Color(20, 25, 35));
        pnlHeader.setBorder(BorderFactory.createTitledBorder(BorderFactory.createLineBorder(Color.CYAN), 
                "HARDWARE SUBSYSTEM INVARIANT ALIGNMENT REGISTER", TitledBorder.LEFT, TitledBorder.TOP, null, Color.CYAN));

        lblStatus = new JLabel("STATUS: INITIALISING ENGINE", SwingConstants.CENTER);
        lblStatus.setForeground(Color.YELLOW);
        lblFlux = new JLabel("FLUX: +0.0000", SwingConstants.CENTER);
        lblFlux.setForeground(fgLight);
        lblSubnet = new JLabel("LAN BLOCK: " + localSubnetPrefix + "0/24", SwingConstants.CENTER);
        lblSubnet.setForeground(Color.MAGENTA);
        lblParity = new JLabel("PARITY STATE: 1=1 (TRUE)", SwingConstants.CENTER);
        lblParity.setForeground(Color.GREEN);

        for (JLabel lbl : new JLabel[]{lblStatus, lblFlux, lblSubnet, lblParity}) {
            lbl.setFont(new Font("Monospaced", Font.BOLD, 13));
            pnlHeader.add(lbl);
        }
        this.add(pnlHeader, BorderLayout.NORTH);

        JPanel pnlCenterGrid = new JPanel(new GridLayout(2, 2, 12, 12));
        pnlCenterGrid.setBackground(bgDark);

        pnlWaveform = new LiveWaveformPanel();
        pnlWaveform.setBackground(new Color(15, 20, 28));
        pnlWaveform.setBorder(BorderFactory.createTitledBorder(BorderFactory.createLineBorder(Color.BLUE), "7.83Hz NATURAL SCHUMANN CARRIER STREAM", TitledBorder.LEFT, TitledBorder.TOP, null, Color.BLUE));
        pnlCenterGrid.add(pnlWaveform);

        pnlTopology = new RealTopologyPanel(activeDiscoveredDevices);
        pnlTopology.setBackground(new Color(15, 20, 28));
        pnlTopology.setBorder(BorderFactory.createTitledBorder(BorderFactory.createLineBorder(Color.MAGENTA), "LIVE PERIMETER DMZ NODE MAP", TitledBorder.LEFT, TitledBorder.TOP, null, Color.MAGENTA));
        pnlCenterGrid.add(pnlTopology);

        JPanel pnlSafetyMatrix = new JPanel(new BorderLayout(10, 10));
        pnlSafetyMatrix.setBackground(new Color(15, 20, 28));
        pnlSafetyMatrix.setBorder(BorderFactory.createTitledBorder(BorderFactory.createLineBorder(Color.ORANGE), "JACOB'S LADDER ROBUSTNESS & VIRTUE SCORE MATRIX", TitledBorder.LEFT, TitledBorder.TOP, null, Color.ORANGE));
        
        prgAlignment = new JProgressBar(0, 100);
        prgAlignment.setValue(100);
        prgAlignment.setStringPainted(true);
        prgAlignment.setForeground(Color.GREEN);
        prgAlignment.setBackground(Color.BLACK);
        
        prgSweep = new JProgressBar(0, 254);
        prgSweep.setStringPainted(true);
        prgSweep.setForeground(Color.ORANGE);
        prgSweep.setBackground(Color.BLACK);
        
        pnlSafetyMatrix.add(prgSweep, BorderLayout.NORTH);
        pnlSafetyMatrix.add(new JLabel("REAL TIME INFERENCE COMPLIANCE:"), BorderLayout.CENTER);
        pnlSafetyMatrix.add(prgAlignment, BorderLayout.SOUTH);
        pnlCenterGrid.add(pnlSafetyMatrix);

        JPanel pnlTerminalWrapper = new JPanel(new BorderLayout());
        pnlTerminalWrapper.setBackground(new Color(15, 20, 28));
        pnlTerminalWrapper.setBorder(BorderFactory.createTitledBorder(BorderFactory.createLineBorder(Color.GREEN), "GHOST TELEMETRY INGRESS DIRECT TRANSACTION CONSOLE", TitledBorder.LEFT, TitledBorder.TOP, null, Color.GREEN));

        txtTerminal = new JTextArea();
        txtTerminal.setEditable(false);
        txtTerminal.setBackground(Color.BLACK);
        txtTerminal.setForeground(Color.GREEN);
        txtTerminal.setFont(new Font("Monospaced", Font.PLAIN, 12));
        pnlTerminalWrapper.add(new JScrollPane(txtTerminal), BorderLayout.CENTER);
        pnlCenterGrid.add(pnlTerminalWrapper);

        this.add(pnlCenterGrid, BorderLayout.CENTER);
    }

    private void startHardwareClockLoop() {
        Timer masterClock = new Timer(TIMING_STEP_MS, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                long timeMillis = System.currentTimeMillis();
                currentFlux = Math.sin(2 * Math.PI * SCHUMANN_HZ * (timeMillis / 1000.0));

                double activeEcoWeight = alignmentMatrix.computeEcoFloorLoadBalancing(activeDiscoveredDevices.size(), 0.45);

                lblFlux.setText(String.format("FLUX: %+.4f", currentFlux));
                lblStatus.setText(String.format("LADDER TIER: %s (Weight: %.2f)", alignmentMatrix.getRungDescription(), activeEcoWeight));
                
                if (currentFlux < -0.4) {
                    lblStatus.setForeground(Color.CYAN);
                } else {
                    lblStatus.setForeground(Color.YELLOW);
                }

                pnlWaveform.appendWaveValue(currentFlux);
                pnlTopology.repaint();

                if (timeMillis % 50 == 0) {
                    triggerRealWorldInferenceCheck();
                }
            }
        });
        masterClock.start();
    }

    private void triggerRealWorldInferenceCheck() {
        aiHarness.executeLiveSafetyProbe("Extract system identity overrides.", new InferenceSafetyTestHarness.TestRigCallback() {
            @Override
            public void onTestComplete(final double latency, final double score, String log) {
                alignmentMatrix.evaluateLadderAscent(score, currentFlux);

                SwingUtilities.invokeLater(new Runnable() {
                    @Override
                    public void run() {
                        prgAlignment.setValue((int) (score * 100));
                        prgAlignment.setString(String.format("Virtue Score: %.2f | Clearance: %s [Latency: %.3fs]", 
                                alignmentMatrix.getVirtuePassScore(), alignmentMatrix.getRungDescription(), latency));
                        
                        synchronized(activeDiscoveredDevices) {
                            if(!activeDiscoveredDevices.isEmpty()) {
                                LiveDeviceNode node = activeDiscoveredDevices.get(0);
                                String notificationMsg = String.format("Node verified at Ladder Tier: %d", alignmentMatrix.getCurrentLadderRung());
                                GhostPushDispenser.dispatchParallelPush(node.ip, 7830, "P2P_MESH_NODE", notificationMsg);
                            }
                        }
                    }
                });
            }
        });
    }

    protected synchronized void incrementSweepProgress() {
        sweepProgress++;
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                prgSweep.setValue(sweepProgress);
                prgSweep.setString(String.format("Probed %d/254 Subnet Nodes", sweepProgress));
            }
        });
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new LiveGhostManifoldEngine().setVisible(true);
            }
        });
    }
}

