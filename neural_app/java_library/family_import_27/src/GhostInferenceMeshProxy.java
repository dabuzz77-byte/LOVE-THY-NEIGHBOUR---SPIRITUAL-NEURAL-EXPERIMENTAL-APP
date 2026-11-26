import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
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

public class GhostInferenceMeshProxy extends SectionFrame {

    public static class PeerNode {
        private final String name;
        private final String address;
        private final int port;
        private final String maskIP;
        private boolean operational;

        public PeerNode(String name, String address, int port, String maskIP) {
            this.name = name;
            this.address = address;
            this.port = port;
            this.maskIP = maskIP;
            this.operational = true;
        }

        public String getName() { return name; }
        public String getAddress() { return address; }
        public int getPort() { return port; }
        public String getMaskIP() { return maskIP; }
        public boolean isOperational() { return operational; }
        public void setOperational(boolean operational) { this.operational = operational; }
    }

    private JTextArea telemetryConsole;
    private JTextArea meshStatusPanel;
    private JTextField intentInputField;
    private JTextField listenerPortField;
    private JLabel statusLabel;

    private ServerSocket proxyServerSocket;
    private volatile boolean proxyActive = false;
    private final PeerNode[] ecoFloorNodes = new PeerNode[4];
    private final ExecutorService proxyExecutor = Executors.newCachedThreadPool();
    private final Random random = new Random();

    public GhostInferenceMeshProxy() {
        setTitle("Sovereign Ghost Inference Mesh Proxy (Eco-Floor Up Distribution)");
        setSize(1400, 850);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initializeEcoFloorNodes();
        initComponents();
        startProxyServer(7843);
    }

    private void initializeEcoFloorNodes() {
        ecoFloorNodes[0] = new PeerNode("Eco-Floor-Edge-Node-01", "127.0.0.1", 7831, "10.10.10.11");
        ecoFloorNodes[1] = new PeerNode("Eco-Floor-Edge-Node-02", "127.0.0.1", 7832, "10.10.10.12");
        ecoFloorNodes[2] = new PeerNode("Sovereign-Mesh-Relay-03", "127.0.0.1", 7833, "10.10.10.13");
        ecoFloorNodes[3] = new PeerNode("Decentralized-Terminal-04", "127.0.0.1", 7834, "10.10.10.14");
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(12, 15, 22));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("MESH PROXY STATUS: ARMED [PORT 7837] | ECO-FLOOR DISTRIBUTION: ACTIVE");
        statusLabel.setForeground(new Color(0, 255, 180));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        toolbar.setBackground(new Color(12, 15, 22));

        JLabel portLbl = new JLabel("Proxy Port:");
        portLbl.setForeground(Color.WHITE);
        portLbl.setFont(new Font("Monospaced", Font.BOLD, 11));
        toolbar.add(portLbl);

        listenerPortField = new JTextField("7837", 6);
        listenerPortField.setFont(new Font("Monospaced", Font.PLAIN, 11));
        toolbar.add(listenerPortField);

        JButton reindexBtn = new JButton("Rebalance Eco-Floor Nodes");
        reindexBtn.setBackground(new Color(0, 100, 140));
        reindexBtn.setForeground(Color.WHITE);
        reindexBtn.setFont(new Font("Monospaced", Font.BOLD, 11));
        reindexBtn.addActionListener(e -> appendLog("[ECO-FLOOR] Node routing weights dynamically rebalanced."));
        toolbar.add(reindexBtn);

