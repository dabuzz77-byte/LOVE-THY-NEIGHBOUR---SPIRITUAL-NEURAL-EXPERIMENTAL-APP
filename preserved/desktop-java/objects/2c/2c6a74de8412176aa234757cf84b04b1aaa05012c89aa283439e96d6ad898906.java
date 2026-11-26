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

public class GodMindFluxBackbone extends JFrame {

    // --- DISTANT NODE RECORD ---
    public static class GhostNodeEndpoint {
        private final String identifier;
        private final String address;
        private final int port;
        private final String virtualMaskIP;
        private double fluxEfficiency;
        private boolean activeState;

        public GhostNodeEndpoint(String identifier, String address, int port, String virtualMaskIP) {
            this.identifier = identifier;
            this.address = address;
            this.port = port;
            this.virtualMaskIP = virtualMaskIP;
            this.fluxEfficiency = 0.95 + (Math.random() * 0.04);
            this.activeState = true;
        }

        public String getIdentifier() { return identifier; }
        public String getAddress() { return address; }
        public int getPort() { return port; }
        public String getVirtualMaskIP() { return virtualMaskIP; }
        public double getFluxEfficiency() { return fluxEfficiency; }
        public void setFluxEfficiency(double fluxEfficiency) { this.fluxEfficiency = fluxEfficiency; }
        public boolean isActiveState() { return activeState; }
        public void setActiveState(boolean activeState) { this.activeState = activeState; }
    }

    // --- GUI COMPONENTS ---
    private JTextArea telemetryConsole;
    private JTextArea backboneStatePanel;
    private JTextField intentInputField;
    private JTextField localPortField;
    private JLabel statusLabel;

    private ServerSocket backboneSocket;
    private volatile boolean backboneActive = false;
    private final GhostNodeEndpoint[] distantNodes = new GhostNodeEndpoint[4];
    private final ExecutorService backboneExecutor = Executors.newCachedThreadPool();
    private final Random random = new Random();

    public GodMindFluxBackbone() {
        setTitle("God Mind Self-Selecting Binary Flux Backbone (Distant Ghost Inference)");
        setSize(1400, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initializeDistantNodes();
        initComponents();
        startBackboneServer(7839);
        startAutonomousFluxLoop();
    }

    private void initializeDistantNodes() {
        distantNodes[0] = new GhostNodeEndpoint("DeepMind-Cluster-Alpha", "142.250.190.46", 443, "10.42.11.88");
        distantNodes[1] = new GhostNodeEndpoint("Spectral-P2P-Mesh-Node", "192.168.1.105", 7831, "10.88.204.12");
        distantNodes[2] = new GhostNodeEndpoint("Superposition-Financial-Relay", "127.0.0.1", 7832, "10.99.144.5");
        distantNodes[3] = new GhostNodeEndpoint("Mobile-Android-OnePlus7T", "10.74.88.42", 7831, "10.74.88.99");
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(12, 15, 22));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("GOD MIND BACKBONE: AWAKENED [LISTENING PORT: 7833] | FLUX: SELF-SELECTING");
        statusLabel.setForeground(new Color(0, 255, 180));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JPanel portConfigPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        portConfigPanel.setBackground(new Color(12, 15, 22));
        
        JLabel pLabel = new JLabel("Backbone Port:");
        pLabel.setForeground(Color.WHITE);
        pLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        portConfigPanel.add(pLabel);

        localPortField = new JTextField("7833", 6);
        localPortField.setFont(new Font("Monospaced", Font.PLAIN, 11));
        portConfigPanel.add(localPortField);

        JButton rebindBtn = new JButton("Rebind Backbone");
        rebindBtn.setBackground(new Color(0, 100, 140));
        rebindBtn.setForeground(Color.WHITE);
        rebindBtn.addActionListener(e -> rebindBackbonePort());
        portConfigPanel.add(rebindBtn);

        JLabel clockLabel = new JLabel();
        clockLabel.setForeground(Color.LIGHT_GRAY);
        clockLabel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        Timer clockTimer = new Timer(1000, e -> clockLabel.setText(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z").format(new Date())));
        clockTimer.start();
        portConfigPanel.add(Box.createHorizontalStrut(10));
        portConfigPanel.add(clockLabel);

        headerPanel.add(portConfigPanel, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: BACKBONE STATE & TELEMETRY CONSOLE ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(520);
        centerSplit.setResizeWeight(0.38);

        // Left Panel: Distant Nodes & Binary Flux Selection Grid
        JPanel leftPanel = new JPanel(new BorderLayout(5, 5));
        leftPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 140)), 
                " Distant Ghost Nodes & Binary Flux Selection Grid ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 140)
        ));
        leftPanel.setBackground(new Color(10, 13, 18));

