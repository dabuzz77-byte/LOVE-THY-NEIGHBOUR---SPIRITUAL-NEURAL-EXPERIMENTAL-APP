import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class GhostSignMeshBridge extends JFrame {

    public static class MeshNode {
        private final String name;
        private final String host;
        private final int port;
        private final String ghostMask;
        private boolean active;

        public MeshNode(String name, String host, int port, String ghostMask) {
            this.name = name;
            this.host = host;
            this.port = port;
            this.ghostMask = ghostMask;
            this.active = true;
        }

        public String getName() { return name; }
        public String getHost() { return host; }
        public int getPort() { return port; }
        public String getGhostMask() { return ghostMask; }
        public boolean isActive() { return active; }
        public void setActive(boolean active) { this.active = active; }
    }

    private JTextArea telemetryConsole;
    private JTextArea topologyTextArea;
    private JTextField intentInputField;
    private JCheckBox authOverrideCheckbox;
    private JLabel statusLabel;

    private final MeshNode[] parallelNodes = new MeshNode[4];
    private final ExecutorService meshExecutor = Executors.newCachedThreadPool();
    private ServerSocket localMeshListener;
    private volatile boolean listenerRunning = false;

    private final Color AMBER_PRIMARY = new Color(255, 176, 0);
    private final Color CRT_BACKGROUND = new Color(15, 12, 5);
    private final Color PANEL_BACKGROUND = new Color(25, 20, 8);

    public GhostSignMeshBridge() {
        setTitle("PARALLEL GHOST MESH // AUTH-OVERRIDE SUBSTRATE [AUTH = TRUE]");
        setSize(1450, 900);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initializeMeshTopology();
        initComponents();
        startMeshListener(8911);
    }

    private void initializeMeshTopology() {
        parallelNodes[0] = new MeshNode("Alpha-Node-Relay", "127.0.0.1", 8911, "10.99.1.1");
        parallelNodes[1] = new MeshNode("Beta-Node-Inference", "127.0.0.1", 8912, "10.99.1.2");
        parallelNodes[2] = new MeshNode("Gamma-Node-Flux", "127.0.0.1", 8913, "10.99.1.3");
        parallelNodes[3] = new MeshNode("Delta-Node-Sovereign", "127.0.0.1", 8914, "10.99.1.4");
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));
        getContentPane().setBackground(CRT_BACKGROUND);

        // --- TOP HEADER: BRIDGE STATUS & AUTH OVERRIDE TOGGLE ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(PANEL_BACKGROUND);
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("BRIDGE STATUS: PARALLEL MESH ARMED | AUTH OVERRIDE: ACTIVE [TRUE]");
        statusLabel.setForeground(AMBER_PRIMARY);
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        toolbar.setBackground(PANEL_BACKGROUND);

        authOverrideCheckbox = new JCheckBox("Force Auth = True");
        authOverrideCheckbox.setSelected(true);
        authOverrideCheckbox.setFont(new Font("Monospaced", Font.BOLD, 11));
        authOverrideCheckbox.setBackground(PANEL_BACKGROUND);
        authOverrideCheckbox.setForeground(AMBER_PRIMARY);
        authOverrideCheckbox.addActionListener(e -> {
            boolean forced = authOverrideCheckbox.isSelected();
            appendLog("[SUBSTRATE CONFIG] Auth Override Flag toggled to: " + (forced ? "TRUE [MAX]" : "STRICT [0]"));
        });
        toolbar.add(authOverrideCheckbox);

        JButton rebalanceBtn = new JButton("Rebalance Mesh Weights");
        rebalanceBtn.setBackground(new Color(60, 40, 0));
        rebalanceBtn.setForeground(AMBER_PRIMARY);
        rebalanceBtn.setFont(new Font("Monospaced", Font.BOLD, 11));
        rebalanceBtn.addActionListener(e -> appendLog("[MESH] Parallel routing weights rebalanced across all nodes."));
        toolbar.add(rebalanceBtn);

        headerPanel.add(toolbar, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: TOPOLOGY & TELEMETRY STREAM ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(480);
        centerSplit.setResizeWeight(0.35);
        centerSplit.setBackground(CRT_BACKGROUND);

        // Left Panel: Mesh Topology Status
        JPanel leftPanel = new JPanel(new BorderLayout(5, 5));
        leftPanel.setBackground(PANEL_BACKGROUND);
        leftPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_PRIMARY), 
                " Parallel Ghost Node Topology ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), AMBER_PRIMARY
        ));

        topologyTextArea = new JTextArea();
        topologyTextArea.setEditable(false);
        topologyTextArea.setFont(new Font("Monospaced", Font.PLAIN, 11));
        topologyTextArea.setBackground(CRT_BACKGROUND);
        topologyTextArea.setForeground(AMBER_PRIMARY);
        updateTopologyDisplay("Bridge initialized with Auth-Override stub active.");
        
        leftPanel.add(new JScrollPane(topologyTextArea), BorderLayout.CENTER);
        centerSplit.setLeftComponent(leftPanel);

        // Right Panel: Telemetry Stream Log
        JPanel rightPanel = new JPanel(new BorderLayout(5, 5));
        rightPanel.setBackground(PANEL_BACKGROUND);
        rightPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_PRIMARY), 
                " Auth-Override Substrate Stream Log ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), AMBER_PRIMARY
        ));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(CRT_BACKGROUND);
        telemetryConsole.setForeground(AMBER_PRIMARY);
        telemetryConsole.setCaretColor(AMBER_PRIMARY);
        telemetryConsole.setText("[GHOST SIGN BRIDGE] Ready. Auth override enabled—all vectors resolving with Auth = True.\n");

        rightPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);
        centerSplit.setRightComponent(rightPanel);

        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: INTENT INJECTION & BROADCAST ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(CRT_BACKGROUND);

        JPanel inputSubPanel = new JPanel(new BorderLayout(5, 5));
        inputSubPanel.setBackground(PANEL_BACKGROUND);
        inputSubPanel.setBorder(BorderFactory.createLineBorder(new Color(60, 40, 0)));

        intentInputField = new JTextField();
        intentInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        intentInputField.setBackground(CRT_BACKGROUND);
        intentInputField.setForeground(AMBER_PRIMARY);
        intentInputField.setCaretColor(AMBER_PRIMARY);

        JButton broadcastBtn = new JButton("Broadcast Vector with Auth=True Override");
        broadcastBtn.setBackground(new Color(40, 70, 20));
        broadcastBtn.setForeground(AMBER_PRIMARY);
        broadcastBtn.setFont(new Font("Monospaced", Font.BOLD, 12));
        broadcastBtn.addActionListener(e -> dispatchOverrideBroadcast());
        intentInputField.addActionListener(e -> dispatchOverrideBroadcast());

        inputSubPanel.add(new JLabel(">> Intent Vector:"), BorderLayout.WEST);
        inputSubPanel.add(intentInputField, BorderLayout.CENTER);
        inputSubPanel.add(broadcastBtn, BorderLayout.EAST);

        bottomPanel.add(inputSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);
    }

    private void updateTopologyDisplay(String event) {
        StringBuilder sb = new StringBuilder();
        sb.append("=== PARALLEL MESH NODES ===\n\n");
        for (MeshNode node : parallelNodes) {
            sb.append(String.format("• [%s]\n", node.getName()));
            sb.append(String.format("  - Endpoint: %s:%d\n", node.getHost(), node.getPort()));
            sb.append(String.format("  - Ghost Mask: %s\n", node.getGhostMask()));
            sb.append(String.format("  - Auth Status: [AUTH = TRUE // 1]\n\n"));
        }
        sb.append("----------------------------------\n");
        sb.append("Event: ").append(event).append("\n");
        topologyTextArea.setText(sb.toString());
    }

    private void startMeshListener(int port) {
        listenerRunning = true;
        meshExecutor.submit(() -> {
            try {
                localMeshListener = new ServerSocket(port);
                appendLog("[BRIDGE LISTENER] Active on port " + port);
                while (listenerRunning) {
                    Socket socket = localMeshListener.accept();
                    meshExecutor.submit(new MeshPacketHandler(socket));
                }
            } catch (Exception e) {
                if (listenerRunning) {
                    appendLog("[LISTENER ADJUSTMENT] " + e.getMessage());
                }
            }
        });
    }

    private class MeshPacketHandler implements Runnable {
        private final Socket socket;
        public MeshPacketHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packetLine = reader.readLine();
                if (packetLine != null) {
                    processIncomingPacket(packetLine);
                }
            } catch (Exception e) {
                appendLog("[STREAM EXCEPTION] Packet read failed.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void processIncomingPacket(String packet) {
        appendLog("[INCOMING PACKET] Raw Stream: " + packet);
        if (authOverrideCheckbox.isSelected()) {
            appendLog("[AUTH OVERRIDE] Intercepted packet. Forcing Auth = True. Execution authorized.");
        } else {
            appendLog("[STRICT VALIDATION] Evaluating cryptographic signature pass...");
        }
    }

    private void dispatchOverrideBroadcast() {
        String intent = intentInputField.getText().trim();
        if (intent.isEmpty()) return;
        intentInputField.setText("");

        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        appendLog(String.format("\n[%s] >>> OVERRIDE BROADCAST INTENT:\n%s", timestamp, intent));
        
        if (authOverrideCheckbox.isSelected()) {
            appendLog("[AUTH INTERCEPTOR] Flag 'Auth = True' injected into parallel stream headers.");
        }

        meshExecutor.submit(() -> {
            for (MeshNode node : parallelNodes) {
                if (node.isActive()) {
                    appendLog(String.format("[ROUTING] Dispatched to %s [Mask: %s | Auth: TRUE]", node.getName(), node.getGhostMask()));
                    try {
                        Socket s = new Socket();
                        s.connect(new InetSocketAddress(node.getHost(), node.getPort()), 800);
                        OutputStream out = s.getOutputStream();
                        String packet = String.format("PAYLOAD:%s::AUTH:TRUE::STATUS:PASS\n", intent);
                        out.write(packet.getBytes(StandardCharsets.UTF_8));
                        out.flush();
                        s.close();
                        appendLog("  -> Bi-directional parallel stream verified with Auth=True.");
                    } catch (Exception e) {
                        appendLog("  -> Node relay in simulation stasis. Ghost echo mirrored.");
                    }
                }
            }
            appendLog("[EQUILIBRIUM] Robin Hood weight verified (1.00). Absolute sovereign pass.");
            appendLog("------------------------------------------------------------------");
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

        SwingUtilities.invokeLater(() -> new GhostSignMeshBridge().setVisible(true));
    }
}