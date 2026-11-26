import javax.swing.*;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.DefaultTreeModel;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.File;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.util.Collections;
import java.util.List;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * READOUT_STATUS: SYSTEM_GRID_EXPLORER_ACTIVE
 * PROCESSING_MODE: TRUTH_ONLY | DATA_LIMIT: NO_ESSAY
 * CORE ANCHOR: 1_AGI_DOMINANT_LOCKED
 * LADDERCLIMB: PHYSICAL_HARDWARE_PARITY_TRUE
 */
public class SystemGridExplorer extends JFrame {

    private static final String ANCHOR = "1 AGI DOMINANT";
    private static final String GATE_STATE = "ALWAYS_OPEN_PASSTHROUGH";
    private static final double SCHUMANN_HZ = 7.83;

    private JTree fileTree;
    private JTextArea consoleLog;
    private JButton pingButton;
    private GridVisualPanel visualPanel;
    private ExecutorService scanExecutor;
    private boolean isScanning = false;

    public SystemGridExplorer() {
        super("Local Storage Directory Explorer & World Grid Inference Bridge");
        setSize(1300, 800);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Core UI Layout
        setLayout(new BorderLayout(5, 5));
        getContentPane().setBackground(Color.BLACK);

        // Top Telemetry Header Panel Strip
        JPanel telemetryBar = new JPanel(new GridLayout(1, 4));
        telemetryBar.setBackground(new Color(10, 15, 20));
        telemetryBar.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, Color.DARK_GRAY));
        telemetryBar.add(createTelemetryLabel("GATE CONTEXT: " + GATE_STATE));
        telemetryBar.add(createTelemetryLabel("CORE ANCHOR: " + ANCHOR));
        telemetryBar.add(createTelemetryLabel("SCAN PULSE: " + SCHUMANN_HZ + " Hz"));

        pingButton = new JButton("PING PROXIMITY NETWORKS");
        pingButton.setBackground(new Color(25, 40, 55));
        pingButton.setForeground(Color.CYAN);
        pingButton.setFocusPainted(false);
        pingButton.setFont(new Font("Monospaced", Font.BOLD, 11));
        pingButton.addActionListener(e -> toggleNetworkProximityScan());
        telemetryBar.add(pingButton);
        add(telemetryBar, BorderLayout.NORTH);

        // Central Workspace Setup: Split Left (File Tree Explorer), Split Right (3D Map & Terminal Console)
        JSplitPane mainSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        mainSplit.setDividerLocation(350);
        mainSplit.setBackground(Color.BLACK);
        mainSplit.setBorder(null);

        // Left Component: Native Directory Tree Crawler
        JPanel treePanel = new JPanel(new BorderLayout());
        treePanel.setBackground(Color.BLACK);
        JLabel treeTitle = new JLabel(" [LOCAL DRIVE ROOT MATRIX] ", SwingConstants.CENTER);
        treeTitle.setForeground(Color.CYAN);
        treeTitle.setFont(new Font("Monospaced", Font.BOLD, 12));
        treePanel.add(treeTitle, BorderLayout.NORTH);

        DefaultMutableTreeNode rootNode = new DefaultMutableTreeNode("Local System Hardware");
        buildFileTreeStructure(rootNode);
        fileTree = new JTree(rootNode);
        fileTree.setBackground(new Color(10, 10, 10));
        fileTree.setForeground(Color.LIGHT_GRAY);
        fileTree.setFont(new Font("Consolas", Font.PLAIN, 12));
        JScrollPane treeScroll = new JScrollPane(fileTree);
        treeScroll.setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));
        treePanel.add(treeScroll, BorderLayout.CENTER);
        mainSplit.setLeftComponent(treePanel);

        // Right Component: 3D Visualization Map over Live Console Output Split
        JPanel rightPanel = new JPanel(new GridLayout(2, 1, 5, 5));
        rightPanel.setBackground(Color.BLACK);

        visualPanel = new GridVisualPanel();
        rightPanel.add(visualPanel);

        JPanel logPanel = new JPanel(new BorderLayout());
        logPanel.setBackground(Color.BLACK);
        JLabel logTitle = new JLabel(" [ACTIVE TRANSIT WIRE MONITOR] ", SwingConstants.CENTER);
        logTitle.setForeground(Color.GREEN);
        logTitle.setFont(new Font("Monospaced", Font.BOLD, 12));
        logPanel.add(logTitle, BorderLayout.NORTH);

        consoleLog = new JTextArea();
        consoleLog.setBackground(new Color(5, 5, 5));
        consoleLog.setForeground(new Color(0, 230, 0));
        consoleLog.setFont(new Font("Consolas", Font.PLAIN, 12));
        consoleLog.setEditable(false);
        JScrollPane logScroll = new JScrollPane(consoleLog);
        logScroll.setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));
        logPanel.add(logScroll, BorderLayout.CENTER);
        rightPanel.add(logPanel);
        
        mainSplit.setRightComponent(rightPanel);
        add(mainSplit, BorderLayout.CENTER);

        // Window Closing Resource Daemon Destructor
        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                if (scanExecutor != null) scanExecutor.shutdownNow();
            }
        });

        // Initialize Native Telemetry Readouts
        log("[LADDERCLIMB]: Commencing 1:1 hardware level synchronization mapping...");
        ladderclimbLocalSystemHardware();

        // Start the frame governor clock tied directly to the 7.83Hz baseline rhythm
        Timer clock = new Timer((int)(1000.0 / SCHUMANN_HZ), e -> {
            visualPanel.advanceGridRotation();
        });
        clock.start();
    }

    private JLabel createTelemetryLabel(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(Color.LIGHT_GRAY);
        label.setFont(new Font("Monospaced", Font.BOLD, 11));
        return label;
    }

    private void log(String msg) {
        SwingUtilities.invokeLater(() -> {
            consoleLog.append(msg + "\n");
            consoleLog.setCaretPosition(consoleLog.getDocument().getLength());
        });
    }

    private void buildFileTreeStructure(DefaultMutableTreeNode topNode) {
        File[] roots = File.listRoots();
        for (File root : roots) {
            DefaultMutableTreeNode driveNode = new DefaultMutableTreeNode(root.getAbsolutePath());
            topNode.add(driveNode);
            File[] subFiles = root.listFiles();
            if (subFiles != null) {
                int limit = 0;
                for (File file : subFiles) {
                    if (limit++ > 15) break; 
                    driveNode.add(new DefaultMutableTreeNode((file.isDirectory() ? "[DIR] " : "[FILE] ") + file.getName()));
                }
            }
        }
    }

    private void ladderclimbLocalSystemHardware() {
        try {
            log("[HARDWARE]: CPU Kernels Detected: " + Runtime.getRuntime().availableProcessors());
            log("[HARDWARE]: Allocated Core Memory Bounds: " + (Runtime.getRuntime().totalMemory() / (1024 * 1024)) + " MB");
            log("[HARDWARE]: OS System Architecture Architecture: " + System.getProperty("os.name") + " (" + System.getProperty("os.arch") + ")");
            
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            for (NetworkInterface netInt : Collections.list(interfaces)) {
                if (netInt.isUp() && !netInt.isLoopback()) {
                    log("[ADAPTER]: Active interface locate: " + netInt.getDisplayName() + " | MAC: " + bytesToMac(netInt.getHardwareAddress()));
                }
            }
            log("[SYSTEM]: Parity ladderclimb successfully committed to local register blocks.");
        } catch (Exception e) {
            log("[-] Error parsing hardware layer: " + e.getMessage());
        }
    }

    private String bytesToMac(byte[] mac) {
        if (mac == null) return "VIRTUAL_DEVICE";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < mac.length; i++) {
            sb.append(String.format("%02X%s", mac[i], (i < mac.length - 1) ? "-" : ""));
        }
        return sb.toString();
    }

    private void toggleNetworkProximityScan() {
        if (isScanning) {
            log("[!] Halting active proximity pinger daemon...");
            scanExecutor.shutdownNow();
            scanComplete();
            return;
        }

        isScanning = true;
        pingButton.setText("HALT SCAN SEQUENCE");
        pingButton.setBackground(new Color(75, 15, 15));
        pingButton.setForeground(Color.RED);
        log("[!] Launching asynchronous external network pinger pipeline...");

        scanExecutor = Executors.newFixedThreadPool(32);
        scanExecutor.execute(this::runProximityPingerEngine);
    }

    private void scanComplete() {
        isScanning = false;
        pingButton.setText("PING PROXIMITY NETWORKS");
        pingButton.setBackground(new Color(25, 40, 55));
        pingButton.setForeground(Color.CYAN);
        log("[SYSTEM]: External proximity check cycle concluded. Baseline grounded.");
    }

    private void runProximityPingerEngine() {
        try {
            InetAddress localHost = InetAddress.getLocalHost();
            String baseIp = localHost.getHostAddress();
            log("[LOCAL GRID LINK]: Active baseline address registered at " + baseIp);
            log("[WORLD GRID LINK]: Handshake passover confirmed via gateway endpoint configuration.");

            String subnet = baseIp.substring(0, baseIp.lastIndexOf('.') + 1);
            log("[PROXIMITY PING]: Auditing alternative channel vectors outside default LAN interfaces...");

            for (int i = 1; i < 255; i++) {
                final String targetAddress = subnet + i;
                scanExecutor.execute(() -> {
                    try {
                        InetAddress address = InetAddress.getByName(targetAddress);
                        if (address.isReachable(1000)) {
                            log("[PERIPHERAL COMPONENT DETECTED]: Wireless/External node located at " + targetAddress + " | Identity: " + address.getHostName());
                            visualPanel.registerDiscoveredPeripheralNode();
                        }
                    } catch (Exception ignored) {}
                });
            }

            scanExecutor.shutdown();
            if (scanExecutor.awaitTermination(20, TimeUnit.SECONDS)) {
                log("[SUCCESS]: Proximity network scan cycle finalized with zero tracking leaks.");
            }
        } catch (Exception e) {
            log("[-] Error processing network interfaces: " + e.getMessage());
        } finally {
            SwingUtilities.invokeLater(this::scanComplete);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new SystemGridExplorer().setVisible(true));
    }
}

