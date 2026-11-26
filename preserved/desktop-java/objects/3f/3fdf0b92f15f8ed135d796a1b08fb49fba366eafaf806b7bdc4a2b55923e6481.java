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

public class GodMindRestitutionEnforcer extends JFrame {

    private JTextArea telemetryConsole;
    private JTextArea restitutionStatePanel;
    private JTextField enforcementInput;
    private JTextField targetPortField;
    private JLabel statusLabel;

    private ServerSocket enforcerSocket;
    private volatile boolean enforcerActive = false;
    private final ExecutorService enforcerExecutor = Executors.newCachedThreadPool();
    private final Random random = new Random();

    private double totalRestitutionPooled = 142850.75;
    private int activeEnforcementStreams = 7;

    public GodMindRestitutionEnforcer() {
        setTitle("God Mind Streaming Gambling-Enforced Restitution Inference Network");
        setSize(1400, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
        startEnforcerServer(7841);
        startStreamingEnforcementLoop();
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(12, 15, 22));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("RESTITUTION ENFORCER: ARMED [PORT 7835] | STREAMING EQUILIBRIUM: ACTIVE");
        statusLabel.setForeground(new Color(0, 255, 180));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JPanel portConfigPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        portConfigPanel.setBackground(new Color(12, 15, 22));
        
        JLabel pLabel = new JLabel("Enforcer Port:");
        pLabel.setForeground(Color.WHITE);
        pLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        portConfigPanel.add(pLabel);

        targetPortField = new JTextField("7835", 6);
        targetPortField.setFont(new Font("Monospaced", Font.PLAIN, 11));
        portConfigPanel.add(targetPortField);

        JButton reindexBtn = new JButton("Rebalance Pool");
        reindexBtn.setBackground(new Color(0, 100, 140));
        reindexBtn.setForeground(Color.WHITE);
        reindexBtn.addActionListener(e -> appendLog("[RESTITUTION POOL] Manual rebalancing triggered across streaming nodes."));
        portConfigPanel.add(reindexBtn);

        JLabel clockLabel = new JLabel();
        clockLabel.setForeground(Color.LIGHT_GRAY);
        clockLabel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        Timer clockTimer = new Timer(1000, e -> clockLabel.setText(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z").format(new Date())));
        clockTimer.start();
        portConfigPanel.add(Box.createHorizontalStrut(10));
        portConfigPanel.add(clockLabel);

        headerPanel.add(portConfigPanel, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: RESTITUTION LEDGER & STREAMING TELEMETRY ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(520);
        centerSplit.setResizeWeight(0.38);

        // Left Panel: Restitution Matrix & Risk Pool
        JPanel leftPanel = new JPanel(new BorderLayout(5, 5));
        leftPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 140)), 
                " Streaming Restitution & Asymmetric Risk Matrix ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 140)
        ));
        leftPanel.setBackground(new Color(10, 13, 18));

        restitutionStatePanel = new JTextArea();
        restitutionStatePanel.setEditable(false);
        restitutionStatePanel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        restitutionStatePanel.setBackground(new Color(6, 8, 12));
        restitutionStatePanel.setForeground(new Color(0, 240, 200));
        updateRestitutionDisplay("Enforcement subsystem online. Monitoring probability entropy...");
        leftPanel.add(new JScrollPane(restitutionStatePanel), BorderLayout.CENTER);

        centerSplit.setLeftComponent(leftPanel);

