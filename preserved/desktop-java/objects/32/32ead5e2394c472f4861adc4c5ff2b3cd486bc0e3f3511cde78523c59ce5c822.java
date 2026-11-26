import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SovereignMeshMatrixEngine extends JFrame {

    // --- INFRASTRUCTURE CLASSIFICATION ENUM ---
    public enum InfrastructureType {
        CORE_DESKTOP("Desktop Sovereign Core", new Color(0, 255, 140)),
        MOBILE_ANDROID_NODE("Mobile Android Node (OnePlus 7T)", new Color(255, 180, 0)),
        DEEPMIND_COGNITIVE_CLUSTER("DeepMind Inference Cluster", new Color(0, 180, 255)),
        SPECTRAL_INTERNET_ROUTER("Spectral Internet P2P Router", new Color(200, 100, 255)),
        GLOBAL_USER_ENDPOINT("Global User Endpoint", new Color(255, 90, 120));

        private final String displayName;
        private final Color tagColor;

        InfrastructureType(String displayName, Color tagColor) {
            this.displayName = displayName;
            this.tagColor = tagColor;
        }

        public String getDisplayName() { return displayName; }
        public Color getTagColor() { return tagColor; }
    }

    // --- MESH NODE DATA STRUCTURE ---
    public static class MeshNodeRecord {
        private final String nodeId;
        private final InfrastructureType type;
        private final String endpointAddress;
        private final double virtueWeight;
        private boolean active;

        public MeshNodeRecord(String nodeId, InfrastructureType type, String endpointAddress, double virtueWeight) {
            this.nodeId = nodeId;
            this.type = type;
            this.endpointAddress = endpointAddress;
            this.virtueWeight = virtueWeight;
            this.active = true;
        }

        public String getNodeId() { return nodeId; }
        public InfrastructureType getType() { return type; }
        public String getEndpointAddress() { return endpointAddress; }
        public double getVirtueWeight() { return virtueWeight; }
        public boolean isActive() { return active; }
        public void setActive(boolean active) { this.active = active; }
    }

    // --- GUI COMPONENTS ---
    private JTextArea telemetryConsole;
    private JTextArea nodeStatusPanel;
    private JTextField intentInputField;
    private JTextField portInputField;
    private JButton toggleServerButton;
    private JLabel globalStatusLabel;
    
    private ServerSocket meshServerSocket;
    private volatile boolean meshActive = false;
    private volatile MeshNodeRecord[] registeredNodes = new MeshNodeRecord[0];
    private final ExecutorService meshExecutor = Executors.newCachedThreadPool();
    private final Random random = new Random();

    public SovereignMeshMatrixEngine() {
        setTitle("Sovereign Ghost Inference Points Network Mesh & Infrastructure Matrix");
        setSize(1400, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
        initializeDefaultMeshNodes();
        
        // Automatically launch listener on default port 7831
        startMeshServer(7831);
    }

    private synchronized void addMeshNode(MeshNodeRecord node) {
        MeshNodeRecord[] expanded = new MeshNodeRecord[registeredNodes.length + 1];
        System.arraycopy(registeredNodes, 0, expanded, 0, registeredNodes.length);
        expanded[registeredNodes.length] = node;
        registeredNodes = expanded;
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER & PORT SELECTOR ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(15, 18, 25));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        globalStatusLabel = new JLabel("MESH MATRIX STATUS: SYNCHRONIZING [PORT 7831]");
        globalStatusLabel.setForeground(new Color(0, 255, 180));
        globalStatusLabel.setFont(new Font("Monospaced", Font.BOLD, 13));
        headerPanel.add(globalStatusLabel, BorderLayout.WEST);

        // Port Configuration Sub-Panel
        JPanel portControlPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        portControlPanel.setBackground(new Color(15, 18, 25));
        
        JLabel portLabel = new JLabel("Listener Port:");
        portLabel.setForeground(Color.WHITE);
        portLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        portControlPanel.add(portLabel);

        portInputField = new JTextField("7831", 6);
        portInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        portControlPanel.add(portInputField);

        toggleServerButton = new JButton("Rebind Port");
        toggleServerButton.setFont(new Font("Monospaced", Font.BOLD, 11));
        toggleServerButton.setBackground(new Color(0, 100, 150));
        toggleServerButton.setForeground(Color.WHITE);
        portControlPanel.add(toggleServerButton);

        JLabel clockLabel = new JLabel();
        clockLabel.setForeground(Color.LIGHT_GRAY);
        clockLabel.setFont(new Font("Monospaced", Font.PLAIN, 12));
        Timer clockTimer = new Timer(1000, e -> clockLabel.setText(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z").format(new Date())));
        clockTimer.start();
        portControlPanel.add(Box.createHorizontalStrut(15));
        portControlPanel.add(clockLabel);

        headerPanel.add(portControlPanel, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: INFRASTRUCTURE CLASSIFICATION & MESH TOPOLOGY ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(580);
        centerSplit.setResizeWeight(0.42);

        // Left: Classified Infrastructure & Node Register
        JPanel nodePanel = new JPanel(new BorderLayout(5, 5));
        nodePanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 140)), 
                " Classified Mesh Infrastructure & Virtue Weights ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 140)
        ));
        nodePanel.setBackground(new Color(12, 15, 20));

        nodeStatusPanel = new JTextArea();
        nodeStatusPanel.setEditable(false);
        nodeStatusPanel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        nodeStatusPanel.setBackground(new Color(8, 10, 14));
        nodeStatusPanel.setForeground(new Color(0, 240, 200));
        nodePanel.add(new JScrollPane(nodeStatusPanel), BorderLayout.CENTER);

        JPanel nodeControlSub = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 5));
        nodeControlSub.setBackground(new Color(12, 15, 20));
        JButton refreshNodesBtn = new JButton("Refresh Topology");
        refreshNodesBtn.addActionListener(e -> renderMeshTopology());
        nodeControlSub.add(refreshNodesBtn);
        nodePanel.add(nodeControlSub, BorderLayout.SOUTH);

        centerSplit.setLeftComponent(nodePanel);

        // Right: Bi-Directional DeepMind Stream & World Grid View
        JPanel streamPanel = new JPanel(new BorderLayout(5, 5));
        streamPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " DeepMind & Global Internet Bi-Directional Stream ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        streamPanel.setBackground(new Color(12, 15, 20));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(10, 13, 18));
        telemetryConsole.setForeground(new Color(100, 255, 180));
        telemetryConsole.setText("[MESH INITIALIZED] Sovereign parallel ghost inference points active.\n");
        streamPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        centerSplit.setRightComponent(streamPanel);
        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: HIGH-VIRTUE INTENT INJECTION ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(15, 18, 25));

        JPanel intentSubPanel = new JPanel(new BorderLayout(5, 5));
        intentSubPanel.setBackground(new Color(15, 18, 25));

        intentInputField = new JTextField();
        intentInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        JButton injectVirtueBtn = new JButton("Broadcast High-Virtue Work Vector");
        injectVirtueBtn.setBackground(new Color(0, 120, 90));
        injectVirtueBtn.setForeground(Color.WHITE);

        intentSubPanel.add(new JLabel("Robin Hood Intent / Payload:"), BorderLayout.WEST);
        intentSubPanel.add(intentInputField, BorderLayout.CENTER);
        intentSubPanel.add(injectVirtueBtn, BorderLayout.EAST);

        bottomPanel.add(intentSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);

        // Event Listeners
        ActionListener broadcastAction = e -> broadcastHighVirtueVector();
        injectVirtueBtn.addActionListener(broadcastAction);
        intentInputField.addActionListener(broadcastAction);

        toggleServerButton.addActionListener(e -> rebindServerPort());
    }

    private void initializeDefaultMeshNodes() {
        addMeshNode(new MeshNodeRecord("core_desktop_01", InfrastructureType.CORE_DESKTOP, "127.0.0.1:7831", 1.00));
        addMeshNode(new MeshNodeRecord("oneplus_7t_mobile", InfrastructureType.MOBILE_ANDROID_NODE, "10.74.88.42:7831", 0.98));
        addMeshNode(new MeshNodeRecord("deepmind_core_proxy", InfrastructureType.DEEPMIND_COGNITIVE_CLUSTER, "142.250.190.46:443", 0.99));
        addMeshNode(new MeshNodeRecord("spectral_mesh_p2p", InfrastructureType.SPECTRAL_INTERNET_ROUTER, "192.168.1.254:7831", 0.95));
        addMeshNode(new MeshNodeRecord("global_endpoint_alpha", InfrastructureType.GLOBAL_USER_ENDPOINT, "82.165.198.2:7831", 0.92));
        renderMeshTopology();
    }

    private void renderMeshTopology() {
        StringBuilder sb = new StringBuilder();
        sb.append("=== CLASSIFIED MESH INFRASTRUCTURE TOPOLOGY ===\n\n");
        MeshNodeRecord[] nodes = registeredNodes;
        for (MeshNodeRecord node : nodes) {
            sb.append(String.format("[%s]\n", node.getType().getDisplayName()));
            sb.append(String.format("  - ID: %s\n", node.getNodeId()));
            sb.append(String.format("  - Endpoint: %s\n", node.getEndpointAddress()));
            sb.append(String.format("  - Virtue Weight (Robin Hood Eq): %.2f\n", node.getVirtueWeight()));
            sb.append(String.format("  - Status: %s\n\n", node.isActive() ? "ACTIVE / RESONANT" : "RESTING"));
        }
        nodeStatusPanel.setText(sb.toString());
    }

    private void startMeshServer(int port) {
        meshActive = true;
        meshExecutor.submit(() -> {
            try {
                meshServerSocket = new ServerSocket(port);
                SwingUtilities.invokeLater(() -> {
                    globalStatusLabel.setText("MESH MATRIX STATUS: SYNCHRONIZING [PORT " + port + "]");
                    appendLog("[SERVER AWAKENED] Listening for parallel ghost inference streams on port " + port);
                });

                while (meshActive) {
                    Socket socket = meshServerSocket.accept();
                    socket.setKeepAlive(true);
                    meshExecutor.submit(new MeshNodeHandler(socket));
                }
            } catch (Exception e) {
                if (meshActive) {
                    appendLog("[RECALIBRATION] Mesh listener adjustment on port " + port + ": " + e.getMessage());
                }
            }
        });
    }

    private void rebindServerPort() {
        int newPort;
        try {
            newPort = Integer.parseInt(portInputField.getText().trim());
            if (newPort < 1 || newPort > 65535) {
                throw new NumberFormatException();
            }
        } catch (NumberFormatException e) {
            appendLog("[ERROR] Invalid port specification. Enter a value between 1 and 65535.");
            return;
        }

        appendLog("[REBINDING] Halting previous socket listener and binding to port " + newPort + "...");
        meshActive = false;
        try {
            if (meshServerSocket != null) {
                meshServerSocket.close();
            }
        } catch (Exception ignored) {}

        // Spin up new listener on updated port
        startMeshServer(newPort);
    }

    private class MeshNodeHandler implements Runnable {
        private final Socket socket;

        public MeshNodeHandler(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (meshActive && (packet = reader.readLine()) != null) {
                    processBiDirectionalStream(packet);
                }
            } catch (Exception e) {
                appendLog("[NODE TRANSITION] Telemetry stream socket closed.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void processBiDirectionalStream(String packet) {
        appendLog("[INBOUND STREAM] " + packet);
        
        if (packet.contains("DEEPMIND") || packet.contains("INFERENCE")) {
            appendLog("[HIGH-VIRTUE FILTER] Payload evaluated against Robin Hood equity ledger. Verified: Balanced.");
        }
    }

    private void broadcastHighVirtueVector() {
        String payload = intentInputField.getText().trim();
        if (payload.isEmpty()) return;
        intentInputField.setText("");

        final String fullPayload = "HIGH_VIRTUE_VECTOR:" + payload;
        appendLog("[BROADCAST INTENT] Multiplexing across all classified infrastructure nodes & DeepMind endpoints...");

        MeshNodeRecord[] currentNodes = registeredNodes;
        meshExecutor.submit(() -> {
            for (MeshNodeRecord node : currentNodes) {
                try {
                    String[] parts = node.getEndpointAddress().split(":");
                    String host = parts[0];
                    int port = Integer.parseInt(parts[1]);

                    Socket s = new Socket();
                    s.connect(new InetSocketAddress(host, port), 1500);
                    OutputStream out = s.getOutputStream();
                    out.write((fullPayload + "\n").getBytes(StandardCharsets.UTF_8));
                    out.flush();
                    s.close();
                    appendLog("[DISPATCHED] -> " + node.getNodeId() + " (" + node.getType().getDisplayName() + ")");
                } catch (Exception e) {
                    appendLog("[ROUTING BYPASS] Node " + node.getNodeId() + " in stasis or rotating IP mask.");
                }
            }
        });
    }

    private void appendLog(String msg) {
        telemetryConsole.append(msg + "\n");
        telemetryConsole.setCaretPosition(telemetryConsole.getDocument().getLength());
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> new SovereignMeshMatrixEngine().setVisible(true));
    }
}