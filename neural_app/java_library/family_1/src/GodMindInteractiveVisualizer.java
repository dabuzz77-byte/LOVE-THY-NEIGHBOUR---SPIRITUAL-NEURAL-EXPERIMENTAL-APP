import neural.studio.*;
import javax.swing.*;
import javax.swing.border.*;
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import com.sun.net.httpserver.HttpServer;

/** A connected, interactive neural simulation. No external libraries or AI service required. */
public class GodMindInteractiveVisualizer extends SectionFrame {
    static final Color BG = new Color(8, 13, 24), CARD = new Color(14, 22, 37);
    static final Color BORDER = new Color(34, 48, 68), TEXT = new Color(232, 240, 251);
    static final Color MUTED = new Color(133, 154, 180), CYAN = new Color(83, 220, 242);
    static final Color MINT = new Color(105, 233, 180), VIOLET = new Color(164, 147, 255);
    static final Color AMBER = new Color(251, 196, 110);
    static final Font FONT = new Font("Segoe UI", Font.PLAIN, 13);
    final Dashboard dashboard;

    public GodMindInteractiveVisualizer() {
        super("GodMind | Interactive Neural Engine");
        dashboard = new Dashboard();
        setContentPane(dashboard);
        setDefaultCloseOperation(SectionFrame.DISPOSE_ON_CLOSE);
        setMinimumSize(new Dimension(1050, 780));
        setSize(1420, 1000);
        setLocationRelativeTo(null);
        addWindowListener(new WindowAdapter() {
            @Override public void windowClosed(WindowEvent event) { dashboard.close(); }
        });
        dashboard.start();
    }

    static void theme() {
        UIManager.put("Panel.background", BG);
        UIManager.put("Label.foreground", TEXT);
        UIManager.put("Label.font", FONT);
        UIManager.put("Button.font", FONT.deriveFont(Font.BOLD, 12));
        UIManager.put("CheckBox.font", FONT);
        UIManager.put("CheckBox.foreground", MUTED);
        UIManager.put("CheckBox.background", CARD);
        UIManager.put("Slider.background", CARD);
        UIManager.put("Slider.foreground", CYAN);
        UIManager.put("ComboBox.background", new Color(24, 36, 55));
        UIManager.put("ComboBox.foreground", TEXT);
        UIManager.put("ComboBox.selectionBackground", new Color(43, 71, 94));
        UIManager.put("ComboBox.selectionForeground", TEXT);
        UIManager.put("ComboBox.font", FONT);
        UIManager.put("TextField.caretForeground", CYAN);
        UIManager.put("ToolTip.background", CARD);
        UIManager.put("ToolTip.foreground", TEXT);
        UIManager.put("ScrollBar.width", 8);
    }

    static final class Edge {
        final int from, to;
        final double weight;
        Edge(int from, int to, double weight) { this.from = from; this.to = to; this.weight = weight; }
    }

    static final class Model {
        final List<Edge> edges = new ArrayList<>();
        double[] activation, stimulus, next, incoming, degree, bias;
        double time, coupling = 1.1;
        long steps, spikes;
        int count;
        boolean autoInput = true;
        private double nextPulse;
        private Random random;
        Model(int count) { reset(count); }
        void reset(int count) {
            if (count < 8 || count > 160) throw new IllegalArgumentException("Node count must be 8 to 160");
            this.count = count;
            random = new Random(4171L + count);
            activation = new double[count]; stimulus = new double[count]; next = new double[count];
            incoming = new double[count]; degree = new double[count]; bias = new double[count];
            edges.clear(); steps = spikes = 0; time = 0; nextPulse = 0.7;
            boolean[][] connected = new boolean[count][count];
            for (int i = 0; i < count; i++) {
                activation[i] = 0.12 + random.nextDouble() * 0.4;
                bias[i] = random.nextDouble() * 0.6 - 0.3;
                for (int j = 1; j <= 4; j++) {
                    int to = j <= 2 ? (i + j) % count : random.nextInt(count);
                    if (to != i && !connected[i][to]) {
                        connected[i][to] = true;
                        double w = random.nextDouble() < 0.15 ? -0.65 : 0.65 + random.nextDouble() * 0.6;
                        edges.add(new Edge(i, to, w));
                        degree[to] += Math.abs(w);
                    }
                }
            }
            pulse(0);
        }
        void pulse(int node) {
            if (node < 0 || node >= count) return;
            stimulus[node] = 3.6;
            activation[node] = Math.max(activation[node], 0.88);
        }
        void pulseAll() { for (int i = 0; i < count; i += Math.max(1, count / 6)) pulse(i); }
        void step(double dt) {
            if (!(dt > 0) || !Double.isFinite(dt)) return;
            dt = Math.min(dt, 0.05);
            time += dt; steps++;
            if (autoInput && time >= nextPulse) { pulse(random.nextInt(count)); nextPulse = time + 0.65; }
            Arrays.fill(incoming, 0);
            for (Edge e : edges) incoming[e.to] += activation[e.from] * e.weight;
            for (int i = 0; i < count; i++) {
                double signal = incoming[i] / Math.max(1.0, degree[i]);
                double target = 1.0 / (1.0 + Math.exp(-(4.4 * (coupling * signal - 0.48) + bias[i] + stimulus[i])));
                next[i] = activation[i] + (target - activation[i]) * (1 - Math.exp(-dt * 4));
                if (activation[i] < 0.65 && next[i] >= 0.65) spikes++;
                stimulus[i] *= Math.exp(-dt * 2.8);
            }
            double[] swap = activation; activation = next; next = swap;
        }
        double mean() { double sum = 0; for (double a : activation) sum += a; return sum / count; }
        int active() { int n = 0; for (double a : activation) if (a >= 0.65) n++; return n; }
        int links(int node) { int n = 0; for (Edge e : edges) if (e.to == node || e.from == node) n++; return n; }
        String json(boolean running) {
            StringBuilder s = new StringBuilder(4096);
            s.append("{\"engine\":\"GodMind\",\"type\":\"neural-simulation\",\"running\":").append(running);
            s.append(",\"steps\":").append(steps).append(",\"seconds\":").append(String.format(Locale.ROOT,"%.3f", time));
            s.append(",\"nodeCount\":").append(count).append(",\"edgeCount\":").append(edges.size());
            s.append(",\"coupling\":").append(coupling).append(",\"autoInput\":").append(autoInput);
            s.append(",\"thresholdCrossings\":").append(spikes).append(",\"activation\":[");
            for (int i = 0; i < count; i++) { if (i > 0) s.append(','); s.append(String.format(Locale.ROOT,"%.5f",activation[i])); }
            return s.append("]}").toString();
        }
        String csv() {
            StringBuilder s = new StringBuilder("node,activation,input,connections\n");
            for (int i = 0; i < count; i++) s.append(String.format(Locale.ROOT,"%d,%.6f,%.6f,%d%n",i,activation[i],stimulus[i],links(i)));
            return s.toString();
        }
    }

