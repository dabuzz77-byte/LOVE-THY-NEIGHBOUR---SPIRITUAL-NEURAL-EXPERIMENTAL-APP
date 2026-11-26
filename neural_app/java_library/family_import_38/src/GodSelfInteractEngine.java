import neural.studio.*;
import com.sun.management.OperatingSystemMXBean;
import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JProgressBar;
import javax.swing.JScrollPane;
import javax.swing.JSlider;
import javax.swing.JSplitPane;
import javax.swing.SwingConstants;
import javax.swing.SwingUtilities;
import neural.studio.SharedTimer;
import javax.swing.UIManager;
import javax.swing.border.EmptyBorder;
import java.awt.BasicStroke;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GradientPaint;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GridLayout;
import java.awt.RenderingHints;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Path2D;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.util.Random;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/** Manifest-centered particle visualization driven by local system telemetry. */
public final class GodSelfInteractEngine extends SectionFrame {
    private static final Color BACKGROUND = new Color(6, 11, 20);
    private static final Color PANEL = new Color(14, 22, 35);
    private static final Color PANEL_EDGE = new Color(38, 62, 86);
    private static final Color TEXT = new Color(225, 239, 248);
    private static final Color MUTED = new Color(133, 157, 180);
    private static final Color CPU_COLOR = new Color(67, 220, 239);
    private static final Color RAM_COLOR = new Color(176, 130, 255);
    private static final Color GPU_COLOR = new Color(255, 181, 91);
    private static final Color NET_COLOR = new Color(103, 234, 162);
    private static final String POWERSHELL_METRICS =
            "$ErrorActionPreference='SilentlyContinue';" +
            "$gpu=-1.0;try{$s=(Get-Counter -Counter '\\GPU Engine(*)\\Utilization Percentage' -MaxSamples 1 -ErrorAction Stop).CounterSamples;" +
            "if($s){$v=@($s|ForEach-Object{[double]$_.CookedValue});if($v.Count -gt 0){$gpu=[math]::Min(100.0,[math]::Max(0.0,(($v|Measure-Object -Maximum).Maximum)))}}}catch{};" +
            "$rx=0L;$tx=0L;try{$n=Get-NetAdapterStatistics -ErrorAction Stop;foreach($a in $n){$rx += [long]$a.ReceivedBytes;$tx += [long]$a.SentBytes}}catch{$rx=-1L;$tx=-1L};" +
            "$gs='NA';if($gpu -ge 0){$gs=[string]::Format([cultureinfo]::InvariantCulture,'{0:F1}',$gpu)};" +
            "Write-Output ('GPU='+$gs+';RX='+$rx+';TX='+$tx)";

    private final ManifestCanvas manifestCanvas = new ManifestCanvas();
    private final TelemetryPanel telemetryPanel = new TelemetryPanel();
    private final TelemetrySampler telemetrySampler = new TelemetrySampler();
    private final ScheduledExecutorService telemetryExecutor =
            SharedScheduler.newSingleThreadScheduledExecutor(runnable -> {
                Thread thread = new Thread(runnable, "god-self-telemetry");
                thread.setDaemon(true);
                return thread;
            });
    private final SharedTimer animationTimer;
    private final JButton pauseButton = new JButton("Pause animation");
    private final JLabel statusLabel = new JLabel("Starting local system telemetry…");

    private double particleScale = 0.8;
    private boolean paused;

    public GodSelfInteractEngine() {
        super("God Self Interact Engine | Manifest Activity Monitor");
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(1120, 760));
        setSize(1500, 960);
        setLocationRelativeTo(null);