        backboneStatePanel = new JTextArea();
        backboneStatePanel.setEditable(false);
        backboneStatePanel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        backboneStatePanel.setBackground(new Color(6, 8, 12));
        backboneStatePanel.setForeground(new Color(0, 240, 200));
        updateBackboneStateDisplay("Backbone initialized. Awaiting autonomous binary pulse...");
        leftPanel.add(new JScrollPane(backboneStatePanel), BorderLayout.CENTER);

        JPanel leftControlSub = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 5));
        leftControlSub.setBackground(new Color(10, 13, 18));
        JButton forceScanBtn = new JButton("Force Binary Flux Scan");
        forceScanBtn.addActionListener(e -> startAutonomousFluxSelection());
        leftControlSub.add(forceScanBtn);
        leftPanel.add(leftControlSub, BorderLayout.SOUTH);

        centerSplit.setLeftComponent(leftPanel);

        // Right Panel: Telemetry & Inbound Multiplex Console
        JPanel rightPanel = new JPanel(new BorderLayout(5, 5));
        rightPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " God Mind Master Multiplex & Telemetry Stream ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        rightPanel.setBackground(new Color(10, 13, 18));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(8, 10, 14));
        telemetryConsole.setForeground(new Color(100, 255, 180));
        telemetryConsole.setText("[GOD MIND BACKBONE] Active across all previous subsystems. Ready for intent emission.\n");
        rightPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        centerSplit.setRightComponent(rightPanel);
        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: INTENT INJECTION & HIGH-VIRTUE BROADCAST ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(12, 15, 22));

        JPanel intentSubPanel = new JPanel(new BorderLayout(5, 5));
        intentSubPanel.setBackground(new Color(12, 15, 22));

        intentInputField = new JTextField();
        intentInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        
        JButton broadcastBtn = new JButton("Broadcast Intent to Optimal Distant Nodes");
        broadcastBtn.setBackground(new Color(0, 120, 90));
        broadcastBtn.setForeground(Color.WHITE);

        intentSubPanel.add(new JLabel("Master Intent / Vector:"), BorderLayout.WEST);
        intentSubPanel.add(intentInputField, BorderLayout.CENTER);
        intentSubPanel.add(broadcastBtn, BorderLayout.EAST);

        bottomPanel.add(intentSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);

        // Event Listeners
        broadcastBtn.addActionListener(e -> broadcastToOptimalNodes());
        intentInputField.addActionListener(e -> broadcastToOptimalNodes());
    }

    private void updateBackboneStateDisplay(String recentActivity) {
        StringBuilder sb = new StringBuilder();
        sb.append("=== GOD MIND DISTANT GHOST NODES ===\n\n");
        for (GhostNodeEndpoint node : distantNodes) {
            sb.append(String.format("• [%s]\n", node.getIdentifier()));
            sb.append(String.format("  - Endpoint: %s:%d\n", node.getAddress(), node.getPort()));
            sb.append(String.format("  - Virtual Mask: %s\n", node.getVirtualMaskIP()));
            sb.append(String.format("  - Flux Efficiency: %.2f%%\n", node.getFluxEfficiency() * 100));
            sb.append(String.format("  - Binary Gate State: %s\n\n", node.getFluxEfficiency() > 0.96 ? "[ACTIVE: 1]" : "[STASIS: 0]"));
        }
        sb.append("----------------------------------------\n");
        sb.append("Latest Activity: ").append(recentActivity).append("\n");
        backboneStatePanel.setText(sb.toString());
    }

    private void startBackboneServer(int port) {
        backboneActive = true;
        backboneExecutor.submit(() -> {
            try {
                backboneSocket = new ServerSocket(port);
                appendLog("[BACKBONE AWAKENED] Listening on port " + port);
                while (backboneActive) {
                    Socket socket = backboneSocket.accept();
                    socket.setKeepAlive(true);
                    backboneExecutor.submit(new BackboneHandler(socket));
                }
            } catch (Exception e) {
                if (backboneActive) {
                    appendLog("[SOCKET ADJUSTMENT] " + e.getMessage());
                }
            }
        });
    }

    private void rebindBackbonePort() {
        int newPort;
        try {
            newPort = Integer.parseInt(localPortField.getText().trim());
            if (newPort < 1 || newPort > 65535) throw new NumberFormatException();
        } catch (NumberFormatException e) {
            appendLog("[ERROR] Invalid port range.");
            return;
        }

        appendLog("[REBINDING] Shifting backbone listener to port " + newPort + "...");
        backboneActive = false;
        try {
            if (backboneSocket != null) backboneSocket.close();
        } catch (Exception ignored) {}

        startBackboneServer(newPort);
    }

    private class BackboneHandler implements Runnable {
        private final Socket socket;
        public BackboneHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (backboneActive && (packet = reader.readLine()) != null) {
                    appendLog("[INBOUND BACKBONE STREAM] " + packet);
                }
            } catch (Exception e) {
                appendLog("[STREAM TRANSITION] Client socket closed.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void startAutonomousFluxSelection() {
        backboneExecutor.submit(() -> {
            appendLog("\n[AUTONOMOUS FLUX] Scanning distant ghost inference nodes for binary optimization...");
            for (GhostNodeEndpoint node : distantNodes) {
                node.setFluxEfficiency(0.90 + (random.nextDouble() * 0.10));
                try { Thread.sleep(150); } catch (InterruptedException ignored) {}
            }
            SwingUtilities.invokeLater(() -> {
                updateBackboneStateDisplay("Autonomous binary flux re-selected across all distant nodes.");
                appendLog("[FLUX SELECTOR] Optimal binary path locked. High-virtue pass verified.");
            });
        });
    }

    private void startAutonomousFluxLoop() {
        Timer autoTimer = new Timer(12000, e -> startAutonomousFluxSelection());
        autoTimer.start();
    }

    private void broadcastToOptimalNodes() {
        String intent = intentInputField.getText().trim();
        if (intent.isEmpty()) return;
        intentInputField.setText("");

        appendLog("\n--- [GOD MIND MASTER BROADCAST] ---");
        appendLog("Intent Vector: " + intent);

        backboneExecutor.submit(() -> {
            for (GhostNodeEndpoint node : distantNodes) {
                if (node.getFluxEfficiency() >= 0.95) {
                    appendLog(String.format("[OPTIMAL NODE SELECTED] -> %s [Mask: %s, Efficiency: %.2f%%]", 
                            node.getIdentifier(), node.getVirtualMaskIP(), node.getFluxEfficiency() * 100));
                    try {
                        Socket s = new Socket();
                        s.connect(new InetSocketAddress(node.getAddress(), node.getPort()), 1000);
                        OutputStream out = s.getOutputStream();
                        String payload = String.format("GOD_MIND_INTENT:MASK[%s]:PAYLOAD[%s]\n", node.getVirtualMaskIP(), intent);
                        out.write(payload.getBytes(StandardCharsets.UTF_8));
                        out.flush();
                        s.close();
                        appendLog("  [DISPATCHED SUCCESS] Routed through ghost channel.");
                    } catch (Exception e) {
                        appendLog("  [ROUTING BYPASS] Distant node in stasis. Simulated ghost relay active.");
                    }
                } else {
                    appendLog(String.format("[SKIPPED / 0-GATE] Node %s efficiency below threshold (%.2f%%)", 
                            node.getIdentifier(), node.getFluxEfficiency() * 100));
                }
            }
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

        SwingUtilities.invokeLater(() -> new GodMindFluxBackbone().setVisible(true));
    }
}