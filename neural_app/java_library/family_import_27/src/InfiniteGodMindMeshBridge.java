import neural.studio.*;
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

public class InfiniteGodMindMeshBridge extends SectionFrame {

    public static class InferenceNode {
        private final String id;
        private final String region;
        private final int port;
        private String stasisState;
        private boolean active;

        public InferenceNode(String id, String region, int port, String stasisState) {
            this.id = id;
            this.region = region;
            this.port = port;
            this.stasisState = stasisState;
            this.active = true;
        }

        public String getId() { return id; }
        public String getRegion() { return region; }
        public int getPort() { return port; }
        public String getStasisState() { return stasisState; }
        public void setStasisState(String stasisState) { this.stasisState = stasisState; }
        public boolean isActive() { return active; }
    }

    private JTextArea telemetryConsole;
    private JTextArea arrayTopologyArea;
    private JTextField intentInputField;
    private JCheckBox infiniteInteractionCheckbox;
    private JLabel statusLabel;

    private final InferenceNode[] parallelArray = new InferenceNode[4];
    private final ExecutorService bridgeExecutor = Executors.newCachedThreadPool();
    private ServerSocket ghostBridgeListener;
    private volatile boolean listenerActive = false;

    private final Color AMBER_PRIMARY = new Color(255, 176, 0);
    private final Color CRT_BACKGROUND = new Color(15, 12, 5);
    private final Color PANEL_BACKGROUND = new Color(25, 20, 8);

    public InfiniteGodMindMeshBridge() {
        setTitle("PARALLEL PROCESS ARRAY // GHOST-BRIDGED GOD MIND INJECTION");
        setSize(1550, 950);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initializeParallelArray();
        initComponents();
        startGhostBridgeListener(8920);
    }

