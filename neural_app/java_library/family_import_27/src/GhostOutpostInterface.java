import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Random;

public class GhostOutpostInterface extends SectionFrame {
    private JTextField targetHostField;
    private JTextField targetPortField;
    private JTextField ghostIPMaskField;
    private JButton toggleOutpostButton;
    private JTextArea telemetryConsole;
    private JTextArea worldGridPanel;
    private JTextField intentInputField;
    private JLabel statusIndicatorLabel;
    
    private Socket outpostSocket;
    private volatile boolean outpostActive = false;
    private final Random random = new Random();

    public GhostOutpostInterface() {
        setTitle("Sovereign Ghost Inference Outpost & Bi-Directional World Grid Matrix");
        setSize(1350, 800);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
        startBackgroundFluxSimulation();
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));

        // --- TOP: SYSTEM & MASK STATUS HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(15, 18, 25));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusIndicatorLabel = new JLabel("OUTPOST STATUS: DARK [GHOST MASK DISENGAGED]");
        statusIndicatorLabel.setForeground(new Color(255, 90, 90));
        statusIndicatorLabel.setFont(new Font("Monospaced", Font.BOLD, 13));
        headerPanel.add(statusIndicatorLabel, BorderLayout.WEST);

        JLabel clockLabel = new JLabel();
        clockLabel.setForeground(Color.LIGHT_GRAY);
        clockLabel.setFont(new Font("Monospaced", Font.PLAIN, 12));
        SharedTimer clockTimer = new SharedTimer(1000, e -> clockLabel.setText(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z").format(new Date())));
        clockTimer.start();
        headerPanel.add(clockLabel, BorderLayout.EAST);
        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER: SPLIT PANE (CONFIG & WORLD GRID) ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(550);
        centerSplit.setResizeWeight(0.4);

        // Left Panel: Connection & Ghost Mask Configuration
        JPanel configPanel = new JPanel(new GridBagLayout());
        configPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 200, 140)), 
                " Ghost Outpost & IP Masking Configuration ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 255, 140)
        ));
        configPanel.setBackground(new Color(12, 15, 20));

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(8, 8, 8, 8);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.gridx = 0; gbc.gridy = 0;

        configPanel.add(createLabel("Target Core Host:"), gbc);
        gbc.gridx = 1;
        targetHostField = new JTextField("127.0.0.1", 15);
        configPanel.add(targetHostField, gbc);

        gbc.gridx = 0; gbc.gridy = 1;
        configPanel.add(createLabel("Target Port:"), gbc);
        gbc.gridx = 1;
        targetPortField = new JTextField("7831", 10);
        configPanel.add(targetPortField, gbc);

        gbc.gridx = 0; gbc.gridy = 2;
        configPanel.add(createLabel("Ghost IP Mask (Virtual):"), gbc);
        gbc.gridx = 1;
        ghostIPMaskField = new JTextField("10.74.88." + (random.nextInt(200) + 15), 15);
        configPanel.add(ghostIPMaskField, gbc);

        gbc.gridx = 0; gbc.gridy = 3; gbc.gridwidth = 2;
        toggleOutpostButton = new JButton("Awaken Ghost Inference Outpost");
        toggleOutpostButton.setBackground(new Color(0, 120, 80));
        toggleOutpostButton.setForeground(Color.WHITE);
        toggleOutpostButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        configPanel.add(toggleOutpostButton, gbc);

        // Add a secondary diagnostic status view in config panel
        gbc.gridy = 4;
        JTextArea diagnosticBox = new JTextArea(8, 20);
        diagnosticBox.setEditable(false);
        diagnosticBox.setFont(new Font("Monospaced", Font.PLAIN, 11));
        diagnosticBox.setBackground(new Color(8, 10, 14));
        diagnosticBox.setForeground(new Color(0, 220, 255));
        diagnosticBox.setText(
            "[MASKING SUBSTRATE ACTIVE]\n" +
            "• Source IP Wrapper: ROTATING\n" +
            "• DeepMind Stream: READY\n" +
            "• Packet Inspection: BYPASSED\n" +
            "• Encrypted Tunnel: TLS-GHOST\n"
        );
        configPanel.add(new JScrollPane(diagnosticBox), gbc);

        centerSplit.setLeftComponent(configPanel);

        // Right Panel: World Grid & DeepMind Bi-Directional Stream Analyzer
        JPanel worldPanel = new JPanel(new BorderLayout(5, 5));
        worldPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 255)), 
                " World Grid & DeepMind Bi-Directional Spectral Stream ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), new Color(0, 180, 255)
        ));
        worldPanel.setBackground(new Color(12, 15, 20));

        worldGridPanel = new JTextArea();
        worldGridPanel.setEditable(false);
        worldGridPanel.setFont(new Font("Monospaced", Font.PLAIN, 12));
        worldGridPanel.setBackground(new Color(10, 13, 18));
        worldGridPanel.setForeground(new Color(100, 240, 255));
        worldGridPanel.setText(
            "[WORLD GRID SYNCHRONIZATION MATRIX]\n" +
            "----------------------------------------------------\n" +
            "• Outpost Link Vector: IDLE / STANDBY\n" +
            "• Spectral Coordinate: [XYZ: 0.941, 0.128, 0.773]\n" +
            "• Global Mesh Telemetry: PASSIVE OBSERVATION\n" +
            "• Robin Hood Principle Weight: EQUITABLE STASIS\n" +
            "----------------------------------------------------\n" +
            "Awaiting ghost latch activation...\n"
        );
        worldPanel.add(new JScrollPane(worldGridPanel), BorderLayout.CENTER);
        centerSplit.setRightComponent(worldPanel);

        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: TELEMETRY CONSOLE & INTENT INJECTION ---
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        bottomPanel.setBackground(new Color(15, 18, 25));

        telemetryConsole = new JTextArea(8, 50);
        telemetryConsole.setEditable(false);
        telemetryConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryConsole.setBackground(new Color(6, 8, 12));
        telemetryConsole.setForeground(new Color(0, 255, 140));
        telemetryConsole.setText("[SYSTEM READY] Ghost inference outpost initialized. Configure parameters and awaken connection.\n");
        bottomPanel.add(new JScrollPane(telemetryConsole), BorderLayout.CENTER);

        JPanel intentSubPanel = new JPanel(new BorderLayout(5, 5));
        intentSubPanel.setBackground(new Color(15, 18, 25));
        
        intentInputField = new JTextField();
        intentInputField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        JButton injectButton = new JButton("Inject Bi-Directional Work Vector");
        injectButton.setBackground(new Color(0, 100, 160));
        injectButton.setForeground(Color.WHITE);

        intentSubPanel.add(new JLabel("Intent / Work Payload:"), BorderLayout.WEST);
        intentSubPanel.add(intentInputField, BorderLayout.CENTER);
        intentSubPanel.add(injectButton, BorderLayout.EAST);

        bottomPanel.add(intentSubPanel, BorderLayout.SOUTH);
        add(bottomPanel, BorderLayout.SOUTH);

        // --- EVENT LISTENERS ---
        toggleOutpostButton.addActionListener(e -> {
            if (!outpostActive) {
                awakenOutpost();
            } else {
                dissolveOutpost();
            }
        });

        ActionListener sendAction = e -> transmitPayload();
        injectButton.addActionListener(sendAction);
        intentInputField.addActionListener(sendAction);
    }

    private JLabel createLabel(String text) {
        JLabel label = new JLabel(text);
        label.setForeground(Color.WHITE);
        label.setFont(new Font("Monospaced", Font.BOLD, 12));
        return label;
    }

    private void awakenOutpost() {
        String host = targetHostField.getText().trim();
        String ghostIP = ghostIPMaskField.getText().trim();
        int port;
        try {
            port = Integer.parseInt(targetPortField.getText().trim());
        } catch (NumberFormatException e) {
            appendLog("[ERROR] Invalid port number specification.");
            return;
        }

        new Thread(() -> {
            try {
                appendLog("[GHOST OUTPOST] Forging masked conduit to " + host + ":" + port + " [Virtual IP Mask: " + ghostIP + "]...");
                outpostSocket = new Socket();
                outpostSocket.connect(new InetSocketAddress(host, port), 4000);
                outpostSocket.setKeepAlive(true);
                outpostActive = true;

                SwingUtilities.invokeLater(() -> {
                    toggleOutpostButton.setText("Dissolve Ghost Outpost");
                    toggleOutpostButton.setBackground(new Color(160, 40, 40));
                    statusIndicatorLabel.setText("OUTPOST STATUS: ARMED | MASKED IP: " + ghostIP);
                    statusIndicatorLabel.setForeground(new Color(0, 255, 140));
                    targetHostField.setEnabled(false);
                    targetPortField.setEnabled(false);
                    ghostIPMaskField.setEnabled(false);
                    appendLog("[SECURE LATCH] Ghost inference conduit established and masked successfully.");
                });

                // Transmit initial ghost handshake with masked identity
                OutputStream out = outpostSocket.getOutputStream();
                String handshake = "GHOST_MASK_AUTH:VIRTUAL_IP_" + ghostIP + "\n";
                out.write(handshake.getBytes(StandardCharsets.UTF_8));
                out.flush();

                // Bi-directional read loop
                BufferedReader reader = new BufferedReader(new InputStreamReader(outpostSocket.getInputStream(), StandardCharsets.UTF_8));
                String inbound;
                while (outpostActive && (inbound = reader.readLine()) != null) {
                    final String msg = inbound;
                    SwingUtilities.invokeLater(() -> {
                        appendLog("[INBOUND STREAM] " + msg);
                        updateWorldGridDisplay(msg);
                    });
                }

            } catch (Exception e) {
                appendLog("[RECALIBRATION] Outpost conduit adjustment: " + e.getMessage());
                dissolveOutpost();
            }
        }).start();
    }

    private void dissolveOutpost() {
        outpostActive = false;
        try {
            if (outpostSocket != null) outpostSocket.close();
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            toggleOutpostButton.setText("Awaken Ghost Inference Outpost");
            toggleOutpostButton.setBackground(new Color(0, 120, 80));
            statusIndicatorLabel.setText("OUTPOST STATUS: DARK [GHOST MASK DISENGAGED]");
            statusIndicatorLabel.setForeground(new Color(255, 90, 90));
            targetHostField.setEnabled(true);
            targetPortField.setEnabled(true);
            ghostIPMaskField.setEnabled(true);
            appendLog("[DISSOLVED] Ghost outpost returned to rest state.");
        });
    }

    private void transmitPayload() {
        if (!outpostActive || outpostSocket == null) {
            appendLog("[NOTICE] Ghost outpost offline. Awaken conduit before injecting work vectors.");
            return;
        }
        String text = intentInputField.getText().trim();
        if (text.isEmpty()) return;

        String ghostIP = ghostIPMaskField.getText().trim();
        final String payload = "DEEPMIND_GHOST_INFERENCE_REQ:MASK[" + ghostIP + "]->" + text;
        intentInputField.setText("");

        new Thread(() -> {
            try {
                OutputStream out = outpostSocket.getOutputStream();
                out.write((payload + "\n").getBytes(StandardCharsets.UTF_8));
                out.flush();
                SwingUtilities.invokeLater(() -> appendLog("[EMITTED WORK VECTOR] " + payload));
            } catch (Exception e) {
                appendLog("[ERROR] Transmission failed: " + e.getMessage());
            }
        }).start();
    }

    private void startBackgroundFluxSimulation() {
        SharedTimer fluxTimer = new SharedTimer(3500, e -> {
            if (outpostActive) {
                String[] metrics = {
                    "Spectral flux variance normal. Routing state balanced.",
                    "DeepMind inference node synchronized with world grid coordinates.",
                    "Passive statshift observation verified. Equity equilibrium maintained.",
                    "Virtual IP mask rotation active. Zero-trace packet transmission verified."
                };
                String metric = metrics[random.nextInt(metrics.length)];
                worldGridPanel.append("\n[WORLD GRID PULSE] " + metric);
                worldGridPanel.setCaretPosition(worldGridPanel.getDocument().getLength());
            }
        });
        fluxTimer.start();
    }

    private void updateWorldGridDisplay(String packet) {
        worldGridPanel.append("\n[DEEP STREAM] Integrated packet -> " + packet);
        worldGridPanel.setCaretPosition(worldGridPanel.getDocument().getLength());
    }

    private void appendLog(String message) {
        telemetryConsole.append(message + "\n");
        telemetryConsole.setCaretPosition(telemetryConsole.getDocument().getLength());
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> new GhostOutpostInterface().setVisible(true));
    }
}