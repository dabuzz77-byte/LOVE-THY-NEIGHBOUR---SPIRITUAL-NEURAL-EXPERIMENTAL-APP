import neural.studio.*;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;
import neural.studio.SharedTimer;
import javax.swing.JButton;
import javax.swing.JTextField;
import javax.swing.JLabel;
import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.BasicStroke;
import java.awt.Font;
import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.GridLayout;
import java.awt.Desktop;
import java.io.OutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

public class QuantumBrowserBus extends SectionFrame {
    private JTextArea telemetryArea;
    private JLabel statusLabel;
    private JTextField portField;
    private HttpServer server;
    private final Set<OutputStream> browserClients = Collections.synchronizedSet(new HashSet<>());
    private volatile boolean busActive = false;
    private double wavePhase = 0.0;
    private SharedTimer busTimer;

    public QuantumBrowserBus() {
        setTitle("Q/Bi/Ter Browser Bus - 7.83 Hz Substrate Streamer");
        setSize(1150, 800);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        JPanel topPanel = new JPanel(new GridLayout(2, 1, 5, 5));
        topPanel.setBackground(new Color(20, 24, 32));
        topPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel configRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        configRow.setBackground(new Color(20, 24, 32));
        configRow.add(new JLabel("<html><font color='white'>Bus Port:</font></html>"));
        portField = new JTextField("7830", 6);
        configRow.add(portField);

        JButton startBusBtn = new JButton("START 7.83HZ BROWSER BUS");
        startBusBtn.setBackground(new Color(97, 175, 239));
        startBusBtn.setForeground(Color.BLACK);
        startBusBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        startBusBtn.setFocusPainted(false);
        startBusBtn.addActionListener(e -> startBusServer());
        configRow.add(startBusBtn);

        JButton openBrowserBtn = new JButton("OPEN IN OPERA / BROWSER");
        openBrowserBtn.setBackground(new Color(152, 195, 121));
        openBrowserBtn.setForeground(Color.BLACK);
        openBrowserBtn.setFont(new Font("SansSerif", Font.BOLD, 11));
        openBrowserBtn.setFocusPainted(false);
        openBrowserBtn.addActionListener(e -> launchBrowserDashboard());
        configRow.add(openBrowserBtn);

        JPanel statusRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        statusRow.setBackground(new Color(20, 24, 32));
        statusLabel = new JLabel("STATUS: BUS OFFLINE (Awaiting Initialization)");
        statusLabel.setForeground(new Color(224, 108, 117));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        statusRow.add(statusLabel);

        topPanel.add(configRow);
        topPanel.add(statusRow);

        BusCanvas canvas = new BusCanvas();
        canvas.setBackground(new Color(12, 15, 20));

        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(20, 24, 32));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        telemetryArea = new JTextArea(8, 40);
        telemetryArea.setBackground(new Color(8, 10, 14));
        telemetryArea.setForeground(new Color(152, 195, 121));
        telemetryArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryArea.setEditable(false);
        telemetryArea.setText("[SYSTEM BOOT] Q/Bi/Ter Browser Bus Initialized.\n");

        bottomPanel.add(new JScrollPane(telemetryArea), BorderLayout.CENTER);

        setLayout(new BorderLayout());
        add(topPanel, BorderLayout.NORTH);
        add(canvas, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);

