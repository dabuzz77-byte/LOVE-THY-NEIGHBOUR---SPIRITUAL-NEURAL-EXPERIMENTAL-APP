import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.geom.Path2D;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;
import java.util.concurrent.*;
import java.util.function.Consumer;

/** Dependency-free local signal lab. Requires JDK 17 or later. */
public final class QuantumBrowserBus extends JFrame {
    private static final long serialVersionUID = 1L;
    private static final Color BG = new Color(11, 17, 27), PANEL = new Color(18, 28, 42);
    private static final Color TEXT = new Color(228, 237, 246), MUTED = new Color(143, 164, 186);
    private static final Color TEAL = new Color(82, 226, 189), BORDER = new Color(39, 55, 74);
    private final JTextArea activity = new JTextArea(5, 60);
    private final JTextField port = new JTextField("7830", 6);
    private final JButton start = button("Start bus", true), stop = button("Stop", false);
    private final JButton browser = button("Open dashboard", false), pause = button("Pause signal", false);
    private final JLabel state = label("OFFLINE", TEAL, 12), endpoint = label("Start the bus to connect a browser", MUTED, 12);
    private final JLabel clients = label("0", TEXT, 26), value = label("0.0000", TEXT, 26);
    private final JLabel packets = label("0", TEXT, 26), uptime = label("00:00", TEXT, 26);
    private final JSpinner frequency = new JSpinner(new SpinnerNumberModel(7.83, 0.1, 20.0, 0.1));
    private final JSpinner amplitude = new JSpinner(new SpinnerNumberModel(0.8, 0.0, 1.0, 0.05));
    private final JComboBox<String> waveform = new JComboBox<>(new String[]{"sine", "triangle", "square"});
    private final transient BusEngine engine = new BusEngine(this::log);
    private final Scope scope = new Scope();
    private final javax.swing.Timer uiTimer;
    private boolean busy, syncing, closing;

    public QuantumBrowserBus() {
        super("Quantum Browser Bus | Local signal lab");
        setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);
        setMinimumSize(new Dimension(900, 700));
        setSize(1220, 820);
        setLocationRelativeTo(null);
        JPanel root = panel(new BorderLayout(22, 20));
        root.setBackground(BG);
        root.setBorder(new EmptyBorder(24, 28, 24, 28));
        setContentPane(root);

        JPanel header = panel(new BorderLayout(16, 12));
        header.setOpaque(false);
        JPanel title = panel(new GridLayout(2, 1, 0, 5));
        title.setOpaque(false);
        title.add(label("QUANTUM / BUS", TEXT, 26));
        title.add(label("LOCAL SIGNAL LAB   /   Desktop control center", MUTED, 12));
        header.add(title, BorderLayout.WEST);
        JPanel connection = panel(new GridLayout(2, 1, 0, 5));
        connection.setOpaque(false);
        state.setHorizontalAlignment(SwingConstants.RIGHT);
        endpoint.setHorizontalAlignment(SwingConstants.RIGHT);
        connection.add(state); connection.add(endpoint);
        header.add(connection, BorderLayout.EAST);
        root.add(header, BorderLayout.NORTH);

        JPanel center = panel(new BorderLayout(18, 18)); center.setOpaque(false);
        JPanel metrics = panel(new GridLayout(1, 4, 12, 0)); metrics.setOpaque(false);
        metrics.add(metric("CONNECTED TABS", clients)); metrics.add(metric("SIGNAL VALUE", value));
        metrics.add(metric("PACKETS GENERATED", packets)); metrics.add(metric("SESSION UPTIME", uptime));
        JPanel plots = panel(new BorderLayout(0, 18)); plots.setOpaque(false);
        plots.add(metrics, BorderLayout.NORTH);
        plots.add(scope, BorderLayout.CENTER);
        center.add(plots, BorderLayout.CENTER);

