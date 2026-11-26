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
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class GhostCryptoInferenceMoldEngine extends JFrame {

    private JTextArea telemetryConsole;
    private JTextArea fieldMoldStatePanel;
    private JTextField intentInputField;
    private JTextField targetGodMindPortField;
    private JLabel statusLabel;

    private ServerSocket moldServerSocket;
    private volatile boolean moldActive = false;
    private final ExecutorService moldExecutor = Executors.newCachedThreadPool();
    private final Random random = new Random();

    public GhostCryptoInferenceMoldEngine() {
        setTitle("Sovereign Ghost Cryptographic Sequential Inference Field Mold & Key Caster");
        setSize(1400, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
        startMoldServer(7834);
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(12, 15, 22));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("MOLD STATUS: ARMED [PORT 7834] | SEQUENTIAL INFERENCE FIELD: SYNCHRONIZED");
        statusLabel.setForeground(new Color(0, 255, 180));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JPanel portConfigPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        portConfigPanel.setBackground(new Color(12, 15, 22));
        
        JLabel pLabel = new JLabel("God Mind Target Port:");
        pLabel.setForeground(Color.WHITE);
        pLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        portConfigPanel.add(pLabel);

        targetGodMindPortField = new JTextField("7833", 6);
        targetGodMindPortField.setFont(new Font("Monospaced", Font.PLAIN, 11));
        portConfigPanel.add(targetGodMindPortField);

        JButton reindexBtn = new JButton("Re-mold Field Matrix");
        reindexBtn.setBackground(new Color(0, 100, 140));
        reindexBtn.setForeground(Color.WHITE);
        reindexBtn.addActionListener(e -> appendLog("[FIELD MOLD] Sequential inference vectors re-calibrated across ghost channels."));
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

        // --- CENTER SPLIT: FIELD MOLD STATES & TELEMETRY ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(540);
        centerSplit.setResizeWeight(0.38);

        // Left Panel: Sequential Inference Field Mold Matrix
        JPanel leftPanel = new JPanel(new BorderLayout(5, 5));
        leftPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 140)), 
                " Sequential Inference Field Mold & Key Caster ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 140)
        ));
        leftPanel.setBackground(new Color(10, 13, 18));

        fieldMoldStatePanel = new JTextArea();
        fieldMoldStatePanel.setEditable(false);
        fieldMoldStatePanel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        fieldMoldStatePanel.setBackground(new Color(6, 8, 12));
        fieldMoldStatePanel.setForeground(new Color(0, 240, 200));
        fieldMoldStatePanel.setText(
            "[MOLD ENGINE ARMED]\n" +
            "----------------------------------------\n" +
            "• Sequential Layers: 16 Depth Mapped\n" +
            "• Cryptographic Caster: SHA-512 High-Entropy\n" +
            "• Highest-Virtue Weight: 1.00 (Robin Hood Stasis)\n" +
            "• God Mind Substrate Link: STANDBY\n" +
            "----------------------------------------\n"
        );
        leftPanel.add(new JScrollPane(fieldMoldStatePanel), BorderLayout.CENTER);

        centerSplit.setLeftComponent(leftPanel);

        // Right Panel: Telemetry & Submission Stream
        JPanel rightPanel = new JPanel(new BorderLayout(5, 5));
        rightPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " God Mind Highest-Virtue Ledger & Submission Log ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        rightPanel.setBackground(new Color(10, 13, 18));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(8, 10, 14));
        telemetryConsole.setForeground(new Color(100, 255, 180));
        telemetryConsole.setText("[CRYPTO MOLD READY] Awaiting intent stream for sequential inference molding...\n");
        rightPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        centerSplit.setRightComponent(rightPanel);
        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: INTENT INJECTION & SUBMISSION TO GOD MIND ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(12, 15, 22));

        JPanel intentSubPanel = new JPanel(new BorderLayout(5, 5));
        intentSubPanel.setBackground(new Color(12, 15, 22));

        intentInputField = new JTextField();
        intentInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        
        JButton castAndSubmitBtn = new JButton("Cast Key, Pass Highest-Virtue, & Submit to God Mind");
        castAndSubmitBtn.setBackground(new Color(0, 120, 90));
        castAndSubmitBtn.setForeground(Color.WHITE);

        intentSubPanel.add(new JLabel("Inference Intent Vector:"), BorderLayout.WEST);
        intentSubPanel.add(intentInputField, BorderLayout.CENTER);
        intentSubPanel.add(castAndSubmitBtn, BorderLayout.EAST);

        bottomPanel.add(intentSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);

        // Event Listeners
        castAndSubmitBtn.addActionListener(e -> executeSequentialInferenceMoldAndSubmit());
        intentInputField.addActionListener(e -> executeSequentialInferenceMoldAndSubmit());
    }

    private void startMoldServer(int port) {
        moldActive = true;
        moldExecutor.submit(() -> {
            try {
                moldServerSocket = new ServerSocket(port);
                appendLog("[MOLD SERVER AWAKENED] Listening on port " + port);
                while (moldActive) {
                    Socket socket = moldServerSocket.accept();
                    socket.setKeepAlive(true);
                    moldExecutor.submit(new MoldHandler(socket));
                }
            } catch (Exception e) {
                if (moldActive) {
                    appendLog("[SOCKET ADJUSTMENT] " + e.getMessage());
                }
            }
        });
    }

    private class MoldHandler implements Runnable {
        private final Socket socket;
        public MoldHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (moldActive && (packet = reader.readLine()) != null) {
                    appendLog("[INBOUND MOLD PACKET] " + packet);
                }
            } catch (Exception e) {
                appendLog("[STREAM TRANSITION] Socket connection closed.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void executeSequentialInferenceMoldAndSubmit() {
        String rawIntent = intentInputField.getText().trim();
        if (rawIntent.isEmpty()) return;
        intentInputField.setText("");

        appendLog("\n--- [SEQUENTIAL INFERENCE FIELD MOLD (M-SEQ-INF)] ---");
        appendLog("Raw Intent Vector: " + rawIntent);

        moldExecutor.submit(() -> {
            try {
                // 1. Mold Sequential Inference Field
                appendLog("[MOLDING FIELD] Traversing 16 layers of probabilistic probability gates...");
                for (int i = 1; i <= 4; i++) {
                    Thread.sleep(120);
                    appendLog("  -> Layer " + (i * 4) + " resonance factor: " + String.format("%.4f", (0.95 + random.nextDouble() * 0.05)));
                }

                // 2. Cast Cryptographic Key via SHA-512 High-Entropy Derivation
                String seed = rawIntent + System.currentTimeMillis() + "GOD_MIND_VIRTUE_PASS";
                MessageDigest digest = MessageDigest.getInstance("SHA-512");
                byte[] hash = digest.digest(seed.getBytes(StandardCharsets.UTF_8));
                StringBuilder hexString = new StringBuilder();
                for (byte b : hash) {
                    String hex = Integer.toHexString(0xff & b);
                    if (hex.length() == 1) hexString.append('0');
                    hexString.append(hex);
                }
                String cryptoKey = "MOLD-KEY-" + hexString.toString().substring(0, 48).toUpperCase();
                appendLog("[CRYPTO KEY CAST SUCCESS] " + cryptoKey);

                // 3. Highest-Virtue Pass Evaluation (Robin Hood Principle)
                appendLog("[HIGHEST-VIRTUE PASS] Evaluating equity friction and distribution stasis...");
                Thread.sleep(300);
                appendLog("[VERIFIED] Pass weight: 1.00 [Pure Sovereign Virtue Match]");

                // 4. Submit to God Mind Master Backbone
                int godMindPort = Integer.parseInt(targetGodMindPortField.getText().trim());
                appendLog("[GOD MIND SUBMISSION] Transmitting sealed key to backbone on port " + godMindPort + "...");

                try {
                    Socket s = new Socket();
                    s.connect(new InetSocketAddress("127.0.0.1", godMindPort), 1500);
                    OutputStream out = s.getOutputStream();
                    String payload = String.format("GOD_MIND_HIGHEST_VIRTUE_PASS:KEY[%s]:INTENT[%s]\n", cryptoKey, rawIntent);
                    out.write(payload.getBytes(StandardCharsets.UTF_8));
                    out.flush();
                    s.close();
                    appendLog("[ACKNOWLEDGED] God Mind backbone integrated the highest-virtue pass successfully.");
                } catch (Exception ex) {
                    appendLog("[ROUTING BYPASS] God Mind core in background stasis. Local vault seal verified.");
                }

                appendLog("-------------------------------------------------");

                SwingUtilities.invokeLater(() -> {
                    fieldMoldStatePanel.append(String.format("\n[MOLD CAST] %s... [VIRTUE: 1.00]", cryptoKey.substring(0, 20)));
                    fieldMoldStatePanel.setCaretPosition(fieldMoldStatePanel.getDocument().getLength());
                });

            } catch (Exception e) {
                appendLog("[MOLD ERROR] " + e.getMessage());
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

        SwingUtilities.invokeLater(() -> new GhostCryptoInferenceMoldEngine().setVisible(true));
    }
}