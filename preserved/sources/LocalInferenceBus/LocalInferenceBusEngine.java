import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.nio.file.*;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.concurrent.*;

/** Local telemetry, an actual 3-10-4 neural classifier, and an activity-driven canvas. */
@SuppressWarnings("serial")
public final class LocalInferenceBusEngine extends JFrame {
    static final Color BG = new Color(8, 14, 23), PANEL = new Color(14, 23, 35);
    static final Color LINE = new Color(34, 49, 65), TEXT = new Color(225, 237, 244);
    static final Color MUTED = new Color(127, 150, 169), CYAN = new Color(73, 221, 207);
    static final Color BLUE = new Color(91, 168, 255), GOLD = new Color(250, 188, 92);
    static final Color PURPLE = new Color(182, 150, 255);
    static final Color[] SIGNALS = {CYAN, BLUE, GOLD, PURPLE};
    static final String[] CLASSES = {"QUIET", "COMPUTE", "NETWORK", "MEMORY"};
    static final Font MONO = new Font("Consolas", Font.PLAIN, 12);
    static final Path MODEL_FILE = Paths.get(System.getProperty("bus.dataDir", "data"), "activity-model.bin");

    private final ConsolePanel console;

    public LocalInferenceBusEngine() {
        super("Local Inference Bus | Neural Activity Console");
        console = new ConsolePanel(true);
        setContentPane(console);
        setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        setMinimumSize(new Dimension(960, 820));
        setSize(1280, 900);
        setLocationRelativeTo(null);
        addWindowListener(new WindowAdapter() {
            @Override public void windowClosed(WindowEvent e) { console.close(); }
        });
    }

    static Font font(int style, int size) { return new Font("Segoe UI", style, size); }
    static Color alpha(Color c, int a) { return new Color(c.getRed(), c.getGreen(), c.getBlue(), Math.max(0, Math.min(255, a))); }
    static double clamp(double x) { return Math.max(0, Math.min(1, x)); }
    static String pct(double x) { return x < 0 ? "--" : String.format(Locale.ROOT, "%.0f%%", x * 100); }
    static String rate(double b) {
        if (b < 0) return "--";
        return b >= 1048576 ? String.format(Locale.ROOT, "%.1f MB/s", b / 1048576)
                : String.format(Locale.ROOT, "%.1f KB/s", b / 1024);
    }
    static double networkInput(double bytesPerSecond) {
        return clamp(Math.log1p(Math.max(0, bytesPerSecond) / 1024) / Math.log1p(1024));
    }

    static final class Prediction {
        final double[] input, hidden, output;
        final int winner;
        Prediction(double[] input, double[] hidden, double[] output) {
            this.input = input; this.hidden = hidden; this.output = output;
            int best = 0;
            for (int i = 1; i < output.length; i++) if (output[i] > output[best]) best = i;
            winner = best;
        }
    }

    /** Small feed-forward MLP. Only the trainer mutates weights; published models are immutable. */
    static final class NeuralModel {
        static final int INPUTS = 3, HIDDEN = 10, OUTPUTS = 4, MAGIC = 0x4C494232;
        final double[][] w1 = new double[HIDDEN][INPUTS], w2 = new double[OUTPUTS][HIDDEN];
        final double[] b1 = new double[HIDDEN], b2 = new double[OUTPUTS];
        double validationAccuracy;

        Prediction infer(double... input) {
            if (input.length != INPUTS) throw new IllegalArgumentException("Expected CPU, memory, network (three values).");
            for (double v : input) if (!Double.isFinite(v) || v < 0 || v > 1)
                throw new IllegalArgumentException("Inference values must be between 0 and 1.");
            double[] h = new double[HIDDEN], out = new double[OUTPUTS];
            for (int j = 0; j < HIDDEN; j++) {
                double sum = b1[j];
                for (int i = 0; i < INPUTS; i++) sum += w1[j][i] * input[i];
                h[j] = Math.tanh(sum);
            }
            double max = -Double.MAX_VALUE, total = 0;
            for (int k = 0; k < OUTPUTS; k++) {
                out[k] = b2[k];
                for (int j = 0; j < HIDDEN; j++) out[k] += w2[k][j] * h[j];
                max = Math.max(max, out[k]);
            }
            for (int k = 0; k < OUTPUTS; k++) { out[k] = Math.exp(out[k] - max); total += out[k]; }
            for (int k = 0; k < OUTPUTS; k++) out[k] /= total;
            return new Prediction(input.clone(), h, out);
        }