        JPanel controls = panel(new GridBagLayout());
        controls.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(BORDER), new EmptyBorder(14, 14, 14, 14)));
        GridBagConstraints c = new GridBagConstraints(); c.gridx = 0; c.gridy = 0; c.weightx = 1; c.fill = GridBagConstraints.HORIZONTAL;
        c.insets = new Insets(0, 0, 5, 0);
        controls.add(label("SIGNAL CONTROLS", TEAL, 12), c);
        addControl(controls, c, "Local port", port);
        addControl(controls, c, "Frequency / Hz", frequency);
        addControl(controls, c, "Amplitude / 0–1", amplitude);
        addControl(controls, c, "Waveform", waveform);
        for (JButton b : new JButton[]{start, stop, pause, browser}) { c.gridy++; controls.add(b, c); }
        c.gridy++; c.weighty = 1; controls.add(Box.createVerticalGlue(), c);
        c.gridy++; c.weighty = 0; controls.add(label("50 samples/s · loopback only", MUTED, 11), c);
        JScrollPane controlScroll = new JScrollPane(controls);
        controlScroll.setBorder(BorderFactory.createEmptyBorder());
        controlScroll.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        controlScroll.getVerticalScrollBar().setUnitIncrement(16);
        controlScroll.setPreferredSize(new Dimension(252, 1));
        center.add(controlScroll, BorderLayout.EAST);
        root.add(center, BorderLayout.CENTER);

        JPanel footer = panel(new BorderLayout(10, 8)); footer.setOpaque(false);
        JPanel logHead = panel(new BorderLayout()); logHead.setOpaque(false);
        logHead.add(label("SESSION ACTIVITY", MUTED, 11), BorderLayout.WEST);
        JPanel actions = panel(new FlowLayout(FlowLayout.RIGHT, 8, 0)); actions.setOpaque(false);
        JButton clear = button("Clear log", false), export = button("Export CSV", false);
        clear.addActionListener(e -> activity.setText("")); export.addActionListener(e -> exportCsv());
        actions.add(clear); actions.add(export); logHead.add(actions, BorderLayout.EAST);
        footer.add(logHead, BorderLayout.NORTH);
        activity.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        activity.setBackground(PANEL); activity.setForeground(MUTED); activity.setEditable(false);
        activity.setBorder(new EmptyBorder(10, 12, 10, 12));
        JScrollPane scroll = new JScrollPane(activity); scroll.setBorder(BorderFactory.createLineBorder(BORDER));
        footer.add(scroll, BorderLayout.CENTER);
        root.add(footer, BorderLayout.SOUTH);

        start.addActionListener(e -> startBus()); stop.addActionListener(e -> stopBus(false));
        pause.addActionListener(e -> { engine.setPaused(!engine.settings().paused()); refresh(); });
        browser.addActionListener(e -> openBrowser());
        frequency.addChangeListener(e -> updateSignal()); amplitude.addChangeListener(e -> updateSignal());
        waveform.addActionListener(e -> updateSignal());
        addWindowListener(new WindowAdapter() { @Override public void windowClosing(WindowEvent e) { closing = true; stopBus(true); } });
        uiTimer = new javax.swing.Timer(33, e -> { refresh(); scope.repaint(); }); uiTimer.start();
        log("Ready. Start the bus to stream a simulated signal to your browser.");
        refresh();
    }

    private static JPanel panel(LayoutManager layout) { JPanel p = new JPanel(layout); p.setBackground(PANEL); return p; }
    private static JLabel label(String text, Color color, int size) {
        JLabel l = new JLabel(text); l.setForeground(color); l.setFont(new Font("Segoe UI", Font.PLAIN, size)); return l;
    }
    private static JButton button(String text, boolean primary) {
        JButton b = new JButton(text); b.setFont(new Font("Segoe UI", Font.BOLD, 12));
        b.setBackground(primary ? TEAL : BORDER); b.setForeground(primary ? BG : TEXT);
        b.setFocusPainted(false); b.setBorder(new EmptyBorder(11, 14, 11, 14)); b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        return b;
    }
    private static JPanel metric(String title, JLabel value) {
        JPanel p = panel(new GridLayout(2, 1, 0, 5)); p.setBorder(new EmptyBorder(14, 18, 14, 18));
        p.add(label(title, MUTED, 10)); p.add(value); return p;
    }
    private static void addControl(JPanel p, GridBagConstraints c, String title, JComponent input) {
        c.gridy++; p.add(label(title, MUTED, 12), c); c.gridy++;
        input.setBackground(BG); input.setForeground(TEXT);
        if (input instanceof JTextField field) { field.setCaretColor(TEAL); field.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(BORDER), new EmptyBorder(3, 7, 3, 7))); }
        if (input instanceof JSpinner spinner && spinner.getEditor() instanceof JSpinner.DefaultEditor editor) {
            editor.getTextField().setBackground(BG); editor.getTextField().setForeground(TEXT); editor.getTextField().setCaretColor(TEAL);
            spinner.setBorder(BorderFactory.createLineBorder(BORDER));
        }
        input.setFont(new Font("Segoe UI", Font.PLAIN, 14)); input.setPreferredSize(new Dimension(190, 30)); p.add(input, c);
    }
    private void log(String message) {
        SwingUtilities.invokeLater(() -> {
            activity.append(LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")) + "  " + message + "\n");
            try { if (activity.getLineCount() > 150) activity.replaceRange("", 0, activity.getLineEndOffset(0)); }
            catch (javax.swing.text.BadLocationException ignored) { }
            activity.setCaretPosition(activity.getDocument().getLength());
        });
    }
    private void startBus() {
        if (busy || engine.isRunning()) return;
        final int requestedPort;
        try { requestedPort = Integer.parseInt(port.getText().trim()); validatePort(requestedPort); }
        catch (IllegalArgumentException e) { log("Enter a port from 1 to 65535."); port.requestFocusInWindow(); return; }
        busy = true; refresh();
        new SwingWorker<Void, Void>() {
            protected Void doInBackground() throws Exception { engine.start(requestedPort); return null; }
            protected void done() {
                try { get(); } catch (Exception e) { log("Could not start: " + rootMessage(e)); }
                busy = false; refresh(); if (closing) stopBus(true);
            }
        }.execute();
    }
    private void stopBus(boolean exit) {
        if (busy) return;
        busy = true; refresh();
        new SwingWorker<Void, Void>() {
            protected Void doInBackground() { engine.stop(); return null; }
            protected void done() { busy = false; refresh(); if (exit || closing) { uiTimer.stop(); dispose(); } }
        }.execute();
    }
    private void updateSignal() {
        if (syncing) return;
        try {
            frequency.commitEdit(); amplitude.commitEdit();
            engine.configure(((Number) frequency.getValue()).doubleValue(), ((Number) amplitude.getValue()).doubleValue(),
                    (String) waveform.getSelectedItem(), engine.settings().paused());
        } catch (Exception e) { log("Invalid signal settings: " + rootMessage(e)); }
    }
    private void refresh() {
        boolean online = engine.isRunning(); Settings s = engine.settings(); Sample last = engine.latest;
        start.setEnabled(!online && !busy); stop.setEnabled(online && !busy); browser.setEnabled(online && !busy);
        port.setEnabled(!online && !busy); pause.setEnabled(online && !busy);
        pause.setText(s.paused() ? "Resume signal" : "Pause signal");
        state.setText(busy ? "UPDATING…" : online ? (s.paused() ? "SIGNAL PAUSED" : "BUS ONLINE") : "OFFLINE");
        state.setForeground(online ? TEAL : MUTED);
        endpoint.setText(online ? engine.url() : "Start the bus to connect a browser");
        clients.setText(Integer.toString(engine.clientCount()));
        value.setText(String.format(Locale.ROOT, "%+.4f", last == null ? 0 : last.value()));
        packets.setText(String.format(Locale.ROOT, "%,d", last == null ? 0 : last.id()));
        long seconds = last == null ? 0 : (long) last.elapsed();
        uptime.setText(String.format(Locale.ROOT, "%02d:%02d", seconds / 60, seconds % 60));
        syncing = true;
        if (!frequency.getValue().equals(s.frequency())) frequency.setValue(s.frequency());
        if (!amplitude.getValue().equals(s.amplitude())) amplitude.setValue(s.amplitude());
        if (!waveform.getSelectedItem().equals(s.waveform())) waveform.setSelectedItem(s.waveform());
        syncing = false;
    }
    private void openBrowser() {
        String url = engine.url();
        new SwingWorker<Void, Void>() {
            protected Void doInBackground() throws Exception {
                if (!Desktop.isDesktopSupported() || !Desktop.getDesktop().isSupported(Desktop.Action.BROWSE))
                    throw new IOException("Open " + url + " manually in a browser.");
                Desktop.getDesktop().browse(URI.create(url)); return null;
            }
            protected void done() { try { get(); } catch (Exception e) { log(rootMessage(e)); } }
        }.execute();
    }
    private void exportCsv() {
        List<Sample> snapshot = engine.history();
        if (snapshot.isEmpty()) { log("No samples to export. Start the bus first."); return; }
        JFileChooser chooser = new JFileChooser(); chooser.setSelectedFile(new File("quantum-bus-samples.csv"));
        if (chooser.showSaveDialog(this) != JFileChooser.APPROVE_OPTION) return;
        Path target = chooser.getSelectedFile().toPath();
        if (Files.exists(target) && JOptionPane.showConfirmDialog(this, "Replace " + target.getFileName() + "?", "Export CSV",
                JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return;
        new SwingWorker<Void, Void>() {
            protected Void doInBackground() throws IOException { Files.writeString(target, csv(snapshot), StandardCharsets.UTF_8); return null; }
            protected void done() { try { get(); log("Exported " + snapshot.size() + " samples to " + target); }
                catch (Exception e) { log("Export failed: " + rootMessage(e)); } }
        }.execute();
    }
    private static String rootMessage(Throwable e) { while (e.getCause() != null) e = e.getCause(); return e.getMessage(); }
    static void validatePort(int port) { if (port < 1 || port > 65535) throw new IllegalArgumentException("Port must be 1–65535."); }

    private class Scope extends JPanel {
        private static final long serialVersionUID = 1L;
        Scope() { setBackground(PANEL); setBorder(BorderFactory.createLineBorder(BORDER)); }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); Graphics2D g = (Graphics2D) graphics.create();
            try {
                g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                int left = 54, top = 68, w = getWidth() - 78, h = getHeight() - 114;
                if (w <= 0 || h <= 0) return;
                g.setFont(new Font("Segoe UI", Font.BOLD, 14)); g.setColor(TEXT); g.drawString("Signal scope", 22, 30);
                g.setFont(new Font("Segoe UI", Font.PLAIN, 11)); g.setColor(MUTED); g.drawString("2 SECOND WINDOW  /  50 SAMPLES PER SECOND", 22, 49);
                for (int i = 0; i <= 8; i++) { int x = left + i * w / 8; g.setColor(BORDER); g.drawLine(x, top, x, top + h); }
                for (int i = 0; i <= 4; i++) {
                    int y = top + i * h / 4; g.setColor(BORDER); g.drawLine(left, y, left + w, y);
                    g.setColor(MUTED); g.drawString(String.format(Locale.ROOT, "%+.1f", 1 - i * .5), 15, y + 4);
                }
                g.setColor(MUTED); g.drawString("−2.0 s", left, top + h + 24); g.drawString("NOW", left + w - 28, top + h + 24);
                List<Sample> samples = engine.history();
                if (samples.size() < 2) { g.setColor(MUTED); g.drawString("Start the bus to see your signal", left + 20, top + h / 2); return; }
                double end = samples.get(samples.size() - 1).elapsed(); Path2D path = new Path2D.Double(); boolean first = true;
                for (Sample s : samples) {
                    if (s.elapsed() < end - 2) continue;
                    double x = left + (s.elapsed() - end + 2) / 2 * w, y = top + h / 2.0 - s.value() * h / 2.0;
                    if (first) { path.moveTo(x, y); first = false; } else path.lineTo(x, y);
                }
                g.setColor(new Color(82, 226, 189, 22)); g.setStroke(new BasicStroke(9, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)); g.draw(path);
                g.setColor(TEAL); g.setStroke(new BasicStroke(2, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)); g.draw(path);
            } finally { g.dispose(); }
        }
    }

    record Settings(double frequency, double amplitude, String waveform, boolean paused) {
        Settings {
            if (!Double.isFinite(frequency) || frequency < .1 || frequency > 20) throw new IllegalArgumentException("Frequency must be 0.1–20 Hz.");
            if (!Double.isFinite(amplitude) || amplitude < 0 || amplitude > 1) throw new IllegalArgumentException("Amplitude must be 0–1.");
            if (!Set.of("sine", "triangle", "square").contains(waveform)) throw new IllegalArgumentException("Unknown waveform.");
        }
    }
    record Sample(long id, long timestamp, double elapsed, double value, Settings settings, int clients, long dropped) {
        String json() {
            return String.format(Locale.ROOT,
                    "{\"id\":%d,\"timestamp\":%d,\"elapsed\":%.6f,\"mod\":%.6f,\"frequency\":%.2f,\"amplitude\":%.3f,\"waveform\":\"%s\",\"paused\":%b,\"clients\":%d,\"sampleRate\":50,\"dropped\":%d}",
                    id, timestamp, elapsed, value, settings.frequency(), settings.amplitude(), settings.waveform(), settings.paused(), clients, dropped);
        }
    }
    static String csv(List<Sample> samples) {
        StringBuilder b = new StringBuilder("id,timestamp_ms,elapsed_seconds,value,frequency_hz,amplitude,waveform,paused\n");
        for (Sample s : samples) b.append(String.format(Locale.ROOT, "%d,%d,%.6f,%.6f,%.2f,%.3f,%s,%b%n",
                s.id(), s.timestamp(), s.elapsed(), s.value(), s.settings().frequency(), s.settings().amplitude(), s.settings().waveform(), s.settings().paused()));
        return b.toString();
    }

    /** Sampling never performs network I/O. Every client has its own bounded queue. */
    static final class BusEngine {
        static final int MAX_CLIENTS = 16, HISTORY_SIZE = 1500;
        private final Consumer<String> logger;
        private final Set<Client> clients = ConcurrentHashMap.newKeySet();
        private final ArrayDeque<Sample> samples = new ArrayDeque<>();
        private final Object signalLock = new Object();
        private volatile Settings settings = new Settings(7.83, .8, "sine", false);
        private volatile boolean running;
        private volatile Sample latest;
        private HttpServer server;
        private ExecutorService workers;
        private ScheduledExecutorService clock;
        private long started, previous, sequence, dropped;
        private double phase;
        private int port;
        private byte[] dashboard;
        BusEngine(Consumer<String> logger) { this.logger = logger; }
        boolean isRunning() { return running; }
        Settings settings() { return settings; }
        int clientCount() { return clients.size(); }
        String url() { return "http://127.0.0.1:" + port + "/"; }
        List<Sample> history() { synchronized (samples) { return new ArrayList<>(samples); } }

        synchronized void start(int requestedPort) throws IOException {
            if (running) return;
            validatePort(requestedPort);
            try (InputStream input = QuantumBrowserBus.class.getResourceAsStream("/code.html")) {
                if (input != null) dashboard = input.readAllBytes();
                else {
                    Path file = Path.of("code.html");
                    if (!Files.isRegularFile(file)) throw new IOException("Missing code.html. Launch with run.bat from the project folder.");
                    dashboard = Files.readAllBytes(file);
                }
            }
            HttpServer newServer = HttpServer.create(new InetSocketAddress(InetAddress.getByName("127.0.0.1"), requestedPort), 0);
            ExecutorService newWorkers = Executors.newFixedThreadPool(MAX_CLIENTS + 6, daemonFactory("bus-http"));
            ScheduledExecutorService newClock = Executors.newSingleThreadScheduledExecutor(daemonFactory("bus-sampler"));
            try {
                newServer.createContext("/", this::route); newServer.setExecutor(newWorkers);
                server = newServer; workers = newWorkers; clock = newClock; port = requestedPort;
                synchronized (signalLock) { started = previous = System.nanoTime(); sequence = dropped = 0; phase = 0; latest = null; }
                synchronized (samples) { samples.clear(); }
                running = true; newServer.start(); newClock.scheduleAtFixedRate(this::tick, 0, 20, TimeUnit.MILLISECONDS);
                logger.accept("Bus online at " + url() + " · 50 samples/s.");
            } catch (RuntimeException e) {
                running = false; newServer.stop(0); newWorkers.shutdownNow(); newClock.shutdownNow(); throw e;
            }
        }
        synchronized void stop() {
            if (!running) return;
            running = false;
            clock.shutdownNow();
            // HttpServer.stop closes active sockets and unblocks slow SSE writers.
            server.stop(0);
            for (Client client : clients) client.close();
            clients.clear(); workers.shutdownNow();
            try { clock.awaitTermination(2, TimeUnit.SECONDS); workers.awaitTermination(2, TimeUnit.SECONDS); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            logger.accept("Bus stopped. All browser connections released.");
        }
        void configure(double frequency, double amplitude, String waveform, boolean paused) {
            Settings next = new Settings(frequency, amplitude, waveform, paused);
            synchronized (signalLock) {
                if (next.equals(settings)) return;
                if (running) advancePhase(System.nanoTime());
                settings = next;
            }
            logger.accept(String.format(Locale.ROOT, "Signal: %s · %.2f Hz · %.0f%% amplitude%s", waveform, frequency, amplitude * 100, paused ? " · paused" : ""));
        }
        void setPaused(boolean paused) { Settings s = settings; configure(s.frequency(), s.amplitude(), s.waveform(), paused); }
        private void advancePhase(long now) {
            if (!settings.paused()) phase = (phase + (now - previous) / 1e9 * settings.frequency()) % 1.0;
            previous = now;
        }
        static double signal(double phase, Settings s) {
            return s.amplitude() * switch (s.waveform()) {
                case "triangle" -> 2 / Math.PI * Math.asin(Math.sin(phase * Math.PI * 2));
                case "square" -> Math.sin(phase * Math.PI * 2) >= 0 ? 1 : -1;
                default -> Math.sin(phase * Math.PI * 2);
            };
        }
        private void tick() {
            if (!running) return;
            Sample sample;
            synchronized (signalLock) {
                long now = System.nanoTime(); advancePhase(now);
                sample = new Sample(++sequence, System.currentTimeMillis(), (now - started) / 1e9, signal(phase, settings), settings, clients.size(), dropped);
                latest = sample;
            }
            synchronized (samples) { samples.addLast(sample); if (samples.size() > HISTORY_SIZE) samples.removeFirst(); }
            for (Client c : clients) if (!c.queue.offer(sample)) { c.queue.poll(); c.queue.offer(sample); dropped++; }
        }
        private void route(HttpExchange exchange) throws IOException {
            String path = exchange.getRequestURI().getPath(); String method = exchange.getRequestMethod();
            exchange.getResponseHeaders().set("X-Content-Type-Options", "nosniff");
            exchange.getResponseHeaders().set("Cache-Control", "no-store");
            if (path.equals("/api/settings")) {
                if (!method.equals("POST")) { exchange.getResponseHeaders().set("Allow", "POST"); send(exchange, 405, "text/plain", "Use POST."); return; }
                settingsRequest(exchange); return;
            }
            if (!method.equals("GET")) { exchange.getResponseHeaders().set("Allow", "GET"); send(exchange, 405, "text/plain", "Use GET."); return; }
            switch (path) {
                case "/" -> {
                    exchange.getResponseHeaders().set("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");
                    send(exchange, 200, "text/html; charset=utf-8", dashboard);
                }
                case "/stream" -> stream(exchange);
                case "/api/status" -> { Sample s = latest; send(exchange, 200, "application/json", s == null ? "{}" : s.json()); }
                case "/api/export" -> {
                    exchange.getResponseHeaders().set("Content-Disposition", "attachment; filename=quantum-bus-samples.csv");
                    send(exchange, 200, "text/csv; charset=utf-8", csv(history()));
                }
                case "/favicon.ico" -> { exchange.sendResponseHeaders(204, -1); exchange.close(); }
                default -> send(exchange, 404, "text/plain", "Not found.");
            }
        }
        private void settingsRequest(HttpExchange e) throws IOException {
            String origin = e.getRequestHeaders().getFirst("Origin");
            if (!"dashboard".equals(e.getRequestHeaders().getFirst("X-Quantum-Client")) ||
                    (origin != null && !origin.equals("http://127.0.0.1:" + port) && !origin.equals("http://localhost:" + port))) {
                send(e, 403, "text/plain", "Use the local dashboard to change settings."); return;
            }
            byte[] body = e.getRequestBody().readNBytes(1025);
            if (body.length > 1024) { send(e, 413, "text/plain", "Settings request is too large."); return; }
            try {
                Map<String, String> fields = new HashMap<>();
                for (String pair : new String(body, StandardCharsets.UTF_8).split("&")) {
                    String[] bits = pair.split("=", 2);
                    if (bits.length != 2) throw new IllegalArgumentException("Invalid settings format.");
                    String key = URLDecoder.decode(bits[0], StandardCharsets.UTF_8);
                    if (!Set.of("frequency", "amplitude", "waveform", "paused").contains(key) || fields.containsKey(key))
                        throw new IllegalArgumentException("Unknown or duplicate setting.");
                    fields.put(key, URLDecoder.decode(bits[1], StandardCharsets.UTF_8));
                }
                synchronized (signalLock) {
                    Settings s = settings;
                    String paused = fields.getOrDefault("paused", Boolean.toString(s.paused()));
                    if (!paused.equals("true") && !paused.equals("false")) throw new IllegalArgumentException("Paused must be true or false.");
                    configure(Double.parseDouble(fields.getOrDefault("frequency", Double.toString(s.frequency()))),
                            Double.parseDouble(fields.getOrDefault("amplitude", Double.toString(s.amplitude()))),
                            fields.getOrDefault("waveform", s.waveform()), Boolean.parseBoolean(paused));
                }
                send(e, 200, "application/json", "{\"ok\":true}");
            } catch (IllegalArgumentException ex) { send(e, 400, "text/plain", ex.getMessage()); }
        }
        private void stream(HttpExchange e) throws IOException {
            Client client = new Client(e);
            synchronized (clients) {
                if (!running || clients.size() >= MAX_CLIENTS) { send(e, 503, "text/plain", "Connection limit reached. Close an unused tab and retry."); return; }
                clients.add(client);
            }
            try {
                e.getResponseHeaders().set("Content-Type", "text/event-stream; charset=utf-8");
                e.getResponseHeaders().set("Cache-Control", "no-cache");
                e.sendResponseHeaders(200, 0);
                OutputStream out = e.getResponseBody(); out.write("retry: 1500\n\n".getBytes(StandardCharsets.UTF_8)); out.flush();
                logger.accept("Browser connected · " + clients.size() + " active tab(s).");
                while (running && !Thread.currentThread().isInterrupted()) {
                    Sample s = client.queue.poll(1, TimeUnit.SECONDS);
                    String event = s == null ? ": heartbeat\n\n" : "id: " + s.id() + "\ndata: " + s.json() + "\n\n";
                    out.write(event.getBytes(StandardCharsets.UTF_8)); out.flush();
                }
            } catch (IOException ignored) {
                // A closed browser tab is normal, not a server failure.
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
            finally { clients.remove(client); client.close(); logger.accept("Browser disconnected · " + clients.size() + " active tab(s)."); }
        }
        private static void send(HttpExchange e, int status, String type, String body) throws IOException { send(e, status, type, body.getBytes(StandardCharsets.UTF_8)); }
        private static void send(HttpExchange e, int status, String type, byte[] body) throws IOException {
            e.getResponseHeaders().set("Content-Type", type); e.sendResponseHeaders(status, body.length);
            try (OutputStream out = e.getResponseBody()) { out.write(body); } finally { e.close(); }
        }
        private static ThreadFactory daemonFactory(String name) {
            return runnable -> { Thread thread = new Thread(runnable, name); thread.setDaemon(true); return thread; };
        }
        private static final class Client {
            final HttpExchange exchange; final ArrayBlockingQueue<Sample> queue = new ArrayBlockingQueue<>(8);
            Client(HttpExchange exchange) { this.exchange = exchange; }
            void close() { exchange.close(); }
        }
    }

    public static void main(String[] args) {
        boolean headless = false; int port = 7830;
        try {
            for (int i = 0; i < args.length; i++) {
                switch (args[i]) {
                    case "--headless" -> headless = true;
                    case "--port" -> { if (++i >= args.length) throw new IllegalArgumentException("Missing port."); port = Integer.parseInt(args[i]); validatePort(port); }
                    case "--help" -> { System.out.println("QuantumBrowserBus [--headless] [--port 7830]\nJDK 17+ · local simulated signals at 50 samples/s"); return; }
                    default -> throw new IllegalArgumentException("Unknown argument: " + args[i]);
                }
            }
            if (headless) {
                BusEngine engine = new BusEngine(System.out::println);
                Runtime.getRuntime().addShutdownHook(new Thread(engine::stop));
                engine.start(port); new CountDownLatch(1).await();
            } else {
                int initialPort = port;
                SwingUtilities.invokeLater(() -> {
                    UIManager.put("Panel.background", PANEL); UIManager.put("Label.foreground", TEXT);
                    QuantumBrowserBus app = new QuantumBrowserBus(); app.port.setText(Integer.toString(initialPort)); app.setVisible(true);
                });
            }
        } catch (Exception e) { System.err.println("Quantum Browser Bus: " + rootMessage(e)); System.exit(1); }
    }
}