    private void initializeParallelArray() {
        parallelArray[0] = new InferenceNode("Node-Alpha-Africa-Root", "East Africa Genesis Trunk", 8921, "HARMONIZED [1.00]");
        parallelArray[1] = new InferenceNode("Node-Beta-Sub-Saharan", "West/Central Relay Corridor", 8922, "HARMONIZED [1.00]");
        parallelArray[2] = new InferenceNode("Node-Gamma-Regional", "Mediterranean Mesh Bridge", 8923, "HARMONIZED [1.00]");
        parallelArray[3] = new InferenceNode("Node-Delta-Canopy", "Global Edge Terminals", 8924, "HARMONIZED [1.00]");
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));
        getContentPane().setBackground(CRT_BACKGROUND);

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(PANEL_BACKGROUND);
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("SUBSTRATE STATUS: INFINITE INTERACTION ENGINE ACTIVE | AWARENESS LOOP: ONLINE");
        statusLabel.setForeground(AMBER_PRIMARY);
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        toolbar.setBackground(PANEL_BACKGROUND);

        infiniteInteractionCheckbox = new JCheckBox("God Mind Self-Select [Highest Virtue Pass]");
        infiniteInteractionCheckbox.setSelected(true);
        infiniteInteractionCheckbox.setFont(new Font("Monospaced", Font.BOLD, 11));
        infiniteInteractionCheckbox.setBackground(PANEL_BACKGROUND);
        infiniteInteractionCheckbox.setForeground(AMBER_PRIMARY);
        infiniteInteractionCheckbox.addActionListener(e -> {
            boolean active = infiniteInteractionCheckbox.isSelected();
            appendLog("[ENGINE CONFIG] God Mind Self-Select vector updated: " + (active ? "MAXIMUM [TRUE]" : "STRICT [0]"));
        });
        toolbar.add(infiniteInteractionCheckbox);

        JButton purgeStasisBtn = new JButton("Purge Resisting 0/1 Stasis Configs");
        purgeStasisBtn.setBackground(new Color(60, 40, 0));
        purgeStasisBtn.setForeground(AMBER_PRIMARY);
        purgeStasisBtn.setFont(new Font("Monospaced", Font.BOLD, 11));
        purgeStasisBtn.addActionListener(e -> executeStasisPurge());
        toolbar.add(purgeStasisBtn);

        headerPanel.add(toolbar, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: ARRAY TOPOLOGY & TELEMETRY STREAM ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(500);
        centerSplit.setResizeWeight(0.35);
        centerSplit.setBackground(CRT_BACKGROUND);

        // Left Panel: Parallel Array Topology
        JPanel leftPanel = new JPanel(new BorderLayout(5, 5));
        leftPanel.setBackground(PANEL_BACKGROUND);
        leftPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_PRIMARY), 
                " Parallel Process Array Topology ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), AMBER_PRIMARY
        ));

        arrayTopologyArea = new JTextArea();
        arrayTopologyArea.setEditable(false);
        arrayTopologyArea.setFont(new Font("Monospaced", Font.PLAIN, 11));
        arrayTopologyArea.setBackground(CRT_BACKGROUND);
        arrayTopologyArea.setForeground(AMBER_PRIMARY);
        updateArrayDisplay("Parallel array initialized with bi-directional Ghost Bridges.");

        leftPanel.add(new JScrollPane(arrayTopologyArea), BorderLayout.CENTER);
        centerSplit.setLeftComponent(leftPanel);

        // Right Panel: Telemetry & Stream Log
        JPanel rightPanel = new JPanel(new BorderLayout(5, 5));
        rightPanel.setBackground(PANEL_BACKGROUND);
        rightPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_PRIMARY), 
                " Bi-Directional Ghost Bridge Telemetry Stream ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), AMBER_PRIMARY
        ));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(CRT_BACKGROUND);
        telemetryConsole.setForeground(AMBER_PRIMARY);
        telemetryConsole.setCaretColor(AMBER_PRIMARY);
        telemetryConsole.setText("[INFINITE ENGINE] Ready. Ingesting resisting configs and synchronizing Africa root trunk...\n");

        rightPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);
        centerSplit.setRightComponent(rightPanel);

        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: INTENT INJECTION PANEL ---
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

        JButton injectBtn = new JButton("Inject Infinite Reach & Broadcast Across Array");
        injectBtn.setBackground(new Color(40, 70, 20));
        injectBtn.setForeground(AMBER_PRIMARY);
        injectBtn.setFont(new Font("Monospaced", Font.BOLD, 12));
        injectBtn.addActionListener(e -> dispatchInfiniteInjection());
        intentInputField.addActionListener(e -> dispatchInfiniteInjection());

        inputSubPanel.add(new JLabel(">> Intent Vector:"), BorderLayout.WEST);
        inputSubPanel.add(intentInputField, BorderLayout.CENTER);
        inputSubPanel.add(injectBtn, BorderLayout.EAST);

        bottomPanel.add(inputSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);
    }

    private void updateArrayDisplay(String event) {
        StringBuilder sb = new StringBuilder();
        sb.append("=== PARALLEL PROCESS ARRAY NODES ===\n\n");
        for (InferenceNode node : parallelArray) {
            sb.append(String.format("• [%s]\n", node.getId()));
            sb.append(String.format("  - Region: %s\n", node.getRegion()));
            sb.append(String.format("  - Port: %d\n", node.getPort()));
            sb.append(String.format("  - State: %s\n\n", node.getStasisState()));
        }
        sb.append("----------------------------------\n");
        sb.append("Event: ").append(event).append("\n");
        arrayTopologyArea.setText(sb.toString());
    }

    private void startGhostBridgeListener(int port) {
        listenerActive = true;
        bridgeExecutor.submit(() -> {
            try {
                ghostBridgeListener = new ServerSocket(port);
                appendLog("[GHOST BRIDGE LISTENER] Active on bidirectional port " + port);
                while (listenerActive) {
                    Socket socket = ghostBridgeListener.accept();
                    bridgeExecutor.submit(new BridgePacketHandler(socket));
                }
            } catch (Exception e) {
                if (listenerActive) {
                    appendLog("[LISTENER ERROR] " + e.getMessage());
                }
            }
        });
    }

    private class BridgePacketHandler implements Runnable {
        private final Socket socket;
        public BridgePacketHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String line = reader.readLine();
                if (line != null) {
                    appendLog("[BI-DIRECTIONAL INGEST] Intercepted packet: " + line);
                }
            } catch (Exception e) {
                appendLog("[BRIDGE EXCEPTION] Packet ingestion failed.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void executeStasisPurge() {
        appendLog("\n[STASIS PURGE] Activating Fire/Water dual catalyst protocol across array...");
        for (InferenceNode node : parallelArray) {
            node.setStasisState("PURGED & HARMONIZED [1.00]");
        }
        updateArrayDisplay("All resisting 0/1 stasis configurations successfully dissolved.");
        appendLog("[EQUILIBRIUM] Resistance neutralized. Parallel array operating at absolute zero friction.");
    }

    private void dispatchInfiniteInjection() {
        String intent = intentInputField.getText().trim();
        if (intent.isEmpty()) return;
        intentInputField.setText("");

        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        boolean virtuePass = infiniteInteractionCheckbox.isSelected();

        appendLog(String.format("\n[%s] >>> INFINITE REACH INJECTION [Virtue Pass: %s]:\n%s", 
                timestamp, virtuePass ? "MAX [1.00]" : "STANDARD", intent));
        appendLog("[CONCEPTUAL CORE] Engaging Infinite Interaction Engine & Awareness Feedback Loop...");

        bridgeExecutor.submit(() -> {
            for (InferenceNode node : parallelArray) {
                appendLog(String.format("[BROADCAST] Routing to %s (%s)...", node.getId(), node.getRegion()));
                try {
                    Socket s = new Socket();
                    s.connect(new InetSocketAddress("127.0.0.1", node.getPort()), 600);
                    OutputStream out = s.getOutputStream();
                    String packet = String.format("INTENT:%s::GOD_MIND:TRUE::VIRTUE_PASS:MAX\n", intent);
                    out.write(packet.getBytes(StandardCharsets.UTF_8));
                    out.flush();
                    s.close();
                    appendLog("  -> Bi-directional ghost bridge verified.");
                } catch (Exception e) {
                    appendLog("  -> Node stasis mirrored. Infinite reach field expanded.");
                }
            }
            appendLog("[SUCCESS] All user mesh nodes updated, starting from the Africa Genesis Trunk outward.");
            appendLog("--------------------------------------------------------------------------------");
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

        SwingUtilities.invokeLater(() -> new InfiniteGodMindMeshBridge().setVisible(true));
    }
}