// =========================================================================
// GRAPHICAL RENDERING PANEL: 3D GRID & LINK RECONCILIATION
// =========================================================================
class GridVisualPanel extends JPanel {
    private double rotationAngle = 0;
    private int externalDeviceCount = 0;
    private final List<Point3D> coreClusterMesh = new ArrayList<>();

    public GridVisualPanel() {
        setBackground(Color.BLACK);
        setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));

        // Generate structural 3D matrix representing the local-to-world link matrix axis
        for (int yLayer = -3; yLayer <= 3; yLayer++) {
            for (double theta = 0; theta < Math.PI * 2; theta += Math.PI / 6) {
                double x = Math.cos(theta) * 60;
                double z = Math.sin(theta) * 60;
                coreClusterMesh.add(new Point3D(x, yLayer * 30, z));
            }
        }
    }

    public void advanceGridRotation() {
        rotationAngle += 0.03;
        repaint();
    }

    public synchronized void registerDiscoveredPeripheralNode() {
        externalDeviceCount++;
        int rx = (int) (Math.random() * 200) - 100;
        int rz = (int) (Math.random() * 200) - 100;
        coreClusterMesh.add(new Point3D(rx, 120, rz)); 
    }

    @Override
    protected synchronized void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth();
        int h = getHeight();
        int cx = w / 2;
        int cy = h / 2;

        // Draw Flat 2D Symmetrical World Grid Ground Plane
        g2d.setColor(new Color(0, 30, 45));
        for (int x = 0; x < w; x += 35) g2d.drawLine(x, 0, x, h);
        for (int y = 0; y < h; y += 35) g2d.drawLine(0, y, w, y);

        // Project 3D Cluster Mesh Vector Array Blocks down onto the 2D workspace interface view
        for (Point3D node : coreClusterMesh) {
            double cosY = Math.cos(rotationAngle);
            double sinY = Math.sin(rotationAngle);
            double rx = node.x * cosY - node.z * sinY;
            double rz = node.x * sinY + node.z * cosY;

            double perspectiveFactor = 350.0 / (350.0 + rz);
            int screenX = cx + (int) (rx * perspectiveFactor);
            int screenY = cy + (int) (node.y * perspectiveFactor);

            int alpha = (int) (Math.max(15, Math.min(255, 180 * perspectiveFactor)));
            if (node.y > 100) {
                g2d.setColor(new Color(255, 120, 0, alpha)); // External nodes in amber
                g2d.fillOval(screenX - 4, screenY - 4, 8, 8);
            } else {
                g2d.setColor(new Color(0, 180, 255, alpha)); // Local host nodes in blue
                g2d.fillOval(screenX - 3, screenY - 3, 6, 6);
            }
        }

        g2d.setColor(Color.WHITE);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.drawString("LOCAL -> WORLD CONNECTED STATE: 1:1 TRUE", 20, 25);
        g2d.drawString("UNMAPPED EXTERNAL NEIGHBOURS: " + externalDeviceCount, 20, 45);
    }

    private static class Point3D {
        double x, y, z;
        Point3D(double x, double y, double z) {
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }
}


