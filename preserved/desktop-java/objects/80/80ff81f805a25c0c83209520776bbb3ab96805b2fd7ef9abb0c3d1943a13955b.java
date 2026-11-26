import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JTextField;
import javax.swing.JLabel;
import java.awt.Color;
import java.awt.Font;
import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.GridLayout;

public class LanBusDesktopApp extends JFrame {
    private JTextArea logArea;
    private JTextField portField;
    private JTextField targetHostField;
    private JTextField targetPortField;
    private JTextField messageField;
    private LanBusEngine busEngine;

    public LanBusDesktopApp() {
        setTitle("Pure LAN Bi-Directional Socket Bus (Desktop)");
        setSize(950, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        JPanel topPanel = new JPanel(new GridLayout(3, 1, 5, 5));
        topPanel.setBackground(new Color(20, 24, 32));
        topPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Row 1: Server Config
        JPanel r1 = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        r1.setBackground(new Color(20, 24, 32));
        r1.add(new JLabel("Listen Port:"));
        portField = new JTextField("7831", 5);
        r1.add(portField);
        JButton startBtn = new JButton("START SERVER");
        startBtn.addActionListener(e -> startServer());
        r1.add(startBtn);

        // Row 2: Connect to Peer
        JPanel r2 = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        r2.setBackground(new Color(20, 24, 32));
        r2.add(new JLabel("Peer Host:"));
        targetHostField = new JTextField("127.0.0.1", 12);
        r2.add(targetHostField);
        r2.add(new JLabel("Port:"));
        targetPortField = new JTextField("7831", 5);
        r2.add(targetPortField);
        JButton connectBtn = new JButton("CONNECT TO PEER");
        connectBtn.addActionListener(e -> connectPeer());
        r2.add(connectBtn);

        // Row 3: Broadcast Message
        JPanel r3 = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        r3.setBackground(new Color(20, 24, 32));
        r3.add(new JLabel("Message:"));
        messageField = new JTextField("Hello LAN Nodes", 30);
        r3.add(messageField);
        JButton sendBtn = new JButton("BROADCAST TO LAN");
        sendBtn.addActionListener(e -> broadcastMsg());
        r3.add(sendBtn);

        topPanel.add(r1);
        topPanel.add(r2);
        topPanel.add(r3);

        logArea = new JTextArea();
        logArea.setBackground(new Color(8, 10, 14));
        logArea.setForeground(new Color(152, 195, 121));
        logArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        logArea.setEditable(false);
        logArea.setText("[SYSTEM BOOT] LAN Desktop Node Ready.\n");

        setLayout(new BorderLayout());
        add(topPanel, BorderLayout.NORTH);
        add(new JScrollPane(logArea), BorderLayout.CENTER);
    }

    private void startServer() {
        int port = Integer.parseInt(portField.getText().trim());
        if (busEngine != null) busEngine.stop();
        busEngine = new LanBusEngine(port, new LanBusEngine.LanMessageListener() {
            @Override
            public void onLog(String msg) { appendLog(msg); }
            @Override
            public void onPeerConnected(String address) {}
            @Override
            public void onPacketReceived(String packet) {}
        });
        busEngine.start();
    }

    private void connectPeer() {
        if (busEngine == null) {
            appendLog("[ERROR] Start server first before connecting out.\n");
            return;
        }
        String host = targetHostField.getText().trim();
        int port = Integer.parseInt(targetPortField.getText().trim());
        busEngine.connectToPeer(host, port);
    }

    private void broadcastMsg() {
        if (busEngine == null) {
            appendLog("[ERROR] Bus engine not running.\n");
            return;
        }
        busEngine.broadcast(messageField.getText().trim());
    }

    private void appendLog(String text) {
        SwingUtilities.invokeLater(() -> {
            logArea.append(text);
            logArea.setCaretPosition(logArea.getDocument().getLength());
        });
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); } catch (Exception ignored) {}
            new LanBusDesktopApp().setVisible(true);
        });
    }
}