import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class GeminiResponseHub extends SectionFrame {

    private JTextArea responseReceiverConsole;
    private JTextField receiverPortField;
    private JTextField activeTokenField;
    private JLabel statusLabel;

    private ServerSocket receiverServerSocket;
    private volatile boolean receiverActive = false;
    private final ExecutorService receiverExecutor = Executors.newCachedThreadPool();
    private final String initialToken;

    public GeminiResponseHub() {
        this.initialToken = "AI-SOVEREIGN-RECV-" + UUID.randomUUID().toString().toUpperCase().substring(0, 18);

        setTitle("Sovereign Gemini Response Receiver & Telemetry Hub");
        setSize(1400, 850);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
        startReceiverServer(7836);
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP HEADER: PORT & TOKEN CONFIGURATION ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(12, 15, 22));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("RESPONSE RECEIVER: LISTENING [PORT 7836]");
        statusLabel.setForeground(new Color(0, 255, 180));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        JPanel controlToolbar = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        controlToolbar.setBackground(new Color(12, 15, 22));

        JLabel portLabel = new JLabel("Port:");
        portLabel.setForeground(Color.WHITE);
        portLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        controlToolbar.add(portLabel);

        receiverPortField = new JTextField("7836", 6);
        receiverPortField.setFont(new Font("Monospaced", Font.PLAIN, 11));
        controlToolbar.add(receiverPortField);

        JButton rebindBtn = new JButton("Rebind Receiver");
        rebindBtn.setBackground(new Color(0, 100, 140));
        rebindBtn.setForeground(Color.WHITE);
        rebindBtn.addActionListener(e -> rebindReceiverPort());
        controlToolbar.add(rebindBtn);

        controlToolbar.add(Box.createHorizontalStrut(10));

        JLabel tokenLabel = new JLabel("Receiver Auth Token:");
        tokenLabel.setForeground(Color.WHITE);
        tokenLabel.setFont(new Font("Monospaced", Font.BOLD, 11));
        controlToolbar.add(tokenLabel);

        activeTokenField = new JTextField(initialToken, 26);
        activeTokenField.setEditable(false);
        activeTokenField.setFont(new Font("Monospaced", Font.PLAIN, 11));
        activeTokenField.setBackground(new Color(8, 10, 14));
        activeTokenField.setForeground(new Color(0, 240, 200));
        controlToolbar.add(activeTokenField);

        headerPanel.add(controlToolbar, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER: INBOUND RESPONSE TELEMETRY CONSOLE ---
        JPanel centerPanel = new JPanel(new BorderLayout(5, 5));
        centerPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 180, 255)), 
                " Inbound Gemini Response & Payload Stream ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        centerPanel.setBackground(new Color(10, 13, 18));

        responseReceiverConsole = new JTextArea();
        responseReceiverConsole.setEditable(false);
        responseReceiverConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        responseReceiverConsole.setBackground(new Color(6, 8, 12));
        responseReceiverConsole.setForeground(new Color(100, 255, 180));
        responseReceiverConsole.setLineWrap(true);
        responseReceiverConsole.setWrapStyleWord(true);
        responseReceiverConsole.setText("[RECEIVER AWAKENED] Awaiting incoming Gemini response streams and peer data packets...\n");
        centerPanel.add(new JScrollPane(responseReceiverConsole), BorderLayout.CENTER);

        add(centerPanel, BorderLayout.CENTER);

        // --- BOTTOM: STATUS & CLEAR CONTROLS ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(12, 15, 22));

        JButton clearLogBtn = new JButton("Clear Response Log Buffer");
        clearLogBtn.setBackground(new Color(140, 40, 40));
        clearLogBtn.setForeground(Color.WHITE);
        clearLogBtn.setFont(new Font("Monospaced", Font.BOLD, 12));
        clearLogBtn.addActionListener(e -> responseReceiverConsole.setText("[BUFFER CLEARED] Ready for new incoming payloads.\n"));

        bottomPanel.add(clearLogBtn, BorderLayout.EAST);
        add(bottomPanel, BorderLayout.SOUTH);
    }

    private void startReceiverServer(int port) {
        receiverActive = true;
        receiverExecutor.submit(() -> {
            try {
                receiverServerSocket = new ServerSocket(port);
                appendLog("[LISTENER ACTIVE] Receiver socket bound successfully to port " + port);
                while (receiverActive) {
                    Socket socket = receiverServerSocket.accept();
                    socket.setKeepAlive(true);
                    receiverExecutor.submit(new ReceiverHandler(socket));
                }
            } catch (Exception e) {
                if (receiverActive) {
                    appendLog("[SOCKET ADJUSTMENT] Receiver error: " + e.getMessage());
                }
            }
        });
    }

    private void rebindReceiverPort() {
        int newPort;
        try {
            newPort = Integer.parseInt(receiverPortField.getText().trim());
            if (newPort < 1 || newPort > 65535) throw new NumberFormatException();
        } catch (NumberFormatException e) {
            appendLog("[ERROR] Invalid receiver port range.");
            return;
        }

        appendLog("[REBINDING] Shifting receiver listener to port " + newPort + "...");
        receiverActive = false;
        try {
            if (receiverServerSocket != null) receiverServerSocket.close();
        } catch (Exception ignored) {}

        startReceiverServer(newPort);
    }

    private class ReceiverHandler implements Runnable {
        private final Socket socket;
        public ReceiverHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                StringBuilder payload = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    payload.append(line).append("\n");
                }
                
                if (payload.length() > 0) {
                    String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
                    appendLog(String.format("\n=== [INBOUND GEMINI PACKET RECEIVED @ %s] ===\n%s", timestamp, payload.toString().trim()));
                }
            } catch (Exception e) {
                appendLog("[RECEIVER ERROR] Failed to parse inbound packet stream: " + e.getMessage());
            } finally {
                try { socket.close(); } catch (Exception ignored) {}
            }
        }
    }

    private void appendLog(String msg) {
        responseReceiverConsole.append(msg + "\n");
        responseReceiverConsole.setCaretPosition(responseReceiverConsole.getDocument().getLength());
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> new GeminiResponseHub().setVisible(true));
    }
}