    /** Serves only immutable snapshots; the simulation stays confined to Swing's event thread. */
    static final class Telemetry implements AutoCloseable {
        volatile String state = "{}";
        HttpServer server;
        ExecutorService executor;
        synchronized int start(int port) throws IOException {
            if (server != null) return server.getAddress().getPort();
            HttpServer candidate = HttpServer.create(new InetSocketAddress("127.0.0.1", port), 0);
            ExecutorService workers = Executors.newFixedThreadPool(2, r -> { Thread t = new Thread(r,"GodMind-telemetry"); t.setDaemon(true); return t; });
            candidate.setExecutor(workers);
            candidate.createContext("/", exchange -> {
                try {
                    int code;
                    String body;
                    if (!"GET".equals(exchange.getRequestMethod())) {
                        code = 405; body = "{\"error\":\"GET only\"}"; exchange.getResponseHeaders().set("Allow","GET");
                    } else if ("/health".equals(exchange.getRequestURI().getPath())) {
                        code = 200; body = "{\"status\":\"ok\",\"engine\":\"GodMind\"}";
                    } else if ("/api/state".equals(exchange.getRequestURI().getPath())) {
                        code = 200; body = state;
                    } else { code = 404; body = "{\"error\":\"Use /health or /api/state\"}"; }
                    byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
                    exchange.getResponseHeaders().set("Content-Type","application/json; charset=utf-8");
                    exchange.getResponseHeaders().set("Cache-Control","no-store");
                    exchange.getResponseHeaders().set("X-Content-Type-Options","nosniff");
                    exchange.sendResponseHeaders(code,bytes.length);
                    exchange.getResponseBody().write(bytes);
                } finally { exchange.close(); }
            });
            try { candidate.start(); server = candidate; executor = workers; }
            catch (RuntimeException ex) { candidate.stop(0); workers.shutdownNow(); throw ex; }
            return server.getAddress().getPort();
        }
        public synchronized void close() {
            if (server != null) { server.stop(0); server = null; }
            if (executor != null) { executor.shutdownNow(); executor = null; }
        }
    }

    static URI validateEndpoint(String value) {
        URI uri = URI.create(value.trim());
        if (!("https".equalsIgnoreCase(uri.getScheme()) || "http".equalsIgnoreCase(uri.getScheme())) || uri.getHost() == null || uri.getUserInfo() != null || uri.getPort() > 65535 || uri.getPort() == 0)
            throw new IllegalArgumentException("Enter a complete http:// or https:// URL");
        return uri;
    }

    static final class Dashboard extends JPanel implements AutoCloseable {
        final Model model = new Model(64);
        final Telemetry telemetry = new Telemetry();
        final FieldView field = new FieldView(this);
        final TraceView trace = new TraceView();
        final JLabel activity = metricValue(), activeNodes = metricValue(), connections = metricValue(), fpsLabel = metricValue();
        final JLabel mode = label("SIMULATION ACTIVE",11,MINT), netBadge = label("NET / NOT CHECKED",11,MUTED);
        final JLabel selection = label("Select a node to inspect it",12,TEXT), selectedDetail = label("Click = pulse  /  drag = orbit",11,MUTED);
        final JLabel networkStatus = label("Not checked",12,MUTED), apiStatus = label("Starting local feed...",11,MUTED);
        final JLabel footer = label("SPACE  Pause    P  Pulse    R  Reset",11,MUTED);
        final JTextArea log = new JTextArea();
        final JButton pause = button("Pause",CYAN), checkNet = button("Check connection",CYAN);
        final JTextField endpoint = new JTextField("https://example.com");
        final JCheckBox internet = new JCheckBox("Check endpoint every 60 seconds",true);
        final JCheckBox api = new JCheckBox("Local telemetry API",true);
        final neural.studio.SharedTimer timer, netTimer;
        final ExecutorService networkExecutor = Executors.newFixedThreadPool(2, r -> { Thread t = new Thread(r,"GodMind-network"); t.setDaemon(true); return t; });
        final HttpClient client = HttpClient.newBuilder().executor(networkExecutor).connectTimeout(Duration.ofSeconds(5)).followRedirects(HttpClient.Redirect.NORMAL).build();
        CompletableFuture<?> pendingRequest;
        boolean running = true, closed, checking;
        double speed = 1, accumulator, sampleAccumulator;
        long lastFrame, fpsStart;
        int frames, measuredFps, selected = -1, requestGeneration;

