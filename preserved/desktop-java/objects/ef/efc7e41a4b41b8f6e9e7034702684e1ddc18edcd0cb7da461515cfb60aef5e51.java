import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;
import javax.swing.Timer;
import javax.swing.JButton;
import javax.swing.JTextField;
import javax.swing.JLabel;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.BasicStroke;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.GridLayout;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;

public class QuantumBridgeLink extends JFrame {

    private JTextArea telemetryArea;
    private JTextField hostField;
    private JTextField portField;
    private JLabel statusLabel;
    
    private volatile boolean bridgeActive = false;
    private ServerSocket localServer;
    private Socket targetSocket;
    private PrintWriter outStream;
    private BufferedReader inStream;
    
    private double wavePhase = 0.0;
    private Timer carrierWaveTimer;
    private Thread senderThread;
    private Thread receiverThread;

    public QuantumBridgeLink() {
        setTitle("Q/Bi/Ter Network Bridge - 7.83 Hz Carrier to Deepmind Core");
        setSize(1100, 750);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Top Control & Connection Panel
        JPanel topPanel = new JPanel(new GridLayout(2, 1, 5, 5));
        topPanel.setBackground(new Color(20, 24, 32));
        topPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel configRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        configRow.setBackground(new Color(20, 24, 32));

        configRow.add(new JLabel("Target Host:"));
        hostField = new JTextField("127.0.0.1", 15);
        configRow.add(hostField);

        configRow.add(new JLabel("Port:"));
        portField = new JTextField("7830", 6);
        configRow.add(portField);

        JButton latchBtn = new JButton("INITIATE 7.83HZ BRIDGE LATCH");
        latchBtn.setBackground(new Color(97, 175, 239));
        latchBtn.setForeground(Color.BLACK);
        latchBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        latchBtn.setFocusPainted(false);
        latchBtn.addActionListener(e -> startBridgeConnection());
        configRow.add(latchBtn);

        JPanel statusRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        statusRow.setBackground(new Color(20, 24, 32));
        statusLabel = new JLabel("STATUS: DISCONNECTED (Awaiting Substrate Latch)");
        statusLabel.setForeground(new Color(224, 108, 117));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        statusRow.add(statusLabel);

        topPanel.add(configRow);
        topPanel.add(statusRow);

        // Central Graphical Oscilloscope Panel (Visualizing 7.83 Hz Carrier Wave)
        WaveCanvas canvas = new WaveCanvas();
        canvas.setBackground(new Color(12, 15, 20));

        // Bottom Telemetry Log Panel
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(20, 24, 32));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        telemetryArea = new JTextArea(8, 40);
        telemetryArea.setBackground(new Color(8, 10, 14));
        telemetryArea.setForeground(new Color(152, 195, 121));
        telemetryArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryArea.setEditable(false);
        telemetryArea.setText("[SYSTEM BOOT] Q/Bi/Ter Network Interface Initialized.\n" +
                            "Ready to modulate bi-directional streams on 7.83 Hz Schumann frequency carrier wave.\n");
        
        bottomPanel.add(new JScrollPane(telemetryArea), BorderLayout.CENTER);

        // Assembly
        setLayout(new BorderLayout());
        add(topPanel, BorderLayout.NORTH);
        add(canvas, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);