        // Synthetic labels describe dominant activity, not faults or physical hardware inference.
        static int label(double[] x) {
            double[] score = {.28, x[0], x[2], Math.max(0, (x[1] - .60) * 2)};
            int best = 0;
            for (int i = 1; i < score.length; i++) if (score[i] > score[best]) best = i;
            return best;
        }
        static double[] sample(Random r) {
            boolean low = r.nextDouble() < .4;
            return new double[]{r.nextDouble() * (low ? .3 : 1), r.nextDouble(), r.nextDouble() * (low ? .3 : 1)};
        }
        static NeuralModel train(long seed) throws InterruptedException {
            Random r = new Random(seed);
            NeuralModel m = new NeuralModel();
            for (double[] row : m.w1) for (int i = 0; i < row.length; i++) row[i] = r.nextGaussian() * .4;
            for (double[] row : m.w2) for (int i = 0; i < row.length; i++) row[i] = r.nextGaussian() * .3;
            for (int step = 0; step < 120000; step++) {
                if ((step & 1023) == 0 && Thread.currentThread().isInterrupted()) throw new InterruptedException();
                double[] x = sample(r);
                Prediction p = m.infer(x);
                double[] error = p.output.clone(), hiddenError = new double[HIDDEN];
                error[label(x)] -= 1;
                for (int j = 0; j < HIDDEN; j++) {
                    for (int k = 0; k < OUTPUTS; k++) hiddenError[j] += error[k] * m.w2[k][j];
                    hiddenError[j] *= (1 - p.hidden[j] * p.hidden[j]);
                }
                double lr = .035 * (1 - .8 * step / 120000.0);
                for (int k = 0; k < OUTPUTS; k++) {
                    m.b2[k] -= lr * error[k];
                    for (int j = 0; j < HIDDEN; j++) m.w2[k][j] -= lr * error[k] * p.hidden[j];
                }
                for (int j = 0; j < HIDDEN; j++) {
                    m.b1[j] -= lr * hiddenError[j];
                    for (int i = 0; i < INPUTS; i++) m.w1[j][i] -= lr * hiddenError[j] * x[i];
                }
            }
            int correct = 0;
            Random validation = new Random(83017);
            for (int i = 0; i < 4000; i++) { double[] x = sample(validation); if (m.infer(x).winner == label(x)) correct++; }
            m.validationAccuracy = correct / 4000.0;
            return m;
        }
        void save(Path path) throws IOException {
            Path absolute = path.toAbsolutePath();
            Files.createDirectories(absolute.getParent());
            Path temp = Files.createTempFile(absolute.getParent(), "activity-model-", ".tmp");
            try {
                try (DataOutputStream out = new DataOutputStream(Files.newOutputStream(temp))) {
                    out.writeInt(MAGIC); out.writeDouble(validationAccuracy);
                    for (double[] row : w1) for (double v : row) out.writeDouble(v);
                    for (double v : b1) out.writeDouble(v);
                    for (double[] row : w2) for (double v : row) out.writeDouble(v);
                    for (double v : b2) out.writeDouble(v);
                }
                try { Files.move(temp, absolute, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
                catch (AtomicMoveNotSupportedException e) { Files.move(temp, absolute, StandardCopyOption.REPLACE_EXISTING); }
            } finally { Files.deleteIfExists(temp); }
        }
        static double readFinite(DataInputStream in) throws IOException {
            double v = in.readDouble();
            if (!Double.isFinite(v) || Math.abs(v) > 10000) throw new IOException("Invalid model weight.");
            return v;
        }
        static NeuralModel load(Path path) throws IOException {
            try (DataInputStream in = new DataInputStream(Files.newInputStream(path))) {
                if (in.readInt() != MAGIC) throw new IOException("Unsupported model format.");
                NeuralModel m = new NeuralModel(); m.validationAccuracy = readFinite(in);
                if (m.validationAccuracy < 0 || m.validationAccuracy > 1) throw new IOException("Invalid model metadata.");
                for (double[] row : m.w1) for (int i = 0; i < row.length; i++) row[i] = readFinite(in);
                for (int i = 0; i < HIDDEN; i++) m.b1[i] = readFinite(in);
                for (double[] row : m.w2) for (int i = 0; i < row.length; i++) row[i] = readFinite(in);
                for (int i = 0; i < OUTPUTS; i++) m.b2[i] = readFinite(in);
                if (in.read() != -1) throw new IOException("Unexpected model data.");
                return m;
            }
        }
    }

    static final class Telemetry {
        final double cpu, memory, processCpu, rx, tx;
        final long usedMemory, totalMemory, sampledAt;
        Telemetry(double cpu, double memory, double processCpu, double rx, double tx, long used, long total) {
            this.cpu = cpu; this.memory = memory; this.processCpu = processCpu;
            this.rx = rx; this.tx = tx; usedMemory = used; totalMemory = total;
            sampledAt = System.nanoTime();
        }
        static Telemetry empty() { return new Telemetry(-1, -1, -1, -1, -1, 0, 0); }
        boolean complete() { return cpu >= 0 && memory >= 0 && rx >= 0 && tx >= 0; }
    }

    /** Counter collection runs away from the Swing event thread and has a bounded subprocess lifetime. */
    static final class Sampler implements AutoCloseable {
        final ScheduledExecutorService workers = Executors.newScheduledThreadPool(2, daemonFactory("bus-sampler"));
        final java.lang.management.OperatingSystemMXBean base = ManagementFactory.getOperatingSystemMXBean();
        final com.sun.management.OperatingSystemMXBean os = base instanceof com.sun.management.OperatingSystemMXBean
                ? (com.sun.management.OperatingSystemMXBean) base : null;
        volatile Telemetry latest = Telemetry.empty();
        volatile double rx = -1, tx = -1;
        volatile long networkTime;
        volatile Process counterProcess;
        volatile boolean closed;
        long previousRx = -1, previousTx, previousTime, previousProcessNanos = -1, previousSystemTime;

        void start() {
            workers.scheduleWithFixedDelay(this::sampleSystem, 0, 1, TimeUnit.SECONDS);
            workers.scheduleWithFixedDelay(this::sampleNetwork, 0, 3, TimeUnit.SECONDS);
        }
        void sampleSystem() {
            try {
                long total = os == null ? 0 : os.getTotalMemorySize();
                long used = os == null ? 0 : total - os.getFreeMemorySize();
                boolean fresh = networkTime > 0 && System.nanoTime() - networkTime < TimeUnit.SECONDS.toNanos(15);
                double processLoad = os == null ? -1 : os.getProcessCpuLoad();
                long processNanos = os == null ? -1 : os.getProcessCpuTime(), now = System.nanoTime();
                if (processLoad < 0 && processNanos >= previousProcessNanos && previousProcessNanos >= 0 && now > previousSystemTime)
                    processLoad = clamp((double) (processNanos - previousProcessNanos) / (now - previousSystemTime) / base.getAvailableProcessors());
                previousProcessNanos = processNanos; previousSystemTime = now;
                latest = new Telemetry(os == null ? -1 : os.getCpuLoad(), total > 0 ? (double) used / total : -1,
                        processLoad, fresh ? rx : -1, fresh ? tx : -1, used, total);
            } catch (RuntimeException ex) { latest = Telemetry.empty(); }
        }
        synchronized void acceptCounters(long received, long sent, long now) {
            if (received < 0 || sent < 0) throw new IllegalArgumentException("Negative network counter.");
            if (previousRx >= 0 && now > previousTime && received >= previousRx && sent >= previousTx) {
                double seconds = (now - previousTime) / 1e9;
                rx = (received - previousRx) / seconds;
                tx = (sent - previousTx) / seconds;
            } else { rx = -1; tx = -1; }
            previousRx = received; previousTx = sent; previousTime = now; networkTime = now;
        }
        void sampleNetwork() {
            try {
                if (closed) return;
                long received = 0, sent = 0;
                if (System.getProperty("os.name").toLowerCase(Locale.ROOT).contains("win")) {
                    String root = System.getenv("SystemRoot");
                    String exe = Paths.get(root == null ? "C:\\Windows" : root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe").toString();
                    String script = "$ErrorActionPreference='Stop'; $s=Get-NetAdapterStatistics; if (!$s) {exit 2}; "
                            + "[long]$r=0; [long]$t=0; foreach($a in $s){$r+=$a.ReceivedBytes; $t+=$a.SentBytes}; Write-Output \"$r $t\"";
                    Process p = new ProcessBuilder(exe, "-NoProfile", "-NonInteractive", "-Command", script)
                            .redirectError(ProcessBuilder.Redirect.DISCARD).start();
                    counterProcess = p;
                    if (closed) { p.destroyForcibly(); return; }
                    if (!p.waitFor(8, TimeUnit.SECONDS)) { p.destroyForcibly(); throw new IOException("Network counter timeout."); }
                    if (p.exitValue() != 0) throw new IOException("Network counters unavailable.");
                    String[] parts = new String(p.getInputStream().readAllBytes(), java.nio.charset.StandardCharsets.UTF_8).trim().split("\\s+");
                    if (parts.length != 2) throw new IOException("Invalid network counters.");
                    received = Long.parseLong(parts[0]); sent = Long.parseLong(parts[1]);
                } else if (Files.isReadable(Paths.get("/proc/net/dev"))) {
                    for (String line : Files.readAllLines(Paths.get("/proc/net/dev"))) {
                        int colon = line.indexOf(':');
                        if (colon < 0 || line.substring(0, colon).trim().equals("lo")) continue;
                        String[] parts = line.substring(colon + 1).trim().split("\\s+");
                        received += Long.parseLong(parts[0]); sent += Long.parseLong(parts[8]);
                    }
                } else { rx = -1; tx = -1; return; }
                acceptCounters(received, sent, System.nanoTime());
            } catch (Exception ex) {
                rx = -1; tx = -1; previousRx = -1;
                if (ex instanceof InterruptedException) Thread.currentThread().interrupt();
            } finally {
                Process p = counterProcess;
                if (p != null && p.isAlive()) p.destroyForcibly();
                counterProcess = null;
            }
        }
        @Override public void close() {
            closed = true; workers.shutdownNow();
            Process p = counterProcess; if (p != null) p.destroyForcibly();
        }
    }

    static ThreadFactory daemonFactory(String name) {
        return r -> { Thread t = new Thread(r, name); t.setDaemon(true); return t; };
    }

    static final class ActivityMotion {
        static double target(Telemetry t, Prediction p, double mix, double random, double pulse) {
            double live = Math.max(0, t.cpu) * .5 + networkInput(t.rx + t.tx) * .3
                    + Math.max(0, t.memory - .6) * .25 + (p == null ? 0 : (1 - p.output[0]) * .15);
            return clamp(mix * clamp(live) + (1 - mix) * random + pulse * .3);
        }
    }

    static final class ConsolePanel extends JPanel implements AutoCloseable {
        final Sampler sampler = new Sampler();
        final ExecutorService trainer = Executors.newSingleThreadExecutor(daemonFactory("bus-model"));
        final JLabel modelStatus = new JLabel("INITIALIZING"), clock = new JLabel();
        final JTextArea log = new JTextArea();
        final JTextField command = new JTextField() {
            @Override protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                if (getText().isEmpty()) {
                    Graphics2D q = (Graphics2D) g.create(); quality(q); q.setFont(getFont()); q.setColor(MUTED);
                    q.drawString("Enter a command... try help", 2, (getHeight() - q.getFontMetrics().getHeight()) / 2 + q.getFontMetrics().getAscent()); q.dispose();
                }
            }
        };
        final JButton pauseButton = button("Pause motion"), netButton = button("Net active");
        final JSlider blend = new JSlider(0, 100, 75);
        final JLabel blendLabel = new JLabel("75% SYSTEM / 25% RANDOM");
        final List<String> history = new ArrayList<>();
        final MetricCard cpuCard = new MetricCard("SYSTEM CPU", BLUE), memCard = new MetricCard("PHYSICAL MEMORY", PURPLE);
        final MetricCard ioCard = new MetricCard("NETWORK TRAFFIC", GOLD), modelCard = new MetricCard("NEURAL OUTPUT", CYAN);
        final BusCanvas canvas;
        final AtomCanvas atomCanvas;
        final CardLayout viewLayout = new CardLayout();
        final JPanel views = new JPanel(viewLayout);
        final JToggleButton atomView = new JToggleButton("Hydrogen / silicon", true), neuralView = new JToggleButton("Neural network");
        final javax.swing.Timer timer;
        NeuralModel model;
        Prediction prediction;
        Telemetry telemetry = Telemetry.empty();
        boolean netActive = true, paused, training, closed;
        double mix = .75, speed = 1, activity, pulse, inferenceMicros;
        long lastTick = System.nanoTime(), lastSample, inferences;
        int historyIndex;
        String historyDraft = "";
        final Random random = new Random();
        double randomTarget = .2, randomTime;

        ConsolePanel(boolean start) {
            setLayout(new BorderLayout(0, 16)); setBorder(new EmptyBorder(22, 26, 20, 26)); setBackground(BG);
            add(header(), BorderLayout.NORTH);
            JPanel body = new JPanel(new BorderLayout(0, 16)); body.setOpaque(false);
            JPanel metrics = new JPanel(new GridLayout(1, 4, 12, 0)); metrics.setOpaque(false);
            for (MetricCard card : new MetricCard[]{cpuCard, memCard, ioCard, modelCard}) metrics.add(card);
            metrics.setPreferredSize(new Dimension(100, 104)); body.add(metrics, BorderLayout.NORTH);
            canvas = new BusCanvas(this); atomCanvas = new AtomCanvas(this);
            JPanel visual = new JPanel(new BorderLayout(0, 8)); visual.setOpaque(false);
            JPanel modes = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0)); modes.setOpaque(false);
            ButtonGroup group = new ButtonGroup();
            for (JToggleButton b : new JToggleButton[]{atomView, neuralView}) {
                group.add(b); b.setFont(font(Font.BOLD, 11)); b.setForeground(TEXT); b.setBackground(PANEL);
                b.setContentAreaFilled(false); b.setOpaque(true);
                b.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(LINE), new EmptyBorder(5, 12, 5, 12)));
                modes.add(b);
            }
            atomView.addActionListener(e -> showView("atom")); neuralView.addActionListener(e -> showView("neural"));
            views.setOpaque(false); views.add(atomCanvas, "atom"); views.add(canvas, "neural");
            visual.add(modes, BorderLayout.NORTH); visual.add(views, BorderLayout.CENTER); body.add(visual, BorderLayout.CENTER);
            showView("atom");
            body.add(console(), BorderLayout.SOUTH); add(body, BorderLayout.CENTER);
            timer = new javax.swing.Timer(25, e -> tick()); timer.setCoalesce(true);
            bindHistory();
            getInputMap(WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_L, InputEvent.CTRL_DOWN_MASK), "focus-command");
            getActionMap().put("focus-command", new AbstractAction() { public void actionPerformed(ActionEvent e) { command.requestFocusInWindow(); } });
            append("Ready. Type help for commands. Ctrl+L focuses the console; Up/Down recalls commands.");
            append("Live sensors + a local 3-10-4 neural model. Training uses synthetic activity examples.");
            if (start) { sampler.start(); trainModel(false); timer.start(); }
            updateCards();
        }

        JPanel header() {
            JPanel panel = new JPanel(new BorderLayout()); panel.setOpaque(false);
            JPanel title = new JPanel(new GridLayout(2, 1, 0, 2)); title.setOpaque(false);
            JLabel heading = new JLabel("LOCAL INFERENCE BUS"); heading.setFont(font(Font.BOLD, 25)); heading.setForeground(TEXT);
            JLabel sub = new JLabel("NEURAL ACTIVITY CONSOLE    /    LOCAL ENGINE 02"); sub.setFont(MONO); sub.setForeground(MUTED);
            title.add(heading); title.add(sub); panel.add(title, BorderLayout.WEST);
            JPanel status = new JPanel(new GridLayout(2, 1, 0, 4)); status.setOpaque(false);
            modelStatus.setHorizontalAlignment(SwingConstants.RIGHT); modelStatus.setFont(font(Font.BOLD, 12)); modelStatus.setForeground(CYAN);
            clock.setHorizontalAlignment(SwingConstants.RIGHT); clock.setFont(MONO); clock.setForeground(MUTED);
            status.add(modelStatus); status.add(clock); panel.add(status, BorderLayout.EAST); return panel;
        }

        JPanel console() {
            JPanel panel = new JPanel(new BorderLayout(0, 10)); panel.setOpaque(false);
            JPanel controls = new JPanel(new BorderLayout(12, 0)); controls.setOpaque(false);
            JPanel actions = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0)); actions.setOpaque(false);
            pauseButton.addActionListener(e -> execute(paused ? "resume" : "pause"));
            netButton.addActionListener(e -> execute(netActive ? "net off" : "net on"));
            JButton retrain = button("Retrain"); retrain.addActionListener(e -> execute("train"));
            actions.add(pauseButton); actions.add(netButton); actions.add(retrain); controls.add(actions, BorderLayout.WEST);
            JPanel blending = new JPanel(new BorderLayout(10, 0)); blending.setOpaque(false);
            blendLabel.setFont(MONO.deriveFont(10f)); blendLabel.setForeground(MUTED);
            blend.setOpaque(false); blend.setPreferredSize(new Dimension(145, 26));
            blend.setToolTipText("How strongly real system activity drives the animation");
            blend.getAccessibleContext().setAccessibleName("System activity contribution percent");
            blend.addChangeListener(e -> { mix = blend.getValue() / 100.0; blendLabel.setText(blend.getValue() + "% SYSTEM / " + (100 - blend.getValue()) + "% RANDOM"); });
            blending.add(blendLabel, BorderLayout.WEST); blending.add(blend, BorderLayout.CENTER); controls.add(blending, BorderLayout.EAST);
            panel.add(controls, BorderLayout.NORTH);
            log.setEditable(false); log.setRows(4); log.setLineWrap(true); log.setWrapStyleWord(true);
            log.setFont(MONO); log.setBackground(PANEL); log.setForeground(MUTED); log.setBorder(new EmptyBorder(9, 12, 9, 12));
            log.getAccessibleContext().setAccessibleName("Command output");
            JScrollPane scroll = new JScrollPane(log); scroll.setBorder(BorderFactory.createLineBorder(LINE)); scroll.setPreferredSize(new Dimension(100, 100));
            panel.add(scroll, BorderLayout.CENTER);
            JPanel input = new JPanel(new BorderLayout(12, 0)); input.setBackground(PANEL);
            input.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(new Color(51, 99, 106)), new EmptyBorder(8, 14, 8, 8)));
            JLabel prompt = new JLabel(">"); prompt.setForeground(CYAN); prompt.setFont(MONO.deriveFont(Font.BOLD, 19f)); input.add(prompt, BorderLayout.WEST);
            command.setFont(MONO.deriveFont(14f)); command.setForeground(TEXT); command.setBackground(PANEL); command.setCaretColor(CYAN); command.setBorder(null);
            command.setToolTipText("Try help, status, infer 0.8 0.4 0.1, mix 75, or train");
            command.getAccessibleContext().setAccessibleName("Engine command input"); command.addActionListener(e -> submit());
            input.add(command, BorderLayout.CENTER);
            JButton run = button("Run  /  Enter"); run.addActionListener(e -> submit()); input.add(run, BorderLayout.EAST);
            panel.add(input, BorderLayout.SOUTH); return panel;
        }
        static JButton button(String label) {
            JButton b = new JButton(label); b.setFont(font(Font.BOLD, 12)); b.setForeground(TEXT); b.setBackground(new Color(24, 39, 54));
            b.setFocusPainted(true); b.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(LINE), new EmptyBorder(7, 12, 7, 12)));
            b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)); return b;
        }
        void bindHistory() {
            for (int direction : new int[]{-1, 1}) {
                String key = direction < 0 ? "history-up" : "history-down";
                command.getInputMap().put(KeyStroke.getKeyStroke(direction < 0 ? KeyEvent.VK_UP : KeyEvent.VK_DOWN, 0), key);
                command.getActionMap().put(key, new AbstractAction() {
                    public void actionPerformed(ActionEvent e) {
                        if (history.isEmpty()) return;
                        if (historyIndex == history.size()) historyDraft = command.getText();
                        historyIndex = Math.max(0, Math.min(history.size(), historyIndex + direction));
                        command.setText(historyIndex == history.size() ? historyDraft : history.get(historyIndex));
                    }
                });
            }
        }
        void submit() { String line = command.getText().trim(); if (line.isEmpty()) return; command.setText(""); execute(line); command.requestFocusInWindow(); }
        void append(String text) {
            if (closed) return;
            log.append(LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")) + "  " + text + "\n");
            if (log.getDocument().getLength() > 24000) {
                try { log.getDocument().remove(0, log.getDocument().getLength() - 18000); } catch (javax.swing.text.BadLocationException ignored) { }
            }
            log.setCaretPosition(log.getDocument().getLength());
        }
        static double number(String s, double min, double max) {
            double v;
            try { v = Double.parseDouble(s); } catch (NumberFormatException ex) { throw new IllegalArgumentException("Enter a number from " + min + " to " + max + "."); }
            if (!Double.isFinite(v) || v < min || v > max) throw new IllegalArgumentException("Enter a number from " + min + " to " + max + ".");
            return v;
        }
        static void arity(String[] p, int count, String usage) { if (p.length != count) throw new IllegalArgumentException("Usage: " + usage); }
        void execute(String line) {
            line = line.trim(); if (line.isEmpty()) return;
            if (line.length() > 300) { append("Command too long (maximum 300 characters)."); return; }
            if (history.isEmpty() || !history.get(history.size() - 1).equals(line)) history.add(line);
            if (history.size() > 100) history.remove(0);
            historyIndex = history.size(); historyDraft = ""; pulse = 1; append("> " + line);
            String[] p = line.toLowerCase(Locale.ROOT).split("\\s+");
            try {
                switch (p[0]) {
                    case "help":
                        arity(p, 1, "help");
                        append("status | pause | resume | net on/off/status | train | save | clear");
                        append("view atom/neural | mix 0..100 (system %) | speed 0.2..3 | pulse | infer <cpu> <memory> <network>");
                        append("infer values are 0..1. Example: infer 0.85 0.40 0.05. Samples do not replace live telemetry.");
                        break;
                    case "status":
                        arity(p, 1, "status");
                        append("CPU " + pct(telemetry.cpu) + " | RAM " + pct(telemetry.memory) + " | RX " + rate(telemetry.rx) + " | TX " + rate(telemetry.tx));
                        append("Neural net " + (netActive ? "enabled" : "disabled") + " | " + inferences + " live inferences | " + (paused ? "motion paused" : "motion running"));
                        if (model != null) append("Synthetic holdout accuracy " + pct(model.validationAccuracy) + "; this describes activity patterns, not hardware health.");
                        break;
                    case "pause": arity(p, 1, "pause"); paused = true; append("Motion paused. Telemetry and neural inference continue."); break;
                    case "resume": arity(p, 1, "resume"); paused = false; append("Motion resumed."); break;
                    case "net":
                        arity(p, 2, "net on | net off | net status");
                        if (p[1].equals("on")) { netActive = true; lastSample = 0; append("Neural inference enabled."); }
                        else if (p[1].equals("off")) { netActive = false; prediction = null; append("Neural inference disabled; live sensors continue."); }
                        else if (p[1].equals("status")) append("Neural net " + (netActive ? "enabled" : "disabled") + "; " + (model == null ? "no model ready" : "3 inputs / 10 hidden neurons / 4 outputs / 84 parameters"));
                        else throw new IllegalArgumentException("Usage: net on | net off | net status");
                        break;
                    case "mix": arity(p, 2, "mix 0..100"); blend.setValue((int) Math.round(number(p[1], 0, 100))); append(blendLabel.getText()); break;
                    case "speed": arity(p, 2, "speed 0.2..3"); speed = number(p[1], .2, 3); append("Motion speed " + speed + "x."); break;
                    case "pulse": arity(p, 1, "pulse"); pulse = 2; append("Visual pulse injected."); break;
                    case "view":
                        arity(p, 2, "view atom | view neural");
                        if (!p[1].equals("atom") && !p[1].equals("neural")) throw new IllegalArgumentException("Usage: view atom | view neural");
                        showView(p[1]); append(p[1].equals("atom") ? "Hydrogen probability cloud / silicon chip view." : "Live neural activation graph."); break;
                    case "infer":
                        arity(p, 4, "infer <cpu 0..1> <memory 0..1> <network 0..1>");
                        if (model == null || !netActive) throw new IllegalArgumentException("Enable the neural net and wait for the model to be ready.");
                        Prediction result = model.infer(number(p[1], 0, 1), number(p[2], 0, 1), number(p[3], 0, 1));
                        append("Sample result: " + CLASSES[result.winner] + " (" + pct(result.output[result.winner]) + "). " + probabilities(result));
                        break;
                    case "train": arity(p, 1, "train"); trainModel(true); break;
                    case "save":
                        arity(p, 1, "save"); if (model == null) throw new IllegalArgumentException("No model ready to save.");
                        NeuralModel current = model;
                        trainer.submit(() -> { try { current.save(MODEL_FILE); onUi(() -> append("Model saved.")); } catch (IOException ex) { onUi(() -> append("Save failed: " + ex.getMessage())); } });
                        break;
                    case "clear": arity(p, 1, "clear"); log.setText(""); break;
                    default: throw new IllegalArgumentException("Unknown command. Type help for available engine commands.");
                }
            } catch (IllegalArgumentException ex) { append(ex.getMessage()); }
            pauseButton.setText(paused ? "Resume motion" : "Pause motion");
            netButton.setText(netActive ? "Net active" : "Net off"); updateCards(); views.repaint();
        }
        void showView(String name) {
            viewLayout.show(views, name); atomView.setSelected(name.equals("atom")); neuralView.setSelected(name.equals("neural"));
            atomView.setForeground(atomView.isSelected() ? CYAN : MUTED); neuralView.setForeground(neuralView.isSelected() ? CYAN : MUTED);
            atomView.setBackground(atomView.isSelected() ? new Color(22, 53, 61) : PANEL);
            neuralView.setBackground(neuralView.isSelected() ? new Color(22, 53, 61) : PANEL);
        }
        static String probabilities(Prediction p) {
            StringBuilder s = new StringBuilder();
            for (int i = 0; i < CLASSES.length; i++) s.append(CLASSES[i]).append(' ').append(pct(p.output[i])).append("  ");
            return s.toString().trim();
        }
        void onUi(Runnable r) { SwingUtilities.invokeLater(() -> { if (!closed) r.run(); }); }
        void trainModel(boolean force) {
            if (training) { append("Training is already running."); return; }
            training = true;
            append(force ? "Training a fresh activity model in the background..." : "Loading saved weights, or training on first launch...");
            trainer.submit(() -> {
                try {
                    NeuralModel next = null;
                    if (!force && Files.exists(MODEL_FILE)) {
                        try { next = NeuralModel.load(MODEL_FILE); }
                        catch (IOException ex) { onUi(() -> append("Saved model unreadable; training a replacement.")); }
                    }
                    boolean trained = next == null;
                    if (trained) next = NeuralModel.train(783L);
                    NeuralModel ready = next;
                    if (trained) try { ready.save(MODEL_FILE); }
                    catch (IOException ex) { onUi(() -> append("Model is active in memory; could not save: " + ex.getMessage())); }
                    onUi(() -> { model = ready; training = false; lastSample = 0;
                        append("Model ready. Synthetic holdout accuracy: " + pct(ready.validationAccuracy) + ". Live inference starts with the next sensor sample."); updateCards(); });
                } catch (InterruptedException ex) { Thread.currentThread().interrupt(); }
                catch (RuntimeException ex) { onUi(() -> { training = false; append("Training failed: " + ex.getMessage()); updateCards(); }); }
            });
        }
        void tick() {
            long now = System.nanoTime(); double dt = Math.min(.1, (now - lastTick) / 1e9); lastTick = now;
            telemetry = sampler.latest;
            if (lastSample != telemetry.sampledAt) {
                lastSample = telemetry.sampledAt;
                if (netActive && model != null && (telemetry.cpu >= 0 || telemetry.memory >= 0 || telemetry.rx >= 0)) {
                    long began = System.nanoTime();
                    prediction = model.infer(clamp(telemetry.cpu), clamp(telemetry.memory), networkInput(telemetry.rx + telemetry.tx));
                    inferenceMicros = (System.nanoTime() - began) / 1000.0; inferences++;
                } else prediction = null;
                canvas.addHistory(telemetry); updateCards();
            }
            if (!paused) {
                randomTime += dt;
                if (randomTime >= .7) { randomTime = 0; randomTarget = .12 + random.nextDouble() * .75; }
                double target = ActivityMotion.target(telemetry, prediction, mix, randomTarget, pulse);
                activity += (target - activity) * (1 - Math.exp(-dt * 3));
                pulse = Math.max(0, pulse - dt * 1.5); canvas.advance(dt);
            }
            clock.setText(LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")) + "  /  " + (paused ? "MOTION PAUSED" : "LIVE SENSORS"));
            views.repaint();
        }
        void updateCards() {
            cpuCard.set(pct(telemetry.cpu), "Engine " + pct(telemetry.processCpu) + "  /  " + Runtime.getRuntime().availableProcessors() + " logical cores", Math.max(0, telemetry.cpu));
            memCard.set(pct(telemetry.memory), telemetry.totalMemory > 0 ? String.format(Locale.ROOT, "%.1f / %.1f GB in use", telemetry.usedMemory / 1073741824.0, telemetry.totalMemory / 1073741824.0) : "Waiting for system sample", Math.max(0, telemetry.memory));
            ioCard.set(rate(telemetry.rx + telemetry.tx < 0 ? -1 : telemetry.rx + telemetry.tx), telemetry.rx < 0 ? "Counters warming up / unavailable" : "RX " + rate(telemetry.rx) + "  TX " + rate(telemetry.tx), networkInput(telemetry.rx + telemetry.tx));
            modelCard.set(prediction == null ? (netActive ? "WARMING UP" : "OFF") : CLASSES[prediction.winner], prediction == null ? "3 inputs / 10 hidden / 4 outputs" : pct(prediction.output[prediction.winner]) + " confidence" + (telemetry.complete() ? "  /  live" : "  /  partial sensors"), prediction == null ? 0 : prediction.output[prediction.winner]);
            modelStatus.setText(!netActive ? "NEURAL NET DISABLED" : training ? "NEURAL NET TRAINING" : model == null ? "MODEL UNAVAILABLE" : "NEURAL NET ACTIVE  /  " + (telemetry.complete() ? "LOCAL" : "PARTIAL SENSORS"));
            modelStatus.setForeground(netActive && model != null ? CYAN : GOLD);
        }
        @Override public void close() { closed = true; timer.stop(); sampler.close(); trainer.shutdownNow(); }
    }

    static final class MetricCard extends JPanel {
        final String title; final Color accent;
        String value = "--", detail = "Waiting for sample"; double level;
        MetricCard(String title, Color accent) { this.title = title; this.accent = accent; setOpaque(false); }
        void set(String value, String detail, double level) { this.value = value; this.detail = detail; this.level = clamp(level); repaint(); }
        @Override protected void paintComponent(Graphics g) {
            super.paintComponent(g); Graphics2D q = (Graphics2D) g.create(); quality(q);
            int w = getWidth(), h = getHeight();
            q.setColor(PANEL); q.fillRoundRect(0, 0, w - 1, h - 1, 14, 14); q.setColor(LINE); q.drawRoundRect(0, 0, w - 1, h - 1, 14, 14);
            q.setFont(MONO.deriveFont(10f)); q.setColor(MUTED); q.drawString(title, 16, 23);
            q.setFont(font(Font.BOLD, value.length() > 9 ? 21 : 27)); q.setColor(TEXT); q.drawString(value, 16, 55);
            q.setFont(font(Font.PLAIN, 11)); q.setColor(MUTED); q.drawString(detail, 16, 77);
            q.setColor(alpha(accent, 35)); q.fillRoundRect(16, h - 13, w - 32, 3, 3, 3);
            q.setColor(accent); q.fillRoundRect(16, h - 13, (int) ((w - 32) * level), 3, 3, 3); q.dispose();
        }
    }
    static void quality(Graphics2D g) {
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
    }

    static final class Particle {
        double progress, lane, offset, pace; int kind;
        Particle(Random r) { progress = r.nextDouble(); lane = r.nextDouble(); offset = r.nextDouble() * Math.PI * 2; pace = .7 + r.nextDouble() * .6; kind = r.nextInt(3); }
    }
    static final class BusCanvas extends JPanel {
        final ConsolePanel owner;
        final List<Particle> particles = new ArrayList<>();
        final double[] cpuHistory = new double[90], netHistory = new double[90];
        int historyCount, historyCursor;
        double phase;
        BusCanvas(ConsolePanel owner) {
            this.owner = owner; setOpaque(false); setPreferredSize(new Dimension(1100, 390));
            Arrays.fill(cpuHistory, -1); Arrays.fill(netHistory, -1);
            Random r = new Random(97); for (int i = 0; i < 90; i++) particles.add(new Particle(r));
            getAccessibleContext().setAccessibleName("Live neural activation graph and system activity history");
            setToolTipText("Connections show learned weights; neuron brightness shows current activation. Lower bus motion blends real activity and random motion.");
        }
        void addHistory(Telemetry t) {
            cpuHistory[historyCursor] = t.cpu;
            netHistory[historyCursor] = t.rx < 0 ? -1 : networkInput(t.rx + t.tx);
            historyCursor = (historyCursor + 1) % 90; historyCount = Math.min(90, historyCount + 1);
        }
        void advance(double dt) {
            phase += dt * owner.speed * (.35 + owner.activity * 2.2);
            for (Particle p : particles) p.progress = (p.progress + dt * owner.speed * (.045 + owner.activity * .24) * p.pace) % 1;
        }
        @Override protected void paintComponent(Graphics g) {
            super.paintComponent(g); Graphics2D q = (Graphics2D) g.create(); quality(q);
            int w = getWidth(), h = getHeight();
            q.setPaint(new GradientPaint(0, 0, new Color(15, 26, 40), w, h, new Color(9, 18, 29)));
            q.fillRoundRect(0, 0, w - 1, h - 1, 18, 18); q.setColor(LINE); q.drawRoundRect(0, 0, w - 1, h - 1, 18, 18);
            q.clip(new RoundRectangle2D.Double(1, 1, w - 2, h - 2, 18, 18));
            for (int x = 25; x < w; x += 28) for (int y = 65; y < h - 100; y += 28) { q.setColor(new Color(47, 68, 85, 55)); q.fillRect(x, y, 1, 1); }
            q.setFont(font(Font.BOLD, 13)); q.setColor(TEXT); q.drawString("LIVE INFERENCE FABRIC", 24, 29);
            q.setFont(MONO.deriveFont(10f)); q.setColor(MUTED); q.drawString("SENSORS  >  LEARNED WEIGHTS  >  ACTIVITY", 24, 48);
            String summary = owner.prediction == null ? "WAITING FOR INFERENCE" : String.format(Locale.ROOT, "%s  /  %.0f us  /  %,d PASSES", owner.telemetry.complete() ? "LIVE" : "PARTIAL INPUT", owner.inferenceMicros, owner.inferences);
            q.setColor(CYAN); right(q, summary, w - 24, 30);
            drawNetwork(q, w, h);
            if (h >= 360) { drawBus(q, w, h); drawHistory(q, w, h); }
            q.dispose();
        }
        void drawNetwork(Graphics2D q, int w, int h) {
            boolean compact = h < 360;
            double top = h < 270 ? 84 : 94, bottom = h - (compact ? 35 : 175);
            double left = w * .22, middle = w * .50, rightX = w * .76;
            Prediction p = owner.netActive ? owner.prediction : null;
            double[] input = p == null ? new double[]{0, 0, 0} : p.input;
            double[] hidden = p == null ? new double[10] : p.hidden;
            double[] out = p == null ? new double[4] : p.output;
            NeuralModel m = owner.model;
            q.setFont(MONO.deriveFont(10f)); q.setColor(MUTED);
            centered(q, "INPUT / 03", left, 72); centered(q, "HIDDEN / 10", middle, 72); centered(q, "OUTPUT / 04", rightX, 72);
            for (int i = 0; i < 3; i++) for (int j = 0; j < 10; j++) {
                double weight = m == null ? 0 : m.w1[j][i];
                connection(q, left, y(i, 3, top + 15, bottom - 15), middle, y(j, 10, top, bottom), weight, input[i], phase + i * .23 + j * .06, p != null);
            }
            for (int j = 0; j < 10; j++) for (int k = 0; k < 4; k++) {
                double weight = m == null ? 0 : m.w2[k][j];
                connection(q, middle, y(j, 10, top, bottom), rightX, y(k, 4, top + 7, bottom - 7), weight, Math.abs(hidden[j]) * out[k], phase + j * .09 + k * .19, p != null);
            }
            String[] names = {"CPU", "RAM", "NET"}; Color[] colors = {BLUE, PURPLE, GOLD};
            for (int i = 0; i < 3; i++) {
                double cy = y(i, 3, top + 15, bottom - 15); node(q, left, cy, 13, input[i], colors[i]);
                q.setFont(MONO.deriveFont(Font.BOLD, 11f)); q.setColor(colors[i]); right(q, names[i], (int) left - 29, (int) cy - 2);
                q.setFont(MONO.deriveFont(10f)); q.setColor(MUTED);
                boolean available = i == 0 ? owner.telemetry.cpu >= 0 : i == 1 ? owner.telemetry.memory >= 0 : owner.telemetry.rx >= 0;
                right(q, available && p != null ? pct(input[i]) : "--", (int) left - 29, (int) cy + 13);
            }
            double hiddenRadius = Math.min(5, Math.max(2.5, (bottom - top) / 23));
            for (int j = 0; j < 10; j++) node(q, middle, y(j, 10, top, bottom), hiddenRadius, Math.abs(hidden[j]), hidden[j] < 0 ? PURPLE : CYAN);
            for (int k = 0; k < 4; k++) {
                double cy = y(k, 4, top + 7, bottom - 7); boolean winner = p != null && p.winner == k;
                node(q, rightX, cy, winner ? 12 : 8, out[k], SIGNALS[k]);
                q.setColor(winner ? SIGNALS[k] : MUTED); q.setFont(MONO.deriveFont(winner ? Font.BOLD : Font.PLAIN, 11f));
                q.drawString(CLASSES[k], (int) rightX + 28, (int) cy - 1);
                q.setFont(MONO.deriveFont(10f)); q.drawString(p == null ? "--" : pct(out[k]), (int) rightX + 28, (int) cy + 13);
            }
            q.setFont(MONO.deriveFont(9f)); q.setColor(MUTED);
            centered(q, "PHYSICAL SYSTEM", left, bottom + 25);
            centered(q, "TANH / 84 PARAMETERS", middle, bottom + 25);
            centered(q, "SOFTMAX / ACTIVITY", rightX, bottom + 25);
        }
        static double y(int index, int count, double top, double bottom) { return top + (bottom - top) * index / (count - 1); }
        void connection(Graphics2D q, double x1, double y1, double x2, double y2, double weight, double activation, double offset, boolean active) {
            Color c = weight < 0 ? PURPLE : CYAN;
            int opacity = active ? 16 + (int) (Math.min(1, Math.abs(weight) / 4) * clamp(activation) * 82) : 12;
            q.setColor(alpha(c, opacity)); q.setStroke(new BasicStroke(activation > .7 ? 1.3f : .7f));
            CubicCurve2D curve = new CubicCurve2D.Double(x1, y1, x1 + (x2 - x1) * .45, y1, x2 - (x2 - x1) * .45, y2, x2, y2); q.draw(curve);
            if (active && activation > .15) {
                double t = offset % 1, u = 1 - t;
                double px = u*u*u*x1 + 3*u*u*t*(x1+(x2-x1)*.45) + 3*u*t*t*(x2-(x2-x1)*.45) + t*t*t*x2;
                double py = u*u*u*y1 + 3*u*u*t*y1 + 3*u*t*t*y2 + t*t*t*y2;
                q.setColor(alpha(c, 60 + (int) (clamp(activation) * 160))); q.fill(new Ellipse2D.Double(px - 1.8, py - 1.8, 3.6, 3.6));
            }
        }
        void node(Graphics2D q, double x, double y, double radius, double activation, Color c) {
            for (int i = 3; i >= 1; i--) { q.setColor(alpha(c, (int) (activation * 10))); double r = radius + i * 5; q.fill(new Ellipse2D.Double(x-r, y-r, r*2, r*2)); }
            q.setColor(new Color(13, 27, 40)); q.fill(new Ellipse2D.Double(x-radius, y-radius, radius*2, radius*2));
            q.setColor(alpha(c, 65 + (int) (clamp(activation) * 180))); q.setStroke(new BasicStroke(1.5f)); q.draw(new Ellipse2D.Double(x-radius, y-radius, radius*2, radius*2));
            double r = Math.max(2, radius * .5); q.setColor(alpha(c, 40 + (int) (clamp(activation) * 210))); q.fill(new Ellipse2D.Double(x-r, y-r, r*2, r*2));
        }
        void drawBus(Graphics2D q, int w, int h) {
            double busY = h - 103;
            q.setStroke(new BasicStroke(1)); q.setColor(alpha(CYAN, 22)); q.drawLine(24, (int)busY - 20, w - 24, (int)busY - 20);
            q.drawLine(24, (int)busY + 9, w - 24, (int)busY + 9);
            int visible = (int) (16 + owner.activity * 74);
            for (int i = 0; i < visible; i++) {
                Particle p = particles.get(i); double x = 24 + p.progress * (w - 48);
                double yy = busY - 6 + (p.lane - .5) * 17 + Math.sin(phase * 1.8 + p.offset + p.progress * 10) * (1 + owner.activity * 3);
                Color c = p.kind == 0 ? BLUE : p.kind == 1 ? CYAN : GOLD;
                q.setColor(alpha(c, 25)); q.fill(new Ellipse2D.Double(x - 5, yy - 5, 10, 10));
                q.setColor(alpha(c, 130 + (int)(owner.activity * 100))); q.fill(new Ellipse2D.Double(x - 1.8, yy - 1.8, 3.6, 3.6));
                q.setColor(alpha(c, 55)); q.draw(new Line2D.Double(x - 5 - owner.activity * 15, yy, x, yy));
            }
        }
        void drawHistory(Graphics2D q, int w, int h) {
            q.setFont(MONO.deriveFont(9f)); q.setColor(MUTED); q.drawString("ACTIVITY / 90s", 24, h - 68);
            q.setColor(BLUE); q.drawString("CPU", 165, h - 68); q.setColor(GOLD); q.drawString("NET (LOG SCALE)", 200, h - 68);
            q.setColor(MUTED); right(q, (int)Math.round(owner.mix*100) + "% SYSTEM  +  " + (100-(int)Math.round(owner.mix*100)) + "% RANDOM", w - 24, h - 68);
            double top = h - 57, bottom = h - 19;
            q.setColor(LINE); q.setStroke(new BasicStroke(1)); q.draw(new Line2D.Double(24, bottom, w-24, bottom));
            plot(q, cpuHistory, BLUE, w, top, bottom); plot(q, netHistory, GOLD, w, top, bottom);
        }
        void plot(Graphics2D q, double[] samples, Color color, int w, double top, double bottom) {
            Path2D path = new Path2D.Double(); boolean drawing = false;
            for (int i = 0; i < historyCount; i++) {
                double value = samples[(historyCursor - historyCount + i + 90) % 90];
                if (value < 0) { drawing = false; continue; }
                double x = 24 + (w-48) * (i + 90-historyCount) / 89.0, y = bottom - clamp(value) * (bottom-top);
                if (!drawing) path.moveTo(x, y); else path.lineTo(x, y); drawing = true;
            }
            q.setColor(alpha(color, 40)); q.setStroke(new BasicStroke(4)); q.draw(path);
            q.setColor(color); q.setStroke(new BasicStroke(1.4f)); q.draw(path);
        }
        static void centered(Graphics2D q, String s, double x, double y) { q.drawString(s, (int)(x-q.getFontMetrics().stringWidth(s)/2.0), (int)y); }
        static void right(Graphics2D q, String s, int x, int y) { q.drawString(s, x-q.getFontMetrics().stringWidth(s), y); }
    }

    /** A weighted point cloud for a conceptual superposition, not measured quantum hardware. */
    static final class HydrogenSample {
        final double x, y, z, s, p, proposal, seed;
        HydrogenSample(Random random, boolean excited) {
            // |1s|^2: Gamma(3, 1/2) radial distribution; |2p_z|^2: Gamma(5, 1).
            double radius = 0;
            for (int i = 0; i < (excited ? 5 : 3); i++) radius -= Math.log(Math.max(1e-12, random.nextDouble())) * (excited ? 1 : .5);
            double cosine = excited ? Math.cbrt(2 * random.nextDouble() - 1) : 2 * random.nextDouble() - 1;
            double azimuth = random.nextDouble() * Math.PI * 2;
            x = radius * Math.sqrt(1 - cosine * cosine) * Math.cos(azimuth);
            y = radius * Math.sqrt(1 - cosine * cosine) * Math.sin(azimuth); z = radius * cosine;
            s = Math.exp(-radius) / Math.sqrt(Math.PI);
            p = z * Math.exp(-radius / 2) / (4 * Math.sqrt(2 * Math.PI));
            proposal = .5 * (s*s + p*p); seed = random.nextDouble() * Math.PI * 2;
        }
    }

    static final class AtomCanvas extends JPanel {
        final ConsolePanel owner;
        final List<HydrogenSample> cloud = new ArrayList<>();
        AtomCanvas(ConsolePanel owner) {
            this.owner = owner; setOpaque(false); setPreferredSize(new Dimension(1100, 390));
            Random r = new Random(114);
            for (int i = 0; i < 640; i++) cloud.add(new HydrogenSample(r, (i & 1) == 0));
            getAccessibleContext().setAccessibleName("Hydrogen 1s and 2p probability cloud connected to a silicon chip; conceptual activity visualization");
            setToolTipText("Illustrative hydrogen state superposition. CPU, memory, network activity, and the random blend drive both the cloud and the silicon graphic.");
        }
        static double density(double s, double p, double excited, double phase) {
            double a = Math.sqrt(1 - clamp(excited)) * s, b = Math.sqrt(clamp(excited)) * p;
            return Math.max(0, a*a + b*b + 2*a*b*Math.cos(phase));
        }
        static double excitedWeight(double activity) { return .12 + .70 * clamp(activity); }
        @Override protected void paintComponent(Graphics g) {
            super.paintComponent(g); Graphics2D q = (Graphics2D) g.create(); quality(q);
            int w = getWidth(), h = getHeight();
            q.setPaint(new GradientPaint(0, 0, new Color(14, 26, 41), w, h, new Color(12, 20, 32)));
            q.fillRoundRect(0, 0, w-1, h-1, 18, 18); q.setColor(LINE); q.drawRoundRect(0, 0, w-1, h-1, 18, 18);
            q.clip(new RoundRectangle2D.Double(1, 1, w-2, h-2, 18, 18));
            q.setFont(font(Font.BOLD, 13)); q.setColor(TEXT); q.drawString("HYDROGEN / SILICON FIELD", 24, 28);
            q.setFont(MONO.deriveFont(10f)); q.setColor(MUTED); q.drawString("PROBABILITY CLOUD  >  STATE MODEL  >  COMPUTATION", 24, 46);
            q.setColor(CYAN); BusCanvas.right(q, owner.paused ? "MOTION PAUSED" : "ACTIVITY-RESPONSIVE", w-24, 28);
            double sceneHeight = Math.max(75, h-140), cy = 70 + sceneHeight/2;
            double radius = Math.min(98, sceneHeight*.40), atomX = w*.23, chipX = w*.77;
            double phase = owner.canvas.phase, activity = owner.activity, excited = excitedWeight(activity);
            for (int x = 24; x < w; x += 26) for (int y = 70; y < h-52; y += 26) {
                q.setColor(new Color(45, 66, 81, 48)); q.fillRect(x, y, 1, 1);
            }
            bridge(q, atomX+radius*1.05, chipX-radius*1.12, cy, phase, activity);
            hydrogen(q, atomX, cy, radius, phase, activity, excited);
            silicon(q, chipX, cy, radius, phase, activity);
            q.setFont(MONO.deriveFont(Font.BOLD, 11f)); q.setColor(CYAN);
            BusCanvas.centered(q, "H / HYDROGEN", atomX, 69);
            q.setColor(GOLD); BusCanvas.centered(q, "Si / SILICON CHIP", chipX, 69);
            double captionY = Math.min(h-43, cy+radius+22);
            q.setFont(MONO.deriveFont(10f)); q.setColor(MUTED);
            BusCanvas.centered(q, "1s " + pct(1-excited) + "  +  2p " + pct(excited), atomX, captionY);
            BusCanvas.centered(q, owner.prediction == null ? "LOCAL NEURAL ENGINE" : "INFERENCE / " + CLASSES[owner.prediction.winner], chipX, captionY);
            q.setColor(LINE); q.drawLine(24, h-34, w-24, h-34);
            q.setFont(font(Font.PLAIN, 10)); q.setColor(MUTED);
            q.drawString("Conceptual quantum-state view. Particles represent probability samples for one electron.", 24, h-16);
            q.setFont(MONO.deriveFont(9f)); q.setColor(CYAN);
            BusCanvas.right(q, (int)Math.round(owner.mix*100) + "% SYSTEM / " + (100-(int)Math.round(owner.mix*100)) + "% RANDOM", w-24, h-16);
            q.dispose();
        }
        void hydrogen(Graphics2D q, double cx, double cy, double r, double phase, double activity, double excited) {
            for (int i = 5; i > 0; i--) {
                double halo = r * (.5 + i*.14);
                q.setColor(alpha(CYAN, 3+(int)(activity*2))); q.fill(new Ellipse2D.Double(cx-halo, cy-halo, halo*2, halo*2));
            }
            q.setStroke(new BasicStroke(.8f));
            q.setColor(alpha(CYAN, 34)); q.draw(new Ellipse2D.Double(cx-r, cy-r, r*2, r*2));
            q.setColor(alpha(PURPLE, 35)); q.draw(new Ellipse2D.Double(cx-r*.60, cy-r, r*1.2, r*2));
            q.setColor(alpha(BLUE, 34)); q.draw(new Ellipse2D.Double(cx-r, cy-r*.40, r*2, r*.8));
            Shape oldClip = q.getClip(); q.clip(new Ellipse2D.Double(cx-r*1.04, cy-r*1.04, r*2.08, r*2.08));
            double angle = phase*.18, ca = Math.cos(angle), sa = Math.sin(angle), scale = r/9;
            for (HydrogenSample sample : cloud) {
                double importance = density(sample.s, sample.p, excited, phase*1.2) / Math.max(1e-30, sample.proposal);
                double intensity = clamp(importance/2);
                if (intensity < .014) continue;
                double px = (sample.x*ca - sample.y*sa)*scale;
                double py = (-sample.z*.92 + (sample.x*sa+sample.y*ca)*.24)*scale;
                // Small decorative drift is separate from the probability weight.
                double jitter = (1-owner.mix)*1.6;
                px += Math.sin(phase+sample.seed)*jitter; py += Math.cos(phase*.8+sample.seed)*jitter;
                Color color = Math.abs(Math.sqrt(excited)*sample.p) > Math.abs(Math.sqrt(1-excited)*sample.s) ? PURPLE : CYAN;
                int opacity = (int)(intensity*(135+activity*110));
                double size = 1.25 + intensity*1.4 + activity*.7;
                q.setColor(alpha(color, opacity/7)); q.fill(new Ellipse2D.Double(cx+px-size*2, cy+py-size*2, size*4, size*4));
                q.setColor(alpha(color, opacity)); q.fill(new Ellipse2D.Double(cx+px-size/2, cy+py-size/2, size, size));
            }
            q.setClip(oldClip);
            double core = Math.max(4, r*.07), glow = core*(3+activity);
            q.setColor(alpha(GOLD, 22)); q.fill(new Ellipse2D.Double(cx-glow, cy-glow, glow*2, glow*2));
            q.setColor(GOLD); q.fill(new Ellipse2D.Double(cx-core, cy-core, core*2, core*2));
            q.setColor(TEXT); q.setFont(font(Font.BOLD, 11)); BusCanvas.centered(q, "+", cx, cy+4);
        }
        void bridge(Graphics2D q, double left, double right, double cy, double phase, double activity) {
            double middle = (left+right)/2, amplitude = 4+activity*13;
            for (int lane = -1; lane <= 1; lane++) {
                Path2D wave = new Path2D.Double();
                for (int i = 0; i <= 100; i++) {
                    double t = i/100.0, x = left+t*(right-left);
                    double y = cy + lane*12 + Math.sin(t*Math.PI*4-phase*2+lane)*amplitude*Math.sin(Math.PI*t);
                    if (i == 0) wave.moveTo(x, y); else wave.lineTo(x, y);
                }
                q.setStroke(new BasicStroke(5)); q.setColor(alpha(lane == 0 ? CYAN : PURPLE, 12)); q.draw(wave);
                q.setStroke(new BasicStroke(1)); q.setColor(alpha(lane == 0 ? CYAN : PURPLE, 45+(int)(activity*50))); q.draw(wave);
            }
            int count = 7+(int)(activity*18);
            for (int i = 0; i < count; i++) {
                double t = (phase*.16+i/(double)count)%1;
                double x = left+t*(right-left), y = cy + Math.sin(t*Math.PI*4-phase*2)*amplitude*Math.sin(Math.PI*t);
                Color color = t < .5 ? CYAN : GOLD;
                q.setColor(alpha(color, 25)); q.fill(new Ellipse2D.Double(x-6, y-6, 12, 12));
                q.setColor(alpha(color, 130+(int)(activity*100))); q.fill(new Ellipse2D.Double(x-2, y-2, 4, 4));
            }
            q.setFont(MONO.deriveFont(Font.BOLD, 10f)); q.setColor(TEXT); BusCanvas.centered(q, "WAVE MODEL > COMPUTE", middle, cy-37);
            q.setFont(MONO.deriveFont(10f)); q.setColor(MUTED); BusCanvas.centered(q, "ACTIVITY " + pct(activity), middle, cy+40);
            q.setColor(alpha(CYAN, 25)); q.fillRoundRect((int)middle-58, (int)cy+48, 116, 3, 3, 3);
            q.setColor(CYAN); q.fillRoundRect((int)middle-58, (int)cy+48, (int)(116*activity), 3, 3, 3);
        }
        void silicon(Graphics2D q, double cx, double cy, double r, double phase, double activity) {
            double half = r*.77;
            for (int i = 3; i > 0; i--) {
                double pad = i*6; q.setColor(alpha(GOLD, 4+(int)(activity*3)));
                q.fill(new RoundRectangle2D.Double(cx-half-pad, cy-half-pad, 2*(half+pad), 2*(half+pad), 18, 18));
            }
            for (int i = 0; i < 9; i++) {
                double offset = (i-4)*half*.19;
                double lit = .2 + activity*.6 + Math.sin(phase*2+i)*.15;
                q.setColor(alpha(GOLD, (int)(60+lit*160))); q.setStroke(new BasicStroke((float)Math.max(2, r*.026)));
                q.draw(new Line2D.Double(cx-half-12, cy+offset, cx-half, cy+offset));
                q.draw(new Line2D.Double(cx+half, cy+offset, cx+half+12, cy+offset));
                q.draw(new Line2D.Double(cx+offset, cy-half-12, cx+offset, cy-half));
                q.draw(new Line2D.Double(cx+offset, cy+half, cx+offset, cy+half+12));
            }
            q.setPaint(new GradientPaint((float)(cx-half), (float)(cy-half), new Color(32, 43, 55), (float)(cx+half), (float)(cy+half), new Color(13, 27, 37)));
            q.fill(new RoundRectangle2D.Double(cx-half, cy-half, half*2, half*2, 10, 10));
            q.setColor(alpha(GOLD, 125+(int)(activity*100))); q.setStroke(new BasicStroke(1.4f)); q.draw(new RoundRectangle2D.Double(cx-half, cy-half, half*2, half*2, 10, 10));
            double inset = half*.75;
            q.setColor(alpha(CYAN, 25)); q.fill(new Rectangle2D.Double(cx-inset, cy-inset, inset*2, inset*2));
            for (int row = 0; row < 7; row++) for (int col = 0; col < 7; col++) {
                double x = cx-inset+(col+.5)*inset*2/7, y = cy-inset+(row+.5)*inset*2/7;
                double level = clamp(activity*.85 + .15*Math.sin(phase*2+row*.8+col*.7));
                if (row < 2 || row > 4 || col < 2 || col > 4) {
                    q.setColor(alpha((row+col)%3 == 0 ? GOLD : CYAN, 20+(int)(level*170)));
                    double cell = inset*.18; q.fill(new Rectangle2D.Double(x-cell/2, y-cell/2, cell, cell));
                }
            }
            q.setColor(TEXT); q.setFont(font(Font.BOLD, (int)Math.max(16, r*.30))); BusCanvas.centered(q, "Si", cx, cy+5);
            q.setColor(GOLD); q.setFont(MONO.deriveFont((float)Math.max(8, r*.1))); BusCanvas.centered(q, "14", cx, cy+half*.37);
            q.setColor(alpha(CYAN, 80)); q.setStroke(new BasicStroke(.6f));
            q.draw(new Rectangle2D.Double(cx-inset, cy-inset, inset*2, inset*2));
        }
    }

    public static void main(String[] args) {
        Locale.setDefault(Locale.ROOT);
        SwingUtilities.invokeLater(() -> {
            UIManager.put("Slider.foreground", CYAN); UIManager.put("Slider.background", PANEL);
            UIManager.put("Slider.focus", BG); UIManager.put("Button.select", new Color(43, 70, 82));
            LocalInferenceBusEngine app = new LocalInferenceBusEngine(); app.setVisible(true);
            app.console.command.requestFocusInWindow();
        });
    }
}
