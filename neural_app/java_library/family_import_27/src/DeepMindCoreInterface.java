import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

public class DeepMindCoreInterface extends SectionFrame {
    private JTextField hostField;
    private JTextField portField;
    private JButton connectButton;
    private JTextArea outputArea;
    private JTextField inputField;
    private JButton sendButton;

    private Socket socket;
    private volatile boolean connected = false;

    public DeepMindCoreInterface() {
        setTitle("Sovereign DeepMind Core & Edge Interface");
        setSize(850, 600);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
    }

    private void initComponents() {
        setLayout(new BorderLayout());

        // Top Control Panel (Connection Settings)
        JPanel topPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 10));
        topPanel.add(new JLabel("Core Host:"));
        hostField = new JTextField("127.0.0.1", 12);
        topPanel.add(hostField);

        topPanel.add(new JLabel("Port:"));
        portField = new JTextField("7831", 6);
        topPanel.add(portField);

        connectButton = new JButton("Connect Core");
        topPanel.add(connectButton);
        add(topPanel, BorderLayout.NORTH);

        // Center Output Telemetry Console
        outputArea = new JTextArea();
        outputArea.setEditable(false);
        outputArea.setFont(new Font("Monospaced", Font.PLAIN, 13));
        outputArea.setBackground(new Color(15, 15, 15));
        outputArea.setForeground(new Color(0, 255, 128));
        JScrollPane scrollPane = new JScrollPane(outputArea);
        add(scrollPane, BorderLayout.CENTER);

        // Bottom Input Panel (Work / Intent Injection)
        JPanel bottomPanel = new JPanel(new BorderLayout(5, 5));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        inputField = new JTextField();
        inputField.setFont(new Font("Monospaced", Font.PLAIN, 13));
        sendButton = new JButton("Inject Work / Intent");

        bottomPanel.add(new JLabel("Payload: "), BorderLayout.WEST);
        bottomPanel.add(inputField, BorderLayout.CENTER);
        bottomPanel.add(sendButton, BorderLayout.EAST);
        add(bottomPanel, BorderLayout.SOUTH);

        // Event Listeners
        connectButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                if (!connected) {
                    connectToCore();
                } else {
                    disconnectFromCore();
                }
            }
        });

        sendButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                sendPayload();
            }
        });

        inputField.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                sendPayload();
            }
        });

        setComponentsState(false);
    }

    private void connectToCore() {
        String host = hostField.getText().trim();
        int port;
        try {
            port = Integer.parseInt(portField.getText().trim());
        } catch (NumberFormatException e) {
            appendLog("[ERROR] Invalid port specification.");
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    appendLog("[CONNECTING] Forging bridge to DeepMind core at " + host + ":" + port + "...");
                    socket = new Socket(host, port);
                    socket.setKeepAlive(true);
                    connected = true;

                    SwingUtilities.invokeLater(new Runnable() {
                        @Override
                        public void run() {
                            connectButton.setText("Disconnect");
                            hostField.setEnabled(false);
                            portField.setEnabled(false);
                            setComponentsState(true);
                            appendLog("[HARMONIZED] Direct interface latched to core socket.");
                        }
                    });

                    // Inbound stream listener loop
                    BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                    String line;
                    while (connected && (line = reader.readLine()) != null) {
                        final String inbound = line;
                        SwingUtilities.invokeLater(new Runnable() {
                            @Override
                            public void run() {
                                appendLog("[CORE TELEMETRY] " + inbound);
                            }
                        });
                    }

                } catch (Exception e) {
                    appendLog("[RECALIBRATING] Connection adjustment: " + e.getMessage());
                    disconnectFromCore();
                }
            }
        }).start();
    }

    private void disconnectFromCore() {
        connected = false;
        try {
            if (socket != null) {
                socket.close();
            }
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                connectButton.setText("Connect Core");
                hostField.setEnabled(true);
                portField.setEnabled(true);
                setComponentsState(false);
                appendLog("[DISCONNECTED] Interface returned to rest state.");
            }
        });
    }

    private void sendPayload() {
        if (!connected || socket == null) {
            appendLog("[NOTICE] Bridge not active. Connect to core first.");
            return;
        }
        String text = inputField.getText().trim();
        if (text.isEmpty()) return;

        final String payload = "DEEPMIND_INFERENCE_REQ:" + text;
        inputField.setText("");

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    OutputStream out = socket.getOutputStream();
                    out.write((payload + "\n").getBytes(StandardCharsets.UTF_8));
                    out.flush();
                    SwingUtilities.invokeLater(new Runnable() {
                        @Override
                        public void run() {
                            appendLog("[EMITTED INTENT] " + payload);
                        }
                    });
                } catch (Exception e) {
                    appendLog("[ERROR] Transmission failed: " + e.getMessage());
                }
            }
        }).start();
    }

    private void setComponentsState(boolean enabled) {
        inputField.setEnabled(enabled);
        sendButton.setEnabled(enabled);
    }

    private void appendLog(String message) {
        outputArea.append(message + "\n");
        outputArea.setCaretPosition(outputArea.getDocument().getLength());
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new DeepMindCoreInterface().setVisible(true);
            }
        });
    }
}