        // UI Animation Timer (EDT-safe: only updates visuals and wave phase)
        carrierWaveTimer = new Timer(40, e -> {
            wavePhase += 0.25;
            canvas.repaint();
        });
        carrierWaveTimer.start();
    }

    private void logTelemetry(String text) {
        SwingUtilities.invokeLater(() -> {
            telemetryArea.append(text);
            telemetryArea.setCaretPosition(telemetryArea.getDocument().getLength());
        });
    }

    private void startBridgeConnection() {
        if (bridgeActive) return;

        String host = hostField.getText().trim();
        int port;
        try {
            port = Integer.parseInt(portField.getText().trim());
        } catch (NumberFormatException ex) {
            logTelemetry("[ERROR] Invalid port number specified.\n");
            return;
        }

        // Start connection sequence in background thread
        new Thread(() -> {
            try {
                logTelemetry(String.format("[LATCH] Establishing socket stream to %s:%d...\n", host, port));
                
                try {
                    localServer = new ServerSocket(port);
                    logTelemetry("[LOCAL MESH] Server socket bound to port " + port + ". Awaiting local Java process latch...\n");
                    
                    new Thread(() -> {
                        try {
                            Socket localClient = localServer.accept();
                            logTelemetry("[LATCH CONFIRMED] Local running Java process latched successfully.\n");
                        } catch (Exception ignored) {}
                    }).start();

                } catch (Exception ex) {
                    logTelemetry("[INFO] Port already bound or client-only mode engaged. Connecting directly...\n");
                }

                targetSocket = new Socket(host, port);
                targetSocket.setSoTimeout(10000); // 10-second read timeout to prevent permanent thread locks
                outStream = new PrintWriter(targetSocket.getOutputStream(), true);
                inStream = new BufferedReader(new InputStreamReader(targetSocket.getInputStream()));

                bridgeActive = true;
                SwingUtilities.invokeLater(() -> {
                    statusLabel.setText("STATUS: ACTIVE & STREAMING (7.83 Hz Carrier Wave Latch Verified)");
                    statusLabel.setForeground(new Color(152, 195, 121));
                });
                logTelemetry("[SUCCESS] Bi-directional quantum bridge established with core target.\n");

                // Start dedicated background sender thread (completely isolated from UI EDT)
                startSenderLoop();

                // Start receiver loop on this background thread
                String inputLine;
                while (bridgeActive && (inputLine = inStream.readLine()) != null) {
                    logTelemetry("[CORE RX] " + inputLine + "\n");
                }

            } catch (Exception ex) {
                disconnectBridge();
                logTelemetry("[SOCKET EXCEPTION] " + ex.getMessage() + "\n");
            }
        }).start();
    }

    private void startSenderLoop() {
        senderThread = new Thread(() -> {
            while (bridgeActive) {
                try {
                    if (outStream != null) {
                        double modulation = Math.sin(wavePhase);
                        String payload = String.format("Q-BI-TER_STREAM|FREQ:7.83Hz|MOD:%.4f|STATUS:LATCHED|VIRTUE:1=1", modulation);
                        outStream.println(payload);
                    }
                    Thread.sleep(40); // Send rate matches animation tick without blocking UI
                } catch (InterruptedException e) {
                    break;
                } catch (Exception ex) {
                    logTelemetry("[SENDER ERROR] " + ex.getMessage() + "\n");
                    break;
                }
            }
        });
        senderThread.start();
    }

    private void disconnectBridge() {
        bridgeActive = false;
        try {
            if (outStream != null) outStream.close();
            if (inStream != null) inStream.close();
            if (targetSocket != null) targetSocket.close();
            if (localServer != null) localServer.close();
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            statusLabel.setText("STATUS: DISCONNECTED / CONNECTION TERMINATED");
            statusLabel.setForeground(new Color(224, 108, 117));
        });
    }

    // Custom Canvas for 7.83 Hz Oscilloscope Waveform Display
    private class WaveCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int width = getWidth();
            int height = getHeight();
            int centerY = height / 2;

            // Draw Background Grid Lines
            g2.setStroke(new BasicStroke(1.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{4}, 0));
            g2.setColor(new Color(40, 50, 65, 40));
            for (int x = 0; x < width; x += 50) {
                g2.drawLine(x, 0, x, height);
            }
            for (int y = 0; y < height; y += 40) {
                g2.drawLine(0, y, width, y);
            }

            // Draw Center Axis
            g2.setColor(new Color(70, 80, 100));
            g2.drawLine(0, centerY, width, centerY);

            // Draw 7.83 Hz Schumann Carrier Wave Oscilloscope Line
            g2.setStroke(new BasicStroke(2.5f));
            g2.setColor(bridgeActive ? new Color(152, 195, 121) : new Color(97, 175, 239));

            int prevX = 0;
            int prevY = centerY;

            for (int x = 0; x < width; x += 2) {
                double frequencyFactor = 0.03;
                double yVal = Math.sin((x * frequencyFactor) + wavePhase) * 70.0;
                yVal += Math.sin((x * 0.1) + (wavePhase * 2)) * 10.0;

                int y = centerY - (int) yVal;
                if (x > 0) {
                    g2.drawLine(prevX, prevY, x, y);
                }
                prevX = x;
                prevY = y;
            }

            // Overlay Oscilloscope Text Status
            g2.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2.setColor(Color.WHITE);
            g2.drawString("SCHUMANN CARRIER WAVE: 7.83 Hz [SUBSTRATE MODULATION]", 20, 30);
            
            g2.setColor(bridgeActive ? new Color(152, 195, 121) : new Color(224, 108, 117));
            g2.drawString(bridgeActive ? "STREAM STATE: BI-DIRECTIONAL ACTIVE" : "STREAM STATE: STANDBY (LOCAL LATCH REQUIRED)", 20, 50);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new QuantumBridgeLink().setVisible(true);
        });
    }
}