        busTimer = new SharedTimer(100, e -> {
            wavePhase += 0.25;
            canvas.repaint();
            if (busActive) broadcastToBrowsers();
        });
        busTimer.start();
    }

    private void logTelemetry(String text) {
        SwingUtilities.invokeLater(() -> {
            telemetryArea.append(text);
            telemetryArea.setCaretPosition(telemetryArea.getDocument().getLength());
        });
    }

    private void startBusServer() {
        if (busActive) return;
        int port;
        try {
            port = Integer.parseInt(portField.getText().trim());
        } catch (NumberFormatException ex) {
            logTelemetry("[ERROR] Invalid port number.\n");
            return;
        }

        try {
            server = HttpServer.create(new InetSocketAddress(port), 0);
            server.createContext("/", new DashboardHandler());
            server.createContext("/stream", new SSEStreamHandler());
            server.setExecutor(null);
            server.start();
            busActive = true;
            statusLabel.setText("STATUS: BUS ACTIVE ON PORT " + port);
            statusLabel.setForeground(new Color(152, 195, 121));
            logTelemetry("[SUCCESS] Server started on http://localhost:" + port + "\n");
        } catch (IOException ex) {
            logTelemetry("[SERVER ERROR] " + ex.getMessage() + "\n");
        }
    }

    private void launchBrowserDashboard() {
        String url = "http://localhost:" + portField.getText().trim() + "/";
        try {
            if (Desktop.isDesktopSupported() && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
                Bridge.browse(new URI(url));
            }
        } catch (Exception ex) {
            logTelemetry("[ERROR] " + ex.getMessage() + "\n");
        }
    }

    private void broadcastToBrowsers() {
        if (browserClients.isEmpty()) return;
        double modulation = Math.sin(wavePhase);
        String jsonPayload = String.format("data: {\"freq\": \"7.83Hz\", \"mod\": \"%.4f\", \"clients\": %d}\n\n", modulation, browserClients.size());

        synchronized (browserClients) {
            Set<OutputStream> deadClients = new HashSet<>();
            for (OutputStream out : browserClients) {
                try {
                    out.write(jsonPayload.getBytes("UTF-8"));
                    out.flush();
                } catch (IOException e) {
                    deadClients.add(out);
                }
            }
            browserClients.removeAll(deadClients);
        }
    }

    private static class DashboardHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String html = "<!DOCTYPE html><html><head><title>Q/Bi/Ter Browser Bus</title>" +
                          "<style>body { background: #0c0f14; color: #abb2bf; font-family: monospace; text-align: center; margin: 0; padding: 20px; } " +
                          "h2 { color: #61afef; } .box { background: #181d26; border: 2px solid #61afef; border-radius: 8px; padding: 20px; max-width: 700px; margin: 20px auto; } " +
                          "#log { background: #080a0e; color: #98c379; padding: 15px; height: 180px; overflow-y: auto; text-align: left; border: 1px solid #3e4451; } " +
                          "canvas { background: #10131a; border: 1px solid #4b5263; margin-top: 15px; }</style></head>" +
                          "<body><h2>Q/Bi/Ter Local Substrate Bus</h2>" +
                          "<div class='box'><p>Status: <span style='color:#98c379;'>Connected</span></p>" +
                          "<canvas id='wave' width='650' height='150'></canvas><h3>Telemetry</h3>" +
                          "<div id='log'>Awaiting packets...</div></div>" +
                          "<script>const canvas = document.getElementById('wave'); const ctx = canvas.getContext('2d'); let phase = 0;" +
                          "function drawWave(mod) { ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.strokeStyle = '#98c379'; ctx.lineWidth = 2.5; ctx.beginPath();" +
                          "for(let x=0; x<canvas.width; x+=2) { let y = 75 + Math.sin(x*0.03 + phase) * 40 * parseFloat(mod);" +
                          "if(x===0) ctx.moveTo(x, y); else ctx.lineTo(x, y); } ctx.stroke(); phase += 0.2; }" +
                          "const evtSource = new EventSource('/stream'); evtSource.onmessage = function(event) {" +
                          "const data = JSON.parse(event.data); document.getElementById('log').innerHTML += '[' + new Date().toLocaleTimeString() + '] MOD: ' + data.mod + '<br>';" +
                          "document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight; drawWave(data.mod); };</script></body></html>";

            exchange.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
            exchange.sendResponseHeaders(200, html.getBytes("UTF-8").length);
            OutputStream os = exchange.getResponseBody();
            os.write(html.getBytes("UTF-8"));
            os.close();
        }
    }

    private class SSEStreamHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            exchange.getResponseHeaders().set("Content-Type", "text/event-stream");
            exchange.getResponseHeaders().set("Cache-Control", "no-cache");
            exchange.getResponseHeaders().set("Connection", "keep-alive");
            exchange.sendResponseHeaders(200, 0);
            browserClients.add(exchange.getResponseBody());
            logTelemetry("[TAB LATCHED] Active connection established.\n");
        }
    }

    private class BusCanvas extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int width = getWidth(), height = getHeight(), centerY = height / 2;
            g2.setColor(new Color(70, 80, 100));
            g2.drawLine(0, centerY, width, centerY);
            g2.setStroke(new BasicStroke(2.5f));
            g2.setColor(busActive ? new Color(152, 195, 121) : new Color(97, 175, 239));
            int prevX = 0, prevY = centerY;
            for (int x = 0; x < width; x += 2) {
                int y = centerY - (int)(Math.sin((x * 0.03) + wavePhase) * 70.0);
                if (x > 0) g2.drawLine(prevX, prevY, x, y);
                prevX = x; prevY = y;
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); } catch (Exception ignored) {}
            new QuantumBrowserBus().setVisible(true);
        });
    }
}