        JPanel root = new JPanel(new BorderLayout(11, 11));
        root.setBackground(BACKGROUND);
        root.setBorder(new EmptyBorder(14, 16, 12, 16));
        setContentPane(root);
        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildMainArea(), BorderLayout.CENTER);
        root.add(buildFooter(), BorderLayout.SOUTH);

        animationTimer = new SharedTimer(33, event -> {
            manifestCanvas.advance(particleScale);
            manifestCanvas.repaint();
        });
        animationTimer.start();
        telemetryExecutor.scheduleWithFixedDelay(this::sampleTelemetry, 0, 2, TimeUnit.SECONDS);
        addWindowListener(new java.awt.event.WindowAdapter() {
            @Override
            public void windowClosing(java.awt.event.WindowEvent event) {
                animationTimer.stop();
                telemetryExecutor.shutdownNow();
            }
        });
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout(12, 0));
        header.setOpaque(false);
        JPanel titleBlock = new JPanel(new GridLayout(2, 1, 0, 4));
        titleBlock.setOpaque(false);
        JLabel title = new JLabel("GOD SELF INTERACT  /  MANIFEST ENGINE");
        title.setForeground(TEXT);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 21));
        JLabel subtitle = new JLabel(
                "Live CPU, memory, GPU, and aggregate network activity animate particles around the manifest center.");
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        titleBlock.add(title);
        titleBlock.add(subtitle);

        JLabel badge = new JLabel(" LOCAL TELEMETRY ", SwingConstants.CENTER);
        badge.setForeground(NET_COLOR);
        badge.setFont(new Font(Font.MONOSPACED, Font.BOLD, 11));
        badge.setOpaque(true);
        badge.setBackground(new Color(14, 45, 39));
        badge.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(40, 116, 88)),
                new EmptyBorder(7, 10, 7, 10)));
        header.add(titleBlock, BorderLayout.CENTER);
        header.add(badge, BorderLayout.EAST);
        return header;
    }

    private JSplitPane buildMainArea() {
        JPanel canvasFrame = new JPanel(new BorderLayout());
        canvasFrame.setBackground(PANEL);
        canvasFrame.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(PANEL_EDGE), new EmptyBorder(1, 1, 1, 1)));
        manifestCanvas.setPreferredSize(new Dimension(1020, 700));
        canvasFrame.add(manifestCanvas, BorderLayout.CENTER);

        JScrollPane telemetryScroll = new JScrollPane(telemetryPanel);
        telemetryScroll.setBorder(null);
        telemetryScroll.getViewport().setBackground(BACKGROUND);
        telemetryScroll.getVerticalScrollBar().setUnitIncrement(22);
        JSplitPane split = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT,
                canvasFrame, telemetryScroll);
        split.setResizeWeight(0.74);
        split.setDividerLocation(1080);
        split.setDividerSize(7);
        split.setBackground(BACKGROUND);
        split.setBorder(null);
        return split;
    }

    private JPanel buildFooter() {
        JPanel footer = new JPanel(new BorderLayout(12, 0));
        footer.setBackground(PANEL);
        footer.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(PANEL_EDGE), new EmptyBorder(7, 10, 7, 10)));
        statusLabel.setForeground(MUTED);
        statusLabel.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));

        pauseButton.setForeground(TEXT);
        pauseButton.setBackground(new Color(27, 42, 58));
        pauseButton.setFocusPainted(false);
        pauseButton.addActionListener(event -> toggleAnimation());
        JButton reset = new JButton("Reset particles");
        reset.setForeground(TEXT);
        reset.setBackground(new Color(27, 42, 58));
        reset.setFocusPainted(false);
        reset.addActionListener(event -> manifestCanvas.resetParticles());

        JSlider density = new JSlider(20, 100, 80);
        density.setOpaque(false);
        density.setToolTipText("Adjust particle density in the manifest field.");
        density.addChangeListener(event -> {
            particleScale = density.getValue() / 100.0;
            manifestCanvas.setParticleScale(particleScale);
        });
        JLabel densityLabel = new JLabel("Particle density");
        densityLabel.setForeground(TEXT);
        JPanel controls = new JPanel(new GridLayout(1, 4, 7, 0));
        controls.setOpaque(false);
        controls.add(densityLabel);
        controls.add(density);
        controls.add(pauseButton);
        controls.add(reset);
        footer.add(statusLabel, BorderLayout.CENTER);
        footer.add(controls, BorderLayout.EAST);
        return footer;
    }

    private void toggleAnimation() {
        paused = !paused;
        if (paused) {
            animationTimer.stop();
            pauseButton.setText("Resume animation");
        } else {
            animationTimer.start();
            pauseButton.setText("Pause animation");
        }
    }

    private void sampleTelemetry() {
        TelemetrySnapshot snapshot = telemetrySampler.sample();
        SwingUtilities.invokeLater(() -> {
            telemetryPanel.update(snapshot);
            manifestCanvas.setTelemetry(snapshot);
            statusLabel.setText(snapshot.gpuPercent >= 0.0
                    ? "GPU engine activity is the busiest reported Windows GPU engine; network totals sum visible adapters."
                    : "GPU counters unavailable; CPU, RAM, and network data continue. Network totals sum visible adapters.");
        });
    }

    private static double clamp(double value, double low, double high) {
        return Math.max(low, Math.min(high, value));
    }

    private static final class TelemetrySnapshot {
        private final double cpuPercent;
        private final double memoryPercent;
        private final double gpuPercent;
        private final long memoryUsedBytes;
        private final long memoryTotalBytes;
        private final long receivedTotalBytes;
        private final long sentTotalBytes;
        private final double receivedBytesPerSecond;
        private final double sentBytesPerSecond;
        private final long sampledAtMillis;

        private TelemetrySnapshot(double cpuPercent, double memoryPercent, double gpuPercent,
                                  long memoryUsedBytes, long memoryTotalBytes,
                                  long receivedTotalBytes, long sentTotalBytes,
                                  double receivedBytesPerSecond, double sentBytesPerSecond,
                                  long sampledAtMillis) {
            this.cpuPercent = cpuPercent;
            this.memoryPercent = memoryPercent;
            this.gpuPercent = gpuPercent;
            this.memoryUsedBytes = memoryUsedBytes;
            this.memoryTotalBytes = memoryTotalBytes;
            this.receivedTotalBytes = receivedTotalBytes;
            this.sentTotalBytes = sentTotalBytes;
            this.receivedBytesPerSecond = receivedBytesPerSecond;
            this.sentBytesPerSecond = sentBytesPerSecond;
            this.sampledAtMillis = sampledAtMillis;
        }
    }

    private static final class WindowsCounters {
        private final double gpuPercent;
        private final long receivedBytes;
        private final long sentBytes;

        private WindowsCounters(double gpuPercent, long receivedBytes, long sentBytes) {
            this.gpuPercent = gpuPercent;
            this.receivedBytes = receivedBytes;
            this.sentBytes = sentBytes;
        }

        private static WindowsCounters unavailable() {
            return new WindowsCounters(-1.0, -1L, -1L);
        }
    }

    private static final class TelemetrySampler {
        private long previousReceived = -1L;
        private long previousSent = -1L;
        private long previousNetworkNanos = -1L;

        private TelemetrySnapshot sample() {
            double cpu = -1.0;
            double memory = -1.0;
            long memoryUsed = -1L;
            long memoryTotal = -1L;
            try {
                java.lang.management.OperatingSystemMXBean bean =
                        ManagementFactory.getOperatingSystemMXBean();
                if (bean instanceof OperatingSystemMXBean) {
                    OperatingSystemMXBean os = (OperatingSystemMXBean) bean;
                    double cpuReading = os.getCpuLoad();
                    if (cpuReading >= 0.0 && cpuReading <= 1.0) cpu = cpuReading * 100.0;
                    memoryTotal = os.getTotalMemorySize();
                    long free = os.getFreeMemorySize();
                    if (memoryTotal > 0L && free >= 0L) {
                        memoryUsed = Math.max(0L, memoryTotal - free);
                        memory = clamp(memoryUsed * 100.0 / memoryTotal, 0.0, 100.0);
                    }
                }
            } catch (RuntimeException ignored) {
                // Keep unsupported readings marked unavailable.
            }

            WindowsCounters windows = readWindowsCounters();
            double receivedRate = -1.0;
            double sentRate = -1.0;
            long now = System.nanoTime();
            if (windows.receivedBytes >= 0L && windows.sentBytes >= 0L) {
                if (previousReceived >= 0L && previousSent >= 0L && previousNetworkNanos > 0L
                        && windows.receivedBytes >= previousReceived
                        && windows.sentBytes >= previousSent) {
                    double seconds = (now - previousNetworkNanos) / 1_000_000_000.0;
                    if (seconds > 0.0) {
                        receivedRate = (windows.receivedBytes - previousReceived) / seconds;
                        sentRate = (windows.sentBytes - previousSent) / seconds;
                    }
                }
                previousReceived = windows.receivedBytes;
                previousSent = windows.sentBytes;
                previousNetworkNanos = now;
            }
            return new TelemetrySnapshot(cpu, memory, windows.gpuPercent,
                    memoryUsed, memoryTotal, windows.receivedBytes, windows.sentBytes,
                    receivedRate, sentRate, System.currentTimeMillis());
        }

        private WindowsCounters readWindowsCounters() {
            Process process = null;
            try {
                process = new ProcessBuilder("powershell.exe", "-NoLogo", "-NoProfile",
                        "-NonInteractive", "-WindowStyle", "Hidden", "-Command", POWERSHELL_METRICS)
                        .redirectErrorStream(true).start();
                if (!process.waitFor(3500L, TimeUnit.MILLISECONDS)) {
                    process.destroyForcibly();
                    return WindowsCounters.unavailable();
                }
                String metrics = null;
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                        process.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        line = line.trim();
                        if (line.startsWith("\uFEFF")) line = line.substring(1);
                        int marker = line.indexOf("GPU=");
                        if (marker >= 0) metrics = line.substring(marker);
                    }
                }
                if (metrics == null) return WindowsCounters.unavailable();
                double gpu = -1.0;
                long received = -1L;
                long sent = -1L;
                String[] fields = metrics.split(";");
                for (String field : fields) {
                    String[] pair = field.split("=", 2);
                    if (pair.length != 2) continue;
                    if (pair[0].equals("GPU") && !pair[1].equals("NA")) {
                        gpu = Double.parseDouble(pair[1]);
                    } else if (pair[0].equals("RX")) {
                        received = Long.parseLong(pair[1]);
                    } else if (pair[0].equals("TX")) {
                        sent = Long.parseLong(pair[1]);
                    }
                }
                return new WindowsCounters(gpu, received, sent);
            } catch (Exception ignored) {
                if (ignored instanceof InterruptedException) Thread.currentThread().interrupt();
                return WindowsCounters.unavailable();
            } finally {
                if (process != null && process.isAlive()) process.destroyForcibly();
            }
        }
    }

    private static final class TelemetryPanel extends JPanel {
        private final MetricCard cpu = new MetricCard("CPU ACTIVITY", CPU_COLOR);
        private final MetricCard memory = new MetricCard("RAM PRESSURE", RAM_COLOR);
        private final MetricCard gpu = new MetricCard("GPU ENGINE", GPU_COLOR);
        private final NetworkCard network = new NetworkCard();
        private final TelemetryChart chart = new TelemetryChart();

        private TelemetryPanel() {
            setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
            setBackground(BACKGROUND);
            setBorder(new EmptyBorder(0, 10, 0, 0));
            setPreferredSize(new Dimension(350, 720));
            add(cpu);
            add(Box.createVerticalStrut(8));
            add(memory);
            add(Box.createVerticalStrut(8));
            add(gpu);
            add(Box.createVerticalStrut(8));
            add(network);
            add(Box.createVerticalStrut(8));
            add(chart);
        }

        private void update(TelemetrySnapshot snapshot) {
            cpu.setMetric(snapshot.cpuPercent, "System utilization",
                    snapshot.cpuPercent >= 0.0 ? String.format("%.1f%%", snapshot.cpuPercent) : "N/A");
            memory.setMetric(snapshot.memoryPercent,
                    "Used " + formatBytes(snapshot.memoryUsedBytes) + " / " + formatBytes(snapshot.memoryTotalBytes),
                    snapshot.memoryPercent >= 0.0 ? String.format("%.1f%%", snapshot.memoryPercent) : "N/A");
            gpu.setMetric(snapshot.gpuPercent, "Busiest reported GPU engine",
                    snapshot.gpuPercent >= 0.0 ? String.format("%.1f%%", snapshot.gpuPercent) : "N/A");
            network.setSnapshot(snapshot);
            chart.addSnapshot(snapshot);
        }
    }

    private static class MetricCard extends JPanel {
        private final Color accent;
        private final JLabel value = new JLabel("N/A");
        private final JLabel detail = new JLabel("Waiting for telemetry…");
        private final JProgressBar bar = new JProgressBar(0, 100);

        private MetricCard(String title, Color accent) {
            this.accent = accent;
            setLayout(new BorderLayout(0, 5));
            setBackground(PANEL);
            setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(PANEL_EDGE),
                    new EmptyBorder(8, 9, 8, 9)));
            JLabel heading = new JLabel(title);
            heading.setForeground(accent);
            heading.setFont(new Font(Font.MONOSPACED, Font.BOLD, 10));
            value.setForeground(TEXT);
            value.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 20));
            detail.setForeground(MUTED);
            detail.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
            bar.setStringPainted(false);
            bar.setForeground(accent);
            bar.setBackground(new Color(7, 14, 24));
            bar.setBorder(BorderFactory.createLineBorder(new Color(37, 55, 74)));

            JPanel content = new JPanel(new BorderLayout(0, 4));
            content.setOpaque(false);
            content.add(value, BorderLayout.NORTH);
            content.add(bar, BorderLayout.CENTER);
            content.add(detail, BorderLayout.SOUTH);
            add(heading, BorderLayout.NORTH);
            add(content, BorderLayout.CENTER);
            setPreferredSize(new Dimension(330, 104));
            setMaximumSize(new Dimension(380, 112));
        }

        private void setMetric(double percent, String text, String formattedValue) {
            value.setText(formattedValue);
            detail.setText(text);
            bar.setValue(percent >= 0.0 ? (int) Math.round(clamp(percent, 0.0, 100.0)) : 0);
            bar.setString(percent >= 0.0 ? formattedValue : "unavailable");
        }
    }

    private static final class NetworkCard extends JPanel {
        private final JLabel heading = new JLabel("TOTAL NETWORK ACTIVITY");
        private final JLabel rates = new JLabel("RX —   TX —");
        private final JLabel totals = new JLabel("Totals: waiting for adapter counters…");
        private final JProgressBar activity = new JProgressBar(0, 100);

        private NetworkCard() {
            setLayout(new BorderLayout(0, 5));
            setBackground(PANEL);
            setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(PANEL_EDGE),
                    new EmptyBorder(8, 9, 8, 9)));
            heading.setForeground(NET_COLOR);
            heading.setFont(new Font(Font.MONOSPACED, Font.BOLD, 10));
            rates.setForeground(TEXT);
            rates.setFont(new Font(Font.MONOSPACED, Font.BOLD, 13));
            totals.setForeground(MUTED);
            totals.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
            activity.setForeground(NET_COLOR);
            activity.setBackground(new Color(7, 14, 24));
            activity.setBorder(BorderFactory.createLineBorder(new Color(37, 55, 74)));
            JPanel content = new JPanel(new BorderLayout(0, 5));
            content.setOpaque(false);
            content.add(rates, BorderLayout.NORTH);
            content.add(activity, BorderLayout.CENTER);
            content.add(totals, BorderLayout.SOUTH);
            add(heading, BorderLayout.NORTH);
            add(content, BorderLayout.CENTER);
            setPreferredSize(new Dimension(330, 126));
            setMaximumSize(new Dimension(380, 136));
        }

        private void setSnapshot(TelemetrySnapshot snapshot) {
            if (snapshot.receivedTotalBytes >= 0L && snapshot.sentTotalBytes >= 0L) {
                rates.setText("RX " + formatRate(snapshot.receivedBytesPerSecond)
                        + "   TX " + formatRate(snapshot.sentBytesPerSecond));
                totals.setText("All adapters  |  RX " + formatBytes(snapshot.receivedTotalBytes)
                        + "  TX " + formatBytes(snapshot.sentTotalBytes));
                double combined = Math.max(0.0, snapshot.receivedBytesPerSecond)
                        + Math.max(0.0, snapshot.sentBytesPerSecond);
                activity.setValue((int) Math.round(networkIntensity(combined) * 100.0));
            } else {
                rates.setText("RX N/A   TX N/A");
                totals.setText("Windows adapter counters unavailable");
                activity.setValue(0);
            }
        }
    }

    private static final class TelemetryChart extends JPanel {
        private final double[][] history = new double[4][90];
        private int position;
        private int count;

        private TelemetryChart() {
            setBackground(PANEL);
            setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(PANEL_EDGE),
                    new EmptyBorder(6, 7, 6, 7)));
            setPreferredSize(new Dimension(330, 220));
            setMinimumSize(new Dimension(250, 170));
        }

        private void addSnapshot(TelemetrySnapshot snapshot) {
            history[0][position] = snapshot.cpuPercent;
            history[1][position] = snapshot.memoryPercent;
            history[2][position] = snapshot.gpuPercent;
            double totalRate = Math.max(0.0, snapshot.receivedBytesPerSecond)
                    + Math.max(0.0, snapshot.sentBytesPerSecond);
            history[3][position] = snapshot.receivedBytesPerSecond < 0.0
                    ? -1.0 : networkIntensity(totalRate) * 100.0;
            position = (position + 1) % history[0].length;
            count = Math.min(count + 1, history[0].length);
            repaint();
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setColor(TEXT);
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 10));
            g.drawString("ACTIVITY HISTORY  /  3 MIN", 9, 16);
            int left = 10;
            int top = 26;
            int plotWidth = Math.max(20, getWidth() - 20);
            int plotHeight = Math.max(20, getHeight() - 55);
            g.setStroke(new BasicStroke(1f));
            g.setColor(new Color(53, 76, 98));
            for (int i = 0; i <= 4; i++) {
                int y = top + plotHeight * i / 4;
                g.drawLine(left, y, left + plotWidth, y);
            }
            Color[] colors = {CPU_COLOR, RAM_COLOR, GPU_COLOR, NET_COLOR};
            for (int series = 0; series < history.length; series++) {
                g.setColor(colors[series]);
                g.setStroke(new BasicStroke(1.6f));
                int previousX = -1;
                int previousY = -1;
                int oldest = count == history[series].length ? position : 0;
                for (int i = 0; i < count; i++) {
                    double value = history[series][(oldest + i) % history[series].length];
                    if (value < 0.0) {
                        previousX = -1;
                        continue;
                    }
                    int x = left + (count <= 1 ? 0 : i * plotWidth / (count - 1));
                    int y = top + plotHeight - (int) (clamp(value, 0.0, 100.0) * plotHeight / 100.0);
                    if (previousX >= 0) g.drawLine(previousX, previousY, x, y);
                    previousX = x;
                    previousY = y;
                }
            }
            g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 9));
            int legendY = getHeight() - 9;
            String[] names = {"CPU", "RAM", "GPU", "NET"};
            int x = 10;
            for (int i = 0; i < names.length; i++) {
                g.setColor(colors[i]);
                g.fillRect(x, legendY - 8, 8, 3);
                g.drawString(names[i], x + 11, legendY - 4);
                x += 61;
            }
            g.dispose();
        }
    }

    private static final class ManifestCanvas extends JPanel {
        private static final int CPU = 0;
        private static final int RAM = 1;
        private static final int GPU = 2;
        private static final int NET = 3;
        private static final String[] ELEMENTS = {
                "SAND", "WATER", "TREE", "FIRE", "ROCK", "AIR", "METAL"
        };
        private static final double[] BASE_RADII = {0.19, 0.27, 0.35, 0.43};

        private final Random random = new Random();
        private final Particle[] particles = new Particle[160];
        private final double[] starX = new double[115];
        private final double[] starY = new double[115];
        private TelemetrySnapshot telemetry = new TelemetrySnapshot(
                -1.0, -1.0, -1.0, -1L, -1L, -1L, -1L, -1.0, -1.0, 0L);
        private double rotation;
        private double pulse;
        private double particleScale = 0.8;

        private ManifestCanvas() {
            setOpaque(true);
            setBackground(BACKGROUND);
            for (int i = 0; i < particles.length; i++) {
                particles[i] = new Particle(i % 4, random);
            }
            for (int i = 0; i < starX.length; i++) {
                starX[i] = random.nextDouble();
                starY[i] = random.nextDouble();
            }
        }

        private void setTelemetry(TelemetrySnapshot telemetry) {
            this.telemetry = telemetry;
            repaint();
        }

        private void setParticleScale(double particleScale) {
            this.particleScale = clamp(particleScale, 0.2, 1.0);
            repaint();
        }

        private void advance(double particleScale) {
            this.particleScale = clamp(particleScale, 0.2, 1.0);
            double cpu = normalized(telemetry.cpuPercent);
            double ram = normalized(telemetry.memoryPercent);
            double gpu = normalized(telemetry.gpuPercent);
            double network = networkActivity();
            rotation = (rotation + 0.0025 + (cpu * 0.010) + network * 0.004) % (Math.PI * 2.0);
            pulse += 0.035 + cpu * 0.09 + gpu * 0.04;
            for (Particle particle : particles) {
                double signal = activityFor(particle.channel, cpu, ram, gpu, network);
                particle.advance(signal, network, random);
            }
        }

        private double activityFor(int channel, double cpu, double ram,
                                   double gpu, double network) {
            if (channel == CPU) return cpu;
            if (channel == RAM) return ram;
            if (channel == GPU) return telemetry.gpuPercent >= 0.0 ? gpu : 0.04;
            return network;
        }

        private double networkActivity() {
            if (telemetry.receivedBytesPerSecond < 0.0 || telemetry.sentBytesPerSecond < 0.0) return 0.0;
            double totalRate = telemetry.receivedBytesPerSecond + telemetry.sentBytesPerSecond;
            return networkIntensity(totalRate);
        }

        private static double normalized(double percent) {
            return percent < 0.0 ? 0.04 : clamp(percent / 100.0, 0.0, 1.0);
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
            int width = getWidth();
            int height = getHeight();
            g.setPaint(new GradientPaint(0, 0, new Color(10, 21, 35),
                    0, height, new Color(4, 8, 16)));
            g.fillRect(0, 0, width, height);
            drawStars(g, width, height);
            drawGrid(g, width, height);
            drawManifestField(g, width, height);
            drawElementLabels(g, width, height);
            g.dispose();
        }

        private void drawStars(Graphics2D g, int width, int height) {
            for (int i = 0; i < starX.length; i++) {
                int x = (int) (starX[i] * width);
                int y = (int) (starY[i] * height);
                int alpha = 45 + (i % 5) * 18;
                g.setColor(new Color(126, 190, 215, alpha));
                g.fillOval(x, y, i % 9 == 0 ? 3 : 2, i % 9 == 0 ? 3 : 2);
            }
        }

        private void drawGrid(Graphics2D g, int width, int height) {
            g.setStroke(new BasicStroke(1f));
            g.setColor(new Color(39, 81, 108, 38));
            for (int x = 0; x < width; x += 42) g.drawLine(x, 0, x, height);
            for (int y = 0; y < height; y += 42) g.drawLine(0, y, width, y);
            int horizon = (int) (height * 0.68);
            g.setColor(new Color(46, 137, 161, 36));
            for (int i = -9; i <= 9; i++) {
                int x = width / 2 + i * 46;
                g.drawLine(width / 2, horizon, x, height);
            }
            for (int i = 1; i <= 6; i++) {
                double t = i / 6.0;
                int y = horizon + (int) ((height - horizon) * t * t);
                g.drawLine(0, y, width, y);
            }
        }

        private void drawManifestField(Graphics2D g, int width, int height) {
            int cx = width / 2;
            int cy = (int) (height * 0.49);
            double scale = Math.min(width, height);
            double cpu = normalized(telemetry.cpuPercent);
            double ram = normalized(telemetry.memoryPercent);
            double gpu = normalized(telemetry.gpuPercent);
            double network = networkActivity();
            double[] signal = {cpu, ram, gpu, network};
            Color[] colors = {CPU_COLOR, RAM_COLOR, GPU_COLOR, NET_COLOR};
            double[] baseRadius = {0.19, 0.27, 0.35, 0.43};

            for (int channel = 0; channel < 4; channel++) {
                double channelActivity = activityFor(channel, cpu, ram, gpu, network);
                double radius = scale * (baseRadius[channel] + channelActivity * 0.045);
                int alpha = channel == GPU && telemetry.gpuPercent < 0.0 ? 25
                        : (int) (32 + signal[channel] * 88);
                g.setStroke(new BasicStroke(channel == 0 ? 1.4f : 1f,
                        BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND,
                        10f, channel % 2 == 0 ? null : new float[] {5f, 6f}, 0f));
                g.setColor(withAlpha(colors[channel], alpha));
                g.draw(new Ellipse2D.Double(cx - radius, cy - radius * 0.72,
                        radius * 2.0, radius * 1.44));
            }

            drawParticles(g, cx, cy, scale, signal, cpu, ram, gpu, network, colors);
            drawNetworkLinks(g, cx, cy, scale, network);
            drawManifestCore(g, cx, cy, scale, cpu, ram,
                    telemetry.gpuPercent >= 0.0 ? gpu : -1.0, network);
            drawCenterLabels(g, cx, cy, scale, cpu, ram, gpu, network);
        }

        private void drawParticles(Graphics2D g, int cx, int cy, double scale,
                                   double[] signal, double cpu, double ram,
                                   double gpu, double network, Color[] colors) {
            int visibleCount = Math.max(24, (int) (particles.length * particleScale));
            visibleCount = Math.min(visibleCount, particles.length);
            for (int i = 0; i < visibleCount; i++) {
                Particle particle = particles[i];
                double channelActivity = activityFor(particle.channel, cpu, ram, gpu, network);
                double layer = BASE_RADII[particle.channel];
                double radius = scale * (layer + particle.radius * 0.06
                        + (particle.channel == RAM ? ram * 0.05 : 0.0));
                double ovalY = radius * 0.72;
                double nowAngle = particle.angle + rotation * 0.12;
                double oldAngle = particle.previousAngle + rotation * 0.12;
                double x = cx + Math.cos(nowAngle) * radius;
                double y = cy + Math.sin(nowAngle) * ovalY + particle.elevation * scale * 0.035;
                double oldX = cx + Math.cos(oldAngle) * radius;
                double oldY = cy + Math.sin(oldAngle) * ovalY + particle.elevation * scale * 0.035;
                Color color = colors[particle.channel];
                int alpha = particle.channel == GPU && telemetry.gpuPercent < 0.0
                        ? 65 : (int) clamp(75 + channelActivity * 170, 75, 245);
                int streak = particle.channel == NET
                        ? 3 + (int) (network * 18.0) : 2 + (int) (channelActivity * 5.0);
                g.setStroke(new BasicStroke(Math.max(1f, streak / 5.0f),
                        BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
                g.setColor(withAlpha(color, alpha / 2));
                g.drawLine((int) oldX, (int) oldY, (int) x, (int) y);
                int size = particle.size + (int) (channelActivity * (particle.channel == GPU ? 5 : 3));
                g.setColor(withAlpha(color, alpha));
                g.fill(new Ellipse2D.Double(x - size / 2.0, y - size / 2.0, size, size));
            }
        }

        private void drawNetworkLinks(Graphics2D g, int cx, int cy, double scale, double activity) {
            double radius = scale * (0.44 + activity * 0.045);
            double angle = rotation * (0.25 + activity * 0.8);
            int ingressX = (int) (cx + Math.cos(angle) * radius);
            int ingressY = (int) (cy + Math.sin(angle) * radius * 0.72);
            int egressX = (int) (cx + Math.cos(angle + Math.PI) * radius);
            int egressY = (int) (cy + Math.sin(angle + Math.PI) * radius * 0.72);
            g.setStroke(new BasicStroke(1.5f));
            g.setColor(withAlpha(NET_COLOR, (int) (45 + activity * 165)));
            g.drawLine(ingressX, ingressY, cx, cy);
            g.drawLine(cx, cy, egressX, egressY);
            g.setColor(NET_COLOR);
            g.fillOval(ingressX - 4, ingressY - 4, 8, 8);
            g.fillOval(egressX - 4, egressY - 4, 8, 8);
        }

        private void drawManifestCore(Graphics2D g, int cx, int cy, double scale,
                                      double cpu, double ram, double gpu, double network) {
            double average = combinedActivity(cpu, ram, gpu, network);
            int radius = (int) (scale * (0.065 + average * 0.025)
                    * (1.0 + 0.05 * Math.sin(pulse)));
            g.setColor(new Color(0, 207, 240, 20));
            g.fill(new Ellipse2D.Double(cx - radius * 2.8, cy - radius * 2.8,
                    radius * 5.6, radius * 5.6));
            g.setStroke(new BasicStroke(1.6f));
            g.setColor(new Color(91, 218, 238, 115));
            g.draw(new Ellipse2D.Double(cx - radius * 1.7, cy - radius * 1.7,
                    radius * 3.4, radius * 3.4));

            Path2D core = new Path2D.Double();
            core.moveTo(cx, cy - radius);
            core.lineTo(cx + radius * 0.76, cy);
            core.lineTo(cx, cy + radius);
            core.lineTo(cx - radius * 0.76, cy);
            core.closePath();
            g.setColor(new Color(14, 57, 78, 238));
            g.fill(core);
            g.setColor(CPU_COLOR);
            g.draw(core);
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, Math.max(9, (int) (scale * 0.018))));
            g.setColor(TEXT);
            String label = "MANIFEST";
            g.drawString(label, cx - g.getFontMetrics().stringWidth(label) / 2, cy + 4);
        }

        private void drawCenterLabels(Graphics2D g, int cx, int cy, double scale,
                                      double cpu, double ram, double gpu, double network) {
            String[] labels = {
                    String.format("CPU %s", formatPercent(telemetry.cpuPercent)),
                    String.format("RAM %s", formatPercent(telemetry.memoryPercent)),
                    String.format("GPU %s", formatPercent(telemetry.gpuPercent)),
                    String.format("NET %s", formatRate(totalNetworkRate()))
            };
            Color[] colors = {CPU_COLOR, RAM_COLOR, GPU_COLOR, NET_COLOR};
            int[] x = {cx - (int) (scale * 0.39), cx + (int) (scale * 0.24),
                    cx + (int) (scale * 0.24), cx - (int) (scale * 0.39)};
            int[] y = {cy - (int) (scale * 0.22), cy - (int) (scale * 0.22),
                    cy + (int) (scale * 0.24), cy + (int) (scale * 0.24)};
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 10));
            for (int i = 0; i < labels.length; i++) {
                g.setColor(colors[i]);
                g.drawString(labels[i], x[i], y[i]);
            }
        }

        private void drawElementLabels(Graphics2D g, int width, int height) {
            g.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 9));
            int y = height - 19;
            int gap = Math.max(74, (width - 50) / ELEMENTS.length);
            int startX = (width - gap * (ELEMENTS.length - 1)) / 2;
            for (int i = 0; i < ELEMENTS.length; i++) {
                int x = startX + i * gap;
                g.setColor(new Color(25, 45, 62, 205));
                g.fillRoundRect(x - 23, y - 13, 58, 19, 8, 8);
                g.setColor(new Color(85, 131, 157, 190));
                g.drawRoundRect(x - 23, y - 13, 58, 19, 8, 8);
                g.setColor(MUTED);
                g.drawString(ELEMENTS[i], x - 13, y);
            }
        }

        private double totalNetworkRate() {
            if (telemetry.receivedBytesPerSecond < 0.0 || telemetry.sentBytesPerSecond < 0.0) return -1.0;
            return telemetry.receivedBytesPerSecond + telemetry.sentBytesPerSecond;
        }

        private void resetParticles() {
            rotation = 0.0;
            pulse = 0.0;
            for (Particle particle : particles) particle.reset(random);
            repaint();
        }

        private static Color withAlpha(Color color, int alpha) {
            return new Color(color.getRed(), color.getGreen(), color.getBlue(),
                    (int) clamp(alpha, 0, 255));
        }

        private static double combinedActivity(double cpu, double ram, double gpu, double network) {
            double total = cpu * 0.35 + ram * 0.25 + network * 0.15;
            double weights = 0.75;
            if (gpu >= 0.0) {
                total += gpu * 0.25;
                weights += 0.25;
            }
            return clamp(total / weights, 0.0, 1.0);
        }
    }

    private static final class Particle {
        private final int channel;
        private double angle;
        private double previousAngle;
        private double radius;
        private double elevation;
        private double speed;
        private int size;

        private Particle(int channel, Random random) {
            this.channel = channel;
            reset(random);
        }

        private void reset(Random random) {
            angle = random.nextDouble() * Math.PI * 2.0;
            previousAngle = angle;
            radius = 0.35 + random.nextDouble() * 0.85;
            elevation = (random.nextDouble() - 0.5) * 0.8;
            speed = 0.35 + random.nextDouble() * 0.85;
            size = 2 + random.nextInt(3);
        }

        private void advance(double activity, double network, Random random) {
            previousAngle = angle;
            double networkBoost = channel == ManifestCanvas.NET ? network * 0.018 : 0.0;
            angle += (0.004 + activity * 0.028 + networkBoost) * speed;
            angle += (random.nextDouble() - 0.5) * (0.001 + activity * 0.003);
            radius += (random.nextDouble() - 0.5) * 0.0025;
            radius = clamp(radius, 0.30, 1.22);
        }
    }

    private static double networkIntensity(double bytesPerSecond) {
        if (bytesPerSecond <= 0.0 || Double.isNaN(bytesPerSecond)) return 0.0;
        return clamp(Math.log1p(bytesPerSecond) / Math.log1p(100_000_000.0), 0.0, 1.0);
    }

    private static String formatPercent(double value) {
        return value >= 0.0 ? String.format("%.1f%%", value) : "N/A";
    }

    private static String formatRate(double bytesPerSecond) {
        if (bytesPerSecond < 0.0) return "N/A";
        if (bytesPerSecond < 1024.0) return String.format("%.0f B/s", bytesPerSecond);
        if (bytesPerSecond < 1024.0 * 1024.0) {
            return String.format("%.1f KB/s", bytesPerSecond / 1024.0);
        }
        return String.format("%.2f MB/s", bytesPerSecond / (1024.0 * 1024.0));
    }

    private static String formatBytes(long bytes) {
        if (bytes < 0L) return "N/A";
        double value = bytes;
        String[] units = {"B", "KB", "MB", "GB", "TB"};
        int unit = 0;
        while (value >= 1024.0 && unit < units.length - 1) {
            value /= 1024.0;
            unit++;
        }
        return unit == 0 ? String.format("%d %s", bytes, units[unit])
                : String.format("%.2f %s", value, units[unit]);
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
            // Use Swing's default theme when the system theme is unavailable.
        }
        SwingUtilities.invokeLater(() -> {
            GodSelfInteractEngine engine = new GodSelfInteractEngine();
            engine.setVisible(true);
        });
    }
}