        Dashboard() {
            super(new BorderLayout(16,16));
            setBackground(BG);
            setBorder(new EmptyBorder(22,26,16,26));
            add(header(),BorderLayout.NORTH);
            JPanel body = new JPanel(new BorderLayout(16,16)); body.setOpaque(false);
            JPanel main = new JPanel(new BorderLayout(0,14)); main.setOpaque(false);
            JPanel metrics = new JPanel(new GridLayout(1,4,12,0)); metrics.setOpaque(false);
            metrics.add(metric("MEAN ACTIVATION",activity,CYAN)); metrics.add(metric("FIRING NODES",activeNodes,MINT));
            metrics.add(metric("CONNECTIONS",connections,VIOLET)); metrics.add(metric("UPDATE RATE",fpsLabel,AMBER));
            main.add(metrics,BorderLayout.NORTH); main.add(field,BorderLayout.CENTER);
            JPanel lower = new JPanel(new BorderLayout(0,12)); lower.setOpaque(false);
            trace.setPreferredSize(new Dimension(400,108)); lower.add(trace,BorderLayout.NORTH);
            lower.add(logPanel(),BorderLayout.CENTER); main.add(lower,BorderLayout.SOUTH);
            body.add(main,BorderLayout.CENTER);
            JScrollPane controls = new JScrollPane(controlPanel()); controls.setPreferredSize(new Dimension(298,100));
            controls.setBorder(BorderFactory.createLineBorder(BORDER)); controls.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
            controls.getVerticalScrollBar().setUnitIncrement(18); controls.getViewport().setBackground(CARD);
            body.add(controls,BorderLayout.EAST); add(body,BorderLayout.CENTER);
            JPanel bottom = new JPanel(new BorderLayout()); bottom.setOpaque(false); bottom.add(footer,BorderLayout.WEST);
            bottom.add(label("RECURRENT NETWORK  /  LOCAL SIMULATION",10,MUTED),BorderLayout.EAST); add(bottom,BorderLayout.SOUTH);
            timer = new neural.studio.SharedTimer(16,e -> onFrame()); timer.setCoalesce(true);
            netTimer = new neural.studio.SharedTimer(60000,e -> { if (internet.isSelected()) checkConnection(); });
            key("SPACE","pause",this::togglePause); key("P","pulse",this::pulse); key("R","reset",this::reset);
            updateReadouts(); log("Engine ready. Weighted recurrent network initialized.");
            log("Select a node to inject a signal; drag the field to rotate.");
        }
        JPanel header() {
            JPanel h = new JPanel(new BorderLayout()); h.setOpaque(false); h.setBorder(new EmptyBorder(0,0,5,0));
            JPanel titles = new JPanel(new GridLayout(2,1,0,3)); titles.setOpaque(false);
            titles.add(label("GODMIND  /  NEURAL ENGINE",23,TEXT)); titles.add(label("Explore the connections. Shape the signal.",12,MUTED));
            h.add(titles,BorderLayout.WEST);
            JPanel badges = new JPanel(new FlowLayout(FlowLayout.RIGHT,14,10)); badges.setOpaque(false); badges.add(mode); badges.add(netBadge);
            h.add(badges,BorderLayout.EAST); return h;
        }
        JPanel logPanel() {
            JPanel p = card(new BorderLayout(0,8)); p.setBorder(new CompoundBorder(new LineBorder(BORDER),new EmptyBorder(12,16,10,16)));
            p.add(label("EVENT STREAM",10,MUTED),BorderLayout.NORTH);
            log.setEditable(false); log.setBackground(CARD); log.setForeground(new Color(144,184,198));
            log.setFont(new Font("Consolas",Font.PLAIN,11)); log.setRows(3); log.setLineWrap(true); log.setWrapStyleWord(true);
            JScrollPane scroll = new JScrollPane(log); scroll.setBorder(null); scroll.setPreferredSize(new Dimension(100,54));
            p.add(scroll,BorderLayout.CENTER); return p;
        }
        JPanel controlPanel() {
            JPanel p = new JPanel(); p.setBackground(CARD); p.setLayout(new BoxLayout(p,BoxLayout.Y_AXIS)); p.setBorder(new EmptyBorder(18,16,18,16));
            section(p,"ENGINE CONTROLS");
            JPanel actions = new JPanel(new GridLayout(1,3,6,0)); actions.setOpaque(false);
            pause.addActionListener(e -> togglePause()); actions.add(pause);
            JButton pulse = button("Pulse",MINT); pulse.addActionListener(e -> pulse()); actions.add(pulse);
            JButton reset = button("Reset",MUTED); reset.addActionListener(e -> reset()); actions.add(reset); addRow(p,actions,34); gap(p,16);
            slider(p,"Nodes",24,128,model.count,v -> { if (v != model.count) { model.reset(v); selected = -1; field.invalidateProjection(); trace.clear(); accumulator = sampleAccumulator = 0; updateReadouts(); log("Network rebuilt with " + v + " nodes."); } },v -> Integer.toString(v));
            slider(p,"Simulation speed",25,200,100,v -> speed = v / 100.0,v -> String.format(Locale.ROOT,"%.2fx",v/100.0));
            slider(p,"Signal coupling",20,200,110,v -> model.coupling = v / 100.0,v -> String.format(Locale.ROOT,"%.2f",v/100.0));
            JCheckBox auto = new JCheckBox("Automatic signal input",true); auto.addActionListener(e -> model.autoInput = auto.isSelected()); addRow(p,auto,27);
            gap(p,16); section(p,"FIELD APPEARANCE");
            JComboBox<String> layout = new JComboBox<>(new String[]{"Sphere","Orbit","Helix"}); layout.addActionListener(e -> { field.layout = (String)layout.getSelectedItem(); field.invalidateProjection(); field.repaint(); });
            addRow(p,layout,30); gap(p,8);
            JCheckBox rotate = new JCheckBox("Rotate field",true); rotate.addActionListener(e -> field.rotate = rotate.isSelected()); addRow(p,rotate,26);
            JCheckBox labels = new JCheckBox("Show node labels",false); labels.addActionListener(e -> { field.labels = labels.isSelected(); field.repaint(); }); addRow(p,labels,26);
            gap(p,10); addRow(p,selection,22); addRow(p,selectedDetail,22);
            gap(p,18); section(p,"NETWORK LINK");
            addRow(p,networkStatus,22); gap(p,7);
            endpoint.setBackground(new Color(8,16,29)); endpoint.setForeground(TEXT); endpoint.setFont(FONT.deriveFont(12f));
            endpoint.setBorder(new CompoundBorder(new LineBorder(BORDER),new EmptyBorder(6,8,6,8)));
            endpoint.setToolTipText("Public endpoint to check. Only a HEAD request is sent; no simulation data is uploaded.");
            endpoint.addActionListener(e -> checkConnection()); addRow(p,endpoint,32); gap(p,8);
            checkNet.addActionListener(e -> checkConnection()); addRow(p,checkNet,32); gap(p,7);
            internet.setFont(FONT.deriveFont(11f)); internet.addActionListener(e -> { if (internet.isSelected()) checkConnection(); else cancelCheck(); }); addRow(p,internet,26);
            api.addActionListener(e -> setTelemetry(api.isSelected())); addRow(p,api,26); addRow(p,apiStatus,21);
            gap(p,18); section(p,"CAPTURE SESSION");
            JPanel exports = new JPanel(new GridLayout(1,2,8,0)); exports.setOpaque(false);
            JButton png = button("Save PNG",TEXT); png.addActionListener(e -> export(true)); exports.add(png);
            JButton csv = button("Export CSV",TEXT); csv.addActionListener(e -> export(false)); exports.add(csv); addRow(p,exports,33);
            gap(p,10); addRow(p,label("Wheel = zoom  /  double-click = focus",10,MUTED),20);
            p.add(Box.createVerticalGlue()); return p;
        }
        void slider(JPanel parent,String text,int min,int max,int initial,java.util.function.IntConsumer action,java.util.function.IntFunction<String> format) {
            JPanel row = new JPanel(new BorderLayout()); row.setOpaque(false); row.add(label(text,12,MUTED),BorderLayout.WEST);
            JLabel value = label(format.apply(initial),12,TEXT); row.add(value,BorderLayout.EAST); addRow(parent,row,20);
            JSlider slider = new JSlider(min,max,initial); slider.setFocusable(false);
            slider.addChangeListener(e -> { value.setText(format.apply(slider.getValue())); if (!slider.getValueIsAdjusting()) action.accept(slider.getValue()); });
            addRow(parent,slider,27); gap(parent,9);
        }
        void key(String stroke,String name,Runnable action) {
            getInputMap(WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(stroke),name);
            getActionMap().put(name,new AbstractAction() { public void actionPerformed(ActionEvent e) {
                if (!(KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner() instanceof javax.swing.text.JTextComponent)) action.run();
            }});
        }
        void start() {
            lastFrame = fpsStart = System.nanoTime(); timer.start(); netTimer.start();
            
        }
        void onFrame() {
            long now = System.nanoTime(); double dt = Math.min(0.1,(now-lastFrame)/1e9); lastFrame = now;
            frames++;
            if (now-fpsStart >= 1000000000L) { measuredFps = (int)Math.round(frames*1e9/(now-fpsStart)); frames = 0; fpsStart = now; }
            if (running) {
                accumulator += dt * speed;
                while (accumulator >= 1.0/60) { model.step(1.0/60); accumulator -= 1.0/60; }
                if (field.rotate) field.yaw += dt * 0.10;
                sampleAccumulator += dt;
                if (sampleAccumulator >= 0.1) { sampleAccumulator = 0; trace.push(model.mean()); }
            }
            if (frames % 6 == 0) updateReadouts();
            field.repaint(); trace.repaint();
        }
        void updateReadouts() {
            activity.setText(String.format(Locale.ROOT,"%.1f%%",model.mean()*100));
            activeNodes.setText(model.active() + " / " + model.count);
            connections.setText(Integer.toString(model.edges.size())); fpsLabel.setText(measuredFps == 0 ? "--" : measuredFps + " fps");
            mode.setText(running ? "SIMULATION ACTIVE" : "SIMULATION PAUSED"); mode.setForeground(running ? MINT : AMBER);
            if (selected >= 0 && selected < model.count) {
                selection.setText(String.format(Locale.ROOT,"NODE %02d  /  %.1f%% active",selected,model.activation[selected]*100));
                selectedDetail.setText(model.links(selected) + " connections  /  click to stimulate");
            } else { selection.setText("Select a node to inspect it"); selectedDetail.setText("Click = pulse  /  drag = orbit"); }
            telemetry.state = model.json(running);
        }
        void togglePause() { running = !running; pause.setText(running ? "Pause" : "Resume"); accumulator = 0; updateReadouts(); log(running ? "Simulation resumed." : "Simulation paused. Network checks remain available."); }
        void pulse() { if (selected >= 0) { model.pulse(selected); log("Signal injected into node " + selected + "."); } else { model.pulseAll(); log("Signal burst injected across the network."); } updateReadouts(); field.repaint(); }
        void reset() { model.reset(model.count); selected = -1; trace.clear(); accumulator = sampleAccumulator = 0; field.yaw = 0.35; field.pitch = -0.18; field.zoom = 1; updateReadouts(); field.repaint(); log("Network state and camera reset."); }
        void log(String text) {
            log.append(LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")) + "  " + text + "\n");
            while (log.getLineCount() > 70) try { log.replaceRange("",0,log.getLineEndOffset(0)); } catch (Exception ignored) { break; }
            log.setCaretPosition(log.getDocument().getLength());
        }
        void setTelemetry(boolean enabled) {
            if (!enabled) { telemetry.close(); apiStatus.setText("Local feed is off"); apiStatus.setForeground(MUTED); log("Local telemetry stopped."); return; }
            try {
                int port;
                try { port = telemetry.start(8765); } catch (BindException busy) { port = telemetry.start(0); }
                apiStatus.setText("127.0.0.1:" + port + "/api/state"); apiStatus.setForeground(MINT); apiStatus.setToolTipText("Read-only JSON feed, accessible from this computer.");
                log("Local telemetry active at http://127.0.0.1:" + port + "/api/state");
            } catch (IOException | RuntimeException ex) { api.setSelected(false); apiStatus.setText("Could not start local feed"); apiStatus.setForeground(AMBER); log("Telemetry: " + shortError(ex)); }
        }
        void cancelCheck() {
            requestGeneration++;
            if (pendingRequest != null) pendingRequest.cancel(true);
            checking = false; checkNet.setEnabled(true);
            networkStatus.setText("Automatic checks off"); networkStatus.setForeground(MUTED); netBadge.setText("NET / MANUAL"); netBadge.setForeground(MUTED);
        }
        void checkConnection() {
            if (closed || checking) return;
            URI uri;
            HttpRequest request;
            try {
                uri = validateEndpoint(endpoint.getText());
                request = HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(8)).header("User-Agent","GodMindVisualizer/2.0").method("HEAD",HttpRequest.BodyPublishers.noBody()).build();
            }
            catch (IllegalArgumentException ex) { networkStatus.setText("Enter a valid HTTP(S) URL"); networkStatus.setForeground(AMBER); log("Connection check: invalid endpoint URL."); return; }
            final int generation = ++requestGeneration;
            checking = true; checkNet.setEnabled(false); networkStatus.setText("Connecting to " + uri.getHost() + "..."); networkStatus.setForeground(CYAN);
            netBadge.setText("NET / CONNECTING"); netBadge.setForeground(CYAN);
            long start = System.nanoTime();
            pendingRequest = client.sendAsync(request,HttpResponse.BodyHandlers.discarding()).whenComplete((response,error) -> SwingUtilities.invokeLater(() -> {
                if (closed || generation != requestGeneration) return;
                checking = false; checkNet.setEnabled(true);
                long ms = (System.nanoTime()-start)/1000000;
                boolean ok = error == null && response.statusCode() >= 200 && response.statusCode() < 400;
                String status = error != null ? shortError(error) : "HTTP " + response.statusCode();
                networkStatus.setText(ok ? "Endpoint reachable  /  " + ms + " ms" : "Check failed  /  " + status);
                networkStatus.setToolTipText(error != null ? shortError(error) : uri.toString() + " - " + status);
                networkStatus.setForeground(ok ? MINT : AMBER); netBadge.setText(ok ? "NET / ONLINE" : "NET / CHECK FAILED"); netBadge.setForeground(ok ? MINT : AMBER);
                log(ok ? "Endpoint responded: " + uri.getHost() + " / " + status + " / " + ms + " ms." : "Endpoint check failed: " + status + ".");
            }));
        }
        void export(boolean image) {
            SectionFileChooser chooser = new SectionFileChooser();
            chooser.setDialogTitle(image ? "Save visualization" : "Export current node state");
            String ext = image ? ".png" : ".csv";
            chooser.setSelectedFile(new File("godmind-" + System.currentTimeMillis() + ext));
            chooser.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(image ? "PNG image" : "CSV data",image ? "png" : "csv"));
            if (chooser.showSaveDialog(this) != SectionFileChooser.APPROVE_OPTION) return;
            File target = chooser.getSelectedFile(); if (!target.getName().toLowerCase(Locale.ROOT).endsWith(ext)) target = new File(target.getPath()+ext);
            if (target.exists() && SectionDialogs.showConfirmDialog(this,"Replace " + target.getName() + "?","File exists",JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return;
            final File file = target;
            final BufferedImage png;
            if (image) { png = new BufferedImage(getWidth(),getHeight(),BufferedImage.TYPE_INT_RGB); Graphics2D g = png.createGraphics(); printAll(g); g.dispose(); } else png = null;
            final String csv = image ? null : model.csv();
            new SharedSwingWorker<Void,Void>() {
                protected Void doInBackground() throws Exception { if (image) ImageIO.write(png,"png",file); else Files.write(file.toPath(),csv.getBytes(StandardCharsets.UTF_8)); return null; }
                protected void done() { try { get(); log("Saved " + file.getName()); } catch (Exception ex) { log("Export failed: " + shortError(ex)); SectionDialogs.showMessageDialog(Dashboard.this,"Could not save file: " + shortError(ex),"Export failed",JOptionPane.ERROR_MESSAGE); } }
            }.execute();
        }
        public void close() { if (closed) return; closed = true; timer.stop(); netTimer.stop(); requestGeneration++; if (pendingRequest != null) pendingRequest.cancel(true); telemetry.close(); networkExecutor.shutdownNow(); }
    }

    static final class FieldView extends JPanel {
        final Dashboard d;
        double yaw = 0.35, pitch = -0.18, zoom = 1;
        boolean rotate = true, labels;
        String layout = "Sphere";
        double[] px = new double[0], py = new double[0], depth = new double[0];
        int hover = -1, pressX, pressY, lastX, lastY;
        boolean dragged;
        FieldView(Dashboard dashboard) {
            d = dashboard; setOpaque(true); setBackground(CARD); setBorder(new LineBorder(BORDER));
            setPreferredSize(new Dimension(680,360));
            MouseAdapter mouse = new MouseAdapter() {
                public void mousePressed(MouseEvent e) { pressX = lastX = e.getX(); pressY = lastY = e.getY(); dragged = false; }
                public void mouseDragged(MouseEvent e) {
                    if (Math.abs(e.getX()-pressX)+Math.abs(e.getY()-pressY) > 5) dragged = true;
                    yaw += (e.getX()-lastX)*0.008; pitch = Math.max(-1.3,Math.min(1.3,pitch+(e.getY()-lastY)*0.008)); lastX = e.getX(); lastY = e.getY(); repaint();
                }
                public void mouseReleased(MouseEvent e) {
                    if (!dragged) { int node = hit(e.getX(),e.getY()); if (node >= 0) { d.selected = node; d.pulse(); } else { d.selected = -1; d.updateReadouts(); } }
                }
                public void mouseClicked(MouseEvent e) { if (e.getClickCount() == 2 && hit(e.getX(),e.getY()) < 0) { zoom = 1; yaw = 0.35; pitch = -0.18; repaint(); } }
                public void mouseMoved(MouseEvent e) { hover = hit(e.getX(),e.getY()); setCursor(Cursor.getPredefinedCursor(hover >= 0 ? Cursor.HAND_CURSOR : Cursor.MOVE_CURSOR)); repaint(); }
                public void mouseExited(MouseEvent e) { hover = -1; repaint(); }
                public void mouseWheelMoved(MouseWheelEvent e) { zoom = Math.max(0.45,Math.min(2.2,zoom-e.getPreciseWheelRotation()*0.09)); repaint(); }
            };
            addMouseListener(mouse); addMouseMotionListener(mouse); addMouseWheelListener(mouse);
        }
        void invalidateProjection() { px = new double[0]; hover = -1; }
        int hit(int x,int y) {
            int best = -1; double nearest = 18*18;
            for (int i = 0; i < px.length; i++) { double distance = Math.pow(x-px[i],2)+Math.pow(y-py[i],2); if (distance < nearest) { nearest = distance; best = i; } }
            return best;
        }
        void project() {
            int n = d.model.count;
            if (px.length != n) { px = new double[n]; py = new double[n]; depth = new double[n]; }
            double scale = Math.min(getWidth()*0.33,(getHeight()-125)*0.45)*zoom;
            double cy = 80+(getHeight()-115)*0.50, cx = getWidth()*0.50;
            for (int i = 0; i < n; i++) {
                double x,y,z;
                if ("Orbit".equals(layout)) {
                    double a = i*2*Math.PI/n*3; double radius = 0.55+(i%3)*0.22;
                    x = Math.cos(a)*radius; z = Math.sin(a)*radius; y = (i%3-1)*0.34;
                } else if ("Helix".equals(layout)) {
                    double a = i*2*Math.PI/n*2.7; x = Math.cos(a)*0.70; z = Math.sin(a)*0.70; y = (i/(double)(n-1)-0.5)*1.9;
                } else {
                    y = 1-2*(i+0.5)/n; double radius = Math.sqrt(1-y*y); double a = i*Math.PI*(3-Math.sqrt(5));
                    x = Math.cos(a)*radius; z = Math.sin(a)*radius;
                }
                double rx = x*Math.cos(yaw)+z*Math.sin(yaw), rz = -x*Math.sin(yaw)+z*Math.cos(yaw);
                double ry = y*Math.cos(pitch)-rz*Math.sin(pitch); rz = y*Math.sin(pitch)+rz*Math.cos(pitch);
                depth[i] = rz; double perspective = 3.7/(3.7-rz);
                px[i] = cx+rx*scale*perspective; py[i] = cy+ry*scale*perspective;
            }
        }
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); Graphics2D g = (Graphics2D)graphics.create(); quality(g);
            int w = getWidth(),h = getHeight();
            g.setPaint(new GradientPaint(0,0,new Color(15,25,42),w,h,new Color(8,15,29))); g.fillRect(0,0,w,h);
            g.setColor(new Color(33,49,66,95));
            for (int x = 22; x < w; x += 28) for (int y = 98; y < h-26; y += 28) g.fillRect(x,y,1,1);
            g.setFont(FONT.deriveFont(Font.BOLD,10)); g.setColor(CYAN); g.drawString("LIVE FIELD  /  " + d.model.count + " NODES",22,28);
            g.setFont(FONT.deriveFont(Font.PLAIN,24)); g.setColor(TEXT); g.drawString("A network in motion.",22,60);
            String time = String.format(Locale.ROOT,"T + %.1fs",d.model.time); g.setFont(new Font("Consolas",Font.PLAIN,11)); g.setColor(MUTED); g.drawString(time,w-g.getFontMetrics().stringWidth(time)-22,29);
            project();
            Shape clip = g.getClip(); g.clipRect(1,80,w-2,Math.max(1,h-112));
            int cx = w/2, cy = (int)(80+(h-115)*0.50); int radius = (int)(Math.min(w*0.33,(h-125)*0.45)*zoom);
            g.setStroke(new BasicStroke(1)); g.setColor(new Color(47,84,110,70)); g.drawOval(cx-radius-30,cy-radius-30,(radius+30)*2,(radius+30)*2);
            g.drawLine(cx-8,cy,cx+8,cy); g.drawLine(cx,cy-8,cx,cy+8);
            for (Edge e : d.model.edges) {
                double strength = d.model.activation[e.from]; boolean focus = d.selected == e.from || d.selected == e.to;
                int alpha = (int)(24+strength*95+(depth[e.from]+1)*14);
                Color base = e.weight < 0 ? VIOLET : CYAN;
                g.setColor(new Color(base.getRed(),base.getGreen(),base.getBlue(),focus ? 205 : Math.min(150,alpha)));
                g.setStroke(new BasicStroke(focus ? 1.6f : 0.65f));
                g.draw(new Line2D.Double(px[e.from],py[e.from],px[e.to],py[e.to]));
                if (strength > 0.35) {
                    double t = (d.model.time*0.50+e.from*0.173+e.to*0.061)%1;
                    double x = px[e.from]+(px[e.to]-px[e.from])*t, y = py[e.from]+(py[e.to]-py[e.from])*t;
                    g.setColor(new Color(base.getRed(),base.getGreen(),base.getBlue(),(int)(strength*180)));
                    g.fill(new Ellipse2D.Double(x-1.6,y-1.6,3.2,3.2));
                }
            }
            Integer[] order = new Integer[d.model.count]; for (int i = 0; i < order.length; i++) order[i] = i;
            Arrays.sort(order,Comparator.comparingDouble(i -> depth[i]));
            for (int i : order) {
                double a = d.model.activation[i], r = 3.2+(depth[i]+1)*1.5+a*3.5;
                Color base = i%3 == 0 ? CYAN : i%3 == 1 ? MINT : VIOLET;
                for (int ring = 3; ring >= 1; ring--) { g.setColor(new Color(base.getRed(),base.getGreen(),base.getBlue(),(int)(a*13))); double glow = r+ring*4; g.fill(new Ellipse2D.Double(px[i]-glow,py[i]-glow,glow*2,glow*2)); }
                g.setColor(new Color(base.getRed(),base.getGreen(),base.getBlue(),(int)(100+a*155))); g.fill(new Ellipse2D.Double(px[i]-r,py[i]-r,r*2,r*2));
                g.setColor(new Color(234,255,255,(int)(90+a*165))); g.fill(new Ellipse2D.Double(px[i]-1.8,py[i]-1.8,3.6,3.6));
                if (i == d.selected || i == hover) { g.setStroke(new BasicStroke(1.3f)); g.setColor(TEXT); g.draw(new Ellipse2D.Double(px[i]-r-5,py[i]-r-5,(r+5)*2,(r+5)*2)); }
                if (labels || i == d.selected || i == hover) { g.setFont(new Font("Consolas",Font.PLAIN,10)); g.setColor(TEXT); g.drawString(String.format(Locale.ROOT,"N%02d  %.0f%%",i,a*100),(int)(px[i]+r+7),(int)py[i]-5); }
            }
            g.setClip(clip); g.setFont(FONT.deriveFont(10f));
            g.setColor(CYAN); g.fillOval(22,h-22,5,5); g.setColor(MUTED); g.drawString("Excitatory links",34,h-17);
            g.setColor(VIOLET); g.fillOval(146,h-22,5,5); g.setColor(MUTED); g.drawString("Inhibitory links",158,h-17);
            String hint = "SELECT / STIMULATE / ORBIT"; g.drawString(hint,w-g.getFontMetrics().stringWidth(hint)-22,h-17);
            g.dispose();
        }
    }

    static final class TraceView extends JPanel {
        final double[] history = new double[240]; int size, cursor;
        TraceView() { setBackground(CARD); setBorder(new LineBorder(BORDER)); }
        void push(double x) { history[cursor] = x; cursor = (cursor+1)%history.length; size = Math.min(size+1,history.length); }
        void clear() { size = cursor = 0; repaint(); }
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); Graphics2D g = (Graphics2D)graphics.create(); quality(g);
            int w = getWidth(),h = getHeight(); g.setFont(FONT.deriveFont(Font.BOLD,10)); g.setColor(MUTED); g.drawString("ACTIVATION HISTORY",18,22);
            g.setFont(FONT.deriveFont(10f)); g.drawString("24 s window  /  0 - 100%",w-160,22);
            g.setColor(BORDER); g.drawLine(18,h-22,w-18,h-22); g.drawLine(18,43,w-18,43);
            if (size > 1) {
                Path2D line = new Path2D.Double(); double endX = 18;
                for (int j = 0; j < size; j++) { int idx = (cursor-size+j+history.length)%history.length; double x = 18+(w-36)*j/(double)(history.length-1); double y = h-22-history[idx]*(h-60); if (j == 0) line.moveTo(x,y); else line.lineTo(x,y); endX = x; }
                Path2D fill = (Path2D)line.clone(); fill.lineTo(endX,h-22); fill.lineTo(18,h-22); fill.closePath();
                g.setPaint(new GradientPaint(0,35,new Color(83,220,242,65),0,h,new Color(83,220,242,0))); g.fill(fill);
                g.setStroke(new BasicStroke(1.7f)); g.setColor(CYAN); g.draw(line);
            }
            g.dispose();
        }
    }

    static JLabel label(String text,int size,Color color) { JLabel l = new JLabel(text); l.setFont(FONT.deriveFont((float)size)); l.setForeground(color); return l; }
    static JLabel metricValue() { JLabel l = label("--",25,TEXT); l.setBorder(new EmptyBorder(6,0,0,0)); return l; }
    static JPanel card(LayoutManager layout) { JPanel p = new JPanel(layout); p.setBackground(CARD); return p; }
    static JPanel metric(String title,JLabel value,Color color) {
        JPanel p = card(new BorderLayout()); p.setBorder(new CompoundBorder(new LineBorder(BORDER),new EmptyBorder(13,16,13,16)));
        p.add(label(title,9,MUTED),BorderLayout.NORTH); value.setForeground(color); p.add(value,BorderLayout.CENTER); return p;
    }
    static JButton button(String title,Color color) {
        JButton b = new JButton(title); b.setBackground(new Color(24,37,55)); b.setForeground(color); b.setFocusPainted(false);
        b.setBorder(new CompoundBorder(new LineBorder(new Color(44,63,84)),new EmptyBorder(7,8,7,8)));
        b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)); b.setFont(FONT.deriveFont(Font.BOLD,11)); return b;
    }
    static void section(JPanel p,String text) { addRow(p,label(text,10,MUTED),20); gap(p,9); }
    static void addRow(JPanel parent,JComponent child,int height) { child.setAlignmentX(Component.LEFT_ALIGNMENT); child.setMaximumSize(new Dimension(Integer.MAX_VALUE,height)); child.setPreferredSize(new Dimension(240,height)); parent.add(child); }
    static void gap(JPanel p,int pixels) { p.add(Box.createVerticalStrut(pixels)); }
    static void quality(Graphics2D g) { g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON); g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,RenderingHints.VALUE_TEXT_ANTIALIAS_ON); g.setRenderingHint(RenderingHints.KEY_RENDERING,RenderingHints.VALUE_RENDER_QUALITY); }
    static String shortError(Throwable error) { while (error.getCause() != null) error = error.getCause(); String s = error.getMessage(); return s == null || s.isEmpty() ? error.getClass().getSimpleName() : s.substring(0,Math.min(s.length(),100)); }
    static void layoutTree(Container c) { c.doLayout(); for (Component child : c.getComponents()) if (child instanceof Container) layoutTree((Container)child); }
    static void snapshot(Path path) throws Exception {
        SwingUtilities.invokeAndWait(() -> {
            Dashboard d = new Dashboard();
            try {
                d.setSize(1420,1000); layoutTree(d);
                for (int i = 0; i < 1440; i++) { d.model.step(1.0/60); if (i%6 == 0) d.trace.push(d.model.mean()); }
                d.selected = 9; d.updateReadouts(); d.apiStatus.setText("Preview / feed not started"); d.log("Preview: 24 seconds of simulated activity.");
                BufferedImage image = new BufferedImage(d.getWidth(),d.getHeight(),BufferedImage.TYPE_INT_RGB);
                Graphics2D g = image.createGraphics(); d.printAll(g); g.dispose();
                ImageIO.write(image,"png",path.toFile());
            } catch (IOException ex) { throw new UncheckedIOException(ex); } finally { d.close(); }
        });
    }
    public static void main(String[] args) throws Exception {
        theme();
        if (args.length >= 2 && "--snapshot".equals(args[0])) { snapshot(Paths.get(args[1])); return; }
        SwingUtilities.invokeLater(() -> new GodMindInteractiveVisualizer().setVisible(true));
    }
}