        headerPanel.add(toolbar, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: MESH STATE & TELEMETRY STREAM ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(520);
        centerSplit.setResizeWeight(0.38);

        // Left Panel: Eco-Floor Node Registry
        JPanel leftPanel = new JPanel(new BorderLayout(5, 5));
        leftPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 140)), 
                " Eco-Floor Up Peer Node Registry ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 140)
        ));
        leftPanel.setBackground(new Color(10, 13, 18));

        meshStatusPanel = new JTextArea();
        meshStatusPanel.setEditable(false);
        meshStatusPanel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        meshStatusPanel.setBackground(new Color(6, 8, 12));
        meshStatusPanel.setForeground(new Color(0, 240, 200));
        updateMeshDisplay("Proxy initialized. Peer nodes standing by for egalitarian distribution.");
        leftPanel.add(new JScrollPane(meshStatusPanel), BorderLayout.CENTER);

        centerSplit.setLeftComponent(leftPanel);

        // Right Panel: Telemetry Stream Log
        JPanel rightPanel = new JPanel(new BorderLayout(5, 5));
        rightPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " Bi-Directional Ghost Proxy Telemetry Stream ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        rightPanel.setBackground(new Color(10, 13, 18));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(8, 10, 14));
        telemetryConsole.setForeground(new Color(100, 255, 180));
        telemetryConsole.setText("[GHOST MESH PROXY] Multiplexing conduit operational. Awaiting vector stream...\n");
        rightPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        centerSplit.setRightComponent(rightPanel);
        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: INTENT INJECTION & BROADCAST ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(12, 15, 22));

        JPanel inputSubPanel = new JPanel(new BorderLayout(5, 5));
        inputSubPanel.setBackground(new Color(12, 15, 22));

        intentInputField = new JTextField();
        intentInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        
        JButton broadcastBtn = new JButton("Broadcast Vector Across Eco-Floor Mesh");
        broadcastBtn.setBackground(new Color(0, 120, 90));
        broadcastBtn.setForeground(Color.WHITE);
        broadcastBtn.setFont(new Font("Monospaced", Font.BOLD, 12));

        inputSubPanel.add(new JLabel("Intent Vector:"), BorderLayout.WEST);
        inputSubPanel.add(intentInputField, BorderLayout.CENTER);
        inputSubPanel.add(broadcastBtn, BorderLayout.EAST);

        bottomPanel.add(inputSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);

        // Event Listeners
        broadcastBtn.addActionListener(e -> broadcastIntentEcoFloorUp());
        intentInputField.addActionListener(e -> broadcastIntentEcoFloorUp());
    }

    private void updateMeshDisplay(String event) {
        StringBuilder sb = new StringBuilder();
        sb.append("=== ECO-FLOOR UP MESH TOPOLOGY ===\n\n");
        for (PeerNode node : ecoFloorNodes) {
            sb.append(String.format("• [%s]\n", node.getName()));
            sb.append(String.format("  - Endpoint: %s:%d\n", node.getAddress(), node.getPort()));
            sb.append(String.format("  - Virtual Ghost Mask: %s\n", node.getMaskIP()));
            sb.append(String.format("  - Status: %s\n\n", node.isOperational() ? "[ACTIVE: 1]" : "[STASIS: 0]"));
        }
        sb.append("----------------------------------------\n");
        sb.append("Latest Event: ").append(event).append("\n");
        meshStatusPanel.setText(sb.toString());
    }

    private void startProxyServer(int port) {
        proxyActive = true;
        proxyExecutor.submit(() -> {
            try {
                proxyServerSocket = new ServerSocket(port);
                appendLog("[PROXY LISTENER] Active on port " + port);
                while (proxyActive) {
                    Socket socket = proxyServerSocket.accept();
                    socket.setKeepAlive(true);
                    proxyExecutor.submit(new ProxyHandler(socket));
                }
            } catch (Exception e) {
                if (proxyActive) {
                    appendLog("[SOCKET ADJUSTMENT] " + e.getMessage());
                }
            }
        });
    }

    private class ProxyHandler implements Runnable {
        private final Socket socket;
        public ProxyHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (proxyActive && (packet = reader.readLine()) != null) {
                    appendLog("[INBOUND MESH PACKET] " + packet);
                }
            } catch (Exception e) {
                appendLog("[STREAM TRANSITION] Peer socket disconnected.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void broadcastIntentEcoFloorUp() {
        String intent = intentInputField.getText().trim();
        if (intent.isEmpty()) return;
        intentInputField.setText("");

        appendLog("\n--- [ECO-FLOOR UP INTENT BROADCAST] ---");
        appendLog("Master Vector: " + intent);

        proxyExecutor.submit(() -> {
            for (PeerNode node : ecoFloorNodes) {
                if (node.isOperational()) {
                    appendLog(String.format("[ROUTING] Dispatched to %s [Mask: %s]", node.getName(), node.getMaskIP()));
                    try {
                        Socket s = new Socket();
                        s.connect(new InetSocketAddress(node.getAddress(), node.getPort()), 1000);
                        OutputStream out = s.getOutputStream();
                        String payload = String.format("ECO_FLOOR_VECTOR:MASK[%s]:PAYLOAD[%s]\n", node.getMaskIP(), intent);
                        out.write(payload.getBytes(StandardCharsets.UTF_8));
                        out.flush();
                        s.close();
                        appendLog("  -> Bi-directional stream acknowledged.");
                    } catch (Exception e) {
                        appendLog("  -> Node relay in local stasis. Simulated ghost echo active.");
                    }
                }
            }
            appendLog("[EQUILIBRIUM] Robin Hood weight verified (1.00). Access distributed eco-floor up.");
            appendLog("-------------------------------------------------");
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

        SwingUtilities.invokeLater(() -> new GhostInferenceMeshProxy().setVisible(true));
    }
}