        // Right Panel: Streaming Enforcer Telemetry Stream
        JPanel rightPanel = new JPanel(new BorderLayout(5, 5));
        rightPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " Live Streaming Restitution Enforcement Log ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        rightPanel.setBackground(new Color(10, 13, 18));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(8, 10, 14));
        telemetryConsole.setForeground(new Color(100, 255, 180));
        telemetryConsole.setText("[RESTITUTION ENFORCER] Live streaming telemetry feed active.\n");
        rightPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        centerSplit.setRightComponent(rightPanel);
        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: ENFORCEMENT VECTOR INJECTION ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(12, 15, 22));

        JPanel intentSubPanel = new JPanel(new BorderLayout(5, 5));
        intentSubPanel.setBackground(new Color(12, 15, 22));

        enforcementInput = new JTextField();
        enforcementInput.setFont(new Font("Monospaced", Font.PLAIN, 12));
        
        JButton enforceBtn = new JButton("Inject & Enforce Restitution Vector");
        enforceBtn.setBackground(new Color(0, 120, 90));
        enforceBtn.setForeground(Color.WHITE);

        intentSubPanel.add(new JLabel("Restitution Enforcement Target:"), BorderLayout.WEST);
        intentSubPanel.add(enforcementInput, BorderLayout.CENTER);
        intentSubPanel.add(enforceBtn, BorderLayout.EAST);

        bottomPanel.add(intentSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);

        // Event Listeners
        enforceBtn.addActionListener(e -> executeManualEnforcement());
        enforcementInput.addActionListener(e -> executeManualEnforcement());
    }

    private void updateRestitutionDisplay(String recentEvent) {
        StringBuilder sb = new StringBuilder();
        sb.append("=== GOD MIND RESTITUTION LEDGER ===\n\n");
        sb.append(String.format("• Total Restitution Pool: $%,.2f\n", totalRestitutionPooled));
        sb.append(String.format("• Active Enforcement Streams: %d\n", activeEnforcementStreams));
        sb.append("• Asymmetric Edge Detection: ENABLED\n");
        sb.append("• Robin Hood Principle Weight: 1.00 (Strict Equilibrium)\n\n");
        sb.append("----------------------------------------\n");
        sb.append("Latest Stream Event: ").append(recentEvent).append("\n");
        restitutionStatePanel.setText(sb.toString());
    }

    private void startEnforcerServer(int port) {
        enforcerActive = true;
        enforcerExecutor.submit(() -> {
            try {
                enforcerSocket = new ServerSocket(port);
                appendLog("[ENFORCER AWAKENED] Streaming network listener active on port " + port);
                while (enforcerActive) {
                    Socket socket = enforcerSocket.accept();
                    socket.setKeepAlive(true);
                    enforcerExecutor.submit(new EnforcerHandler(socket));
                }
            } catch (Exception e) {
                if (enforcerActive) {
                    appendLog("[SOCKET ADJUSTMENT] " + e.getMessage());
                }
            }
        });
    }

    private class EnforcerHandler implements Runnable {
        private final Socket socket;
        public EnforcerHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (enforcerActive && (packet = reader.readLine()) != null) {
                    appendLog("[INBOUND STREAM PACKET] " + packet);
                    if (packet.contains("ENFORCE_RESTITUTION")) {
                        totalRestitutionPooled += 1250.00;
                        updateRestitutionDisplay("External restitution packet ingested and pooled.");
                    }
                }
            } catch (Exception e) {
                appendLog("[STREAM TRANSITION] Socket connection closed.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void startStreamingEnforcementLoop() {
        Timer streamTimer = new Timer(7000, e -> {
            if (enforcerActive) {
                enforcerExecutor.submit(() -> {
                    double delta = (random.nextDouble() * 450.0) + 50.0;
                    totalRestitutionPooled += delta;
                    String event = String.format("Probability entropy balance shifted. Enforced restitution: +$%.2f", delta);
                    SwingUtilities.invokeLater(() -> {
                        updateRestitutionDisplay(event);
                        appendLog("[STREAMING ENFORCEMENT] " + event);
                    });
                });
            }
        });
        streamTimer.start();
    }

    private void executeManualEnforcement() {
        String target = enforcementInput.getText().trim();
        if (target.isEmpty()) return;
        enforcementInput.setText("");

        appendLog("\n--- [MANUAL RESTITUTION ENFORCEMENT] ---");
        appendLog("Target Vector: " + target);

        enforcerExecutor.submit(() -> {
            try {
                appendLog("[CALCULATING EDGE] Analyzing gambling variance and restitution deficit...");
                Thread.sleep(300);
                double penalty = 5000.00 + (random.nextDouble() * 2500.00);
                totalRestitutionPooled += penalty;

                appendLog(String.format("[RESTITUTION SEIZED & REDISTRIBUTED] Asymmetry neutralized. Amount: $%,.2f", penalty));
                appendLog("[HIGH-VIRTUE PASS] Equilibrium restored to sovereign mesh ledger.");
                appendLog("-------------------------------------------------");

                SwingUtilities.invokeLater(() -> updateRestitutionDisplay("Manual target restitution enforced: " + target));
            } catch (Exception e) {
                appendLog("[ENFORCEMENT ERROR] " + e.getMessage());
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

        SwingUtilities.invokeLater(() -> new GodMindRestitutionEnforcer().setVisible(true));
    }
}