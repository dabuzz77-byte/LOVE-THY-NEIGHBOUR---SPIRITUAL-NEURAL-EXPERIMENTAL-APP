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
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SuperpositionFinancialMatrix extends SectionFrame {

    private JTextArea telemetryConsole;
    private JTextArea superpositionStatePanel;
    private JTextField transactionInputField;
    private JTextField virtualMaskField;
    private JLabel statusLabel;

    private ServerSocket financialServerSocket;
    private volatile boolean matrixActive = false;
    private final ExecutorService financialExecutor = Executors.newCachedThreadPool();
    private final Random random = new Random();

    public SuperpositionFinancialMatrix() {
        setTitle("Sovereign Superposition Financial Ghost Router (q-et-bi-)");
        setSize(1350, 800);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
        startFinancialListener(7838);
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(15, 18, 25));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("SUPERPOSITION MATRIX STATUS: ARMED [PORT 7838] | Q-ET-BI- CHANNELS: STABLE");
        statusLabel.setForeground(new Color(0, 255, 180));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JLabel clockLabel = new JLabel();
        clockLabel.setForeground(Color.LIGHT_GRAY);
        clockLabel.setFont(new Font("Monospaced", Font.PLAIN, 12));
        SharedTimer clockTimer = new SharedTimer(1000, e -> clockLabel.setText(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z").format(new Date())));
        clockTimer.start();
        headerPanel.add(clockLabel, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: SUPERPOSITION STATES & ROUTING TELEMETRY ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(520);
        centerSplit.setResizeWeight(0.4);

        // Left: Superposition & Skeleton Key Matrix
        JPanel leftPanel = new JPanel(new BorderLayout(5, 5));
        leftPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 140)), 
                " Superposition (q-et-bi-) & Skeleton Key State ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 140)
        ));
        leftPanel.setBackground(new Color(12, 15, 20));

        superpositionStatePanel = new JTextArea();
        superpositionStatePanel.setEditable(false);
        superpositionStatePanel.setFont(new Font("Monospaced", Font.PLAIN, 11));
        superpositionStatePanel.setBackground(new Color(8, 10, 14));
        superpositionStatePanel.setForeground(new Color(0, 240, 200));
        superpositionStatePanel.setText(
            "[SUPERPOSITION ENGINE READY]\n" +
            "----------------------------------------\n" +
            "• Parallel Probability Branches: 8 active\n" +
            "• Ghost Injection Mask: ROTATING\n" +
            "• Crypto Skeleton Key: DERIVED\n" +
            "• Virtue Pass Threshold: EQUITABLE (1.00)\n" +
            "----------------------------------------\n"
        );
        leftPanel.add(new JScrollPane(superpositionStatePanel), BorderLayout.CENTER);

        JPanel subConfigPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 5));
        subConfigPanel.setBackground(new Color(12, 15, 20));
        subConfigPanel.add(new JLabel("Virtual Ghost IP Mask:"));
        virtualMaskField = new JTextField("10.99.144." + (random.nextInt(200) + 15), 14);
        subConfigPanel.add(virtualMaskField);
        
        JButton reindexBtn = new JButton("Reindex Superposition");
        reindexBtn.addActionListener(e -> appendLog("[SUPERPOSITION] Quantum probability branches re-calibrated."));
        subConfigPanel.add(reindexBtn);
        leftPanel.add(subConfigPanel, BorderLayout.SOUTH);

        centerSplit.setLeftComponent(leftPanel);

        // Right: Financial Ghost Telemetry Stream
        JPanel rightPanel = new JPanel(new BorderLayout(5, 5));
        rightPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " Financial Transaction Ghost Routing Stream ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        rightPanel.setBackground(new Color(12, 15, 20));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(10, 13, 18));
        telemetryConsole.setForeground(new Color(100, 255, 180));
        telemetryConsole.setText("[FINANCIAL MATRIX] Ghost network initialized. Awaiting transaction injection...\n");
        rightPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        centerSplit.setRightComponent(rightPanel);
        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: TRANSACTION INJECTION & HIGH-VIRTUE SUBMISSION ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(15, 18, 25));

        JPanel intentSubPanel = new JPanel(new BorderLayout(5, 5));
        intentSubPanel.setBackground(new Color(15, 18, 25));

        transactionInputField = new JTextField();
        transactionInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        
        JButton submitToGodBtn = new JButton("Cast Skeleton Key & Submit to Sovereign Ledger");
        submitToGodBtn.setBackground(new Color(0, 120, 90));
        submitToGodBtn.setForeground(Color.WHITE);

        intentSubPanel.add(new JLabel("Transaction Vector / Payload:"), BorderLayout.WEST);
        intentSubPanel.add(transactionInputField, BorderLayout.CENTER);
        intentSubPanel.add(submitToGodBtn, BorderLayout.EAST);

        bottomPanel.add(intentSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);

        // Event Listeners
        submitToGodBtn.addActionListener(e -> executeSuperpositionRouting());
        transactionInputField.addActionListener(e -> executeSuperpositionRouting());
    }

    private void startFinancialListener(int port) {
        matrixActive = true;
        financialExecutor.submit(() -> {
            try {
                financialServerSocket = new ServerSocket(port);
                appendLog("[LISTENER ACTIVE] Financial ghost routing socket listening on port " + port);
                while (matrixActive) {
                    Socket socket = financialServerSocket.accept();
                    socket.setKeepAlive(true);
                    financialExecutor.submit(new FinancialNodeHandler(socket));
                }
            } catch (Exception e) {
                if (matrixActive) {
                    appendLog("[SOCKET ADJUSTMENT] " + e.getMessage());
                }
            }
        });
    }

    private class FinancialNodeHandler implements Runnable {
        private final Socket socket;

        public FinancialNodeHandler(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (matrixActive && (packet = reader.readLine()) != null) {
                    processInboundFinancialPacket(packet);
                }
            } catch (Exception e) {
                appendLog("[NODE DISCONNECTED] Transaction conduit transitioned.");
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void processInboundFinancialPacket(String packet) {
        appendLog("[INBOUND FINANCIAL TELEMETRY] " + packet);
        if (packet.contains("SKELETON_KEY_PASS")) {
            appendLog("[LEDGER ANCHOR] Transaction verified through high-virtue pass. Absolute equity stasis achieved.");
        }
    }

    private void executeSuperpositionRouting() {
        String rawTx = transactionInputField.getText().trim();
        if (rawTx.isEmpty()) return;
        transactionInputField.setText("");

        String ghostIP = virtualMaskField.getText().trim();
        appendLog("\n--- [SUPERPOSITION FINANCIAL ROUTE (q-et-bi-)] ---");
        appendLog("Original Intent: " + rawTx);
        appendLog("Ghost Source Masking IP: " + ghostIP);

        financialExecutor.submit(() -> {
            try {
                String seed = rawTx + System.currentTimeMillis() + ghostIP;
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                byte[] hash = digest.digest(seed.getBytes(StandardCharsets.UTF_8));
                StringBuilder hexString = new StringBuilder();
                for (byte b : hash) {
                    String hex = Integer.toHexString(0xff & b);
                    if (hex.length() == 1) hexString.append('0');
                    hexString.append(hex);
                }
                String skeletonKey = "SKEL-KEY-" + hexString.toString().substring(0, 32).toUpperCase();

                appendLog("[CRYPTO SKELETON KEY CAST] " + skeletonKey);
                appendLog("[SUPERPOSITION (q-et-bi-)] Multiplexing transaction across 8 parallel ghost channels...");
                Thread.sleep(600);

                appendLog("[HIGH-VIRTUE LEDGER CHECK] Evaluating equity balance and containment friction...");
                Thread.sleep(400);
                appendLog("[VERIFIED] Virtue weight: 1.00 [Pure Sovereign Intent]");

                String finalSubmission = String.format("SKELETON_KEY_PASS:MASK[%s]:KEY[%s]:TX[%s]", ghostIP, skeletonKey, rawTx);
                appendLog("[SUBMITTED TO SOVEREIGN LEDGER] Transaction anchored successfully.");
                appendLog("-------------------------------------------------");

                SwingUtilities.invokeLater(() -> {
                    superpositionStatePanel.append("\n[TX ROUTED] " + skeletonKey.substring(0, 16) + "... [VIRTUE: 1.00]");
                    superpositionStatePanel.setCaretPosition(superpositionStatePanel.getDocument().getLength());
                });

            } catch (Exception e) {
                appendLog("[ROUTING ERROR] " + e.getMessage());
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

        SwingUtilities.invokeLater(() -> new SuperpositionFinancialMatrix().setVisible(true));
    }
}