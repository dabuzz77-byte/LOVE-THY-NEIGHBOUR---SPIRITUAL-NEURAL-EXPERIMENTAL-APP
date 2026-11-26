import com.sun.management.OperatingSystemMXBean;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JProgressBar;
import javax.swing.JSlider;
import javax.swing.SwingConstants;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
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
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.GridLayout;
import java.awt.RenderingHints;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Path2D;
import java.lang.management.ManagementFactory;
import java.util.Random;

/** Visual CPU activity monitor with a controllable random component. */
public final class AllPrevUnifiedEngine extends JFrame {
    private static final Color BACKGROUND = new Color(7, 12, 22);
    private static final Color PANEL = new Color(15, 24, 38);
    private static final Color PANEL_EDGE = new Color(40, 65, 91);
    private static final Color TEXT = new Color(228, 239, 250);
    private static final Color MUTED = new Color(137, 160, 183);
    private static final Color CYAN = new Color(67, 220, 239);
    private static final Color GREEN = new Color(110, 235, 165);
    private static final Color AMBER = new Color(255, 183, 91);

    private final ActivityCanvas canvas = new ActivityCanvas();
    private final JLabel cpuReadout = new JLabel("CPU: sampling…");
    private final JLabel mixReadout = new JLabel("MIXED ACTIVITY: —");
    private final JLabel randomMixLabel = new JLabel("Random influence: 15%");
    private final JProgressBar cpuBar = new JProgressBar(0, 100);
    private final JProgressBar mixedBar = new JProgressBar(0, 100);
    private final JSlider randomMixSlider = new JSlider(0, 50, 15);
    private final JButton pauseButton = new JButton("Pause animation");
    private final JButton resetButton = new JButton("Reset view");

    private final Random random = new Random();
    private final Timer animationTimer;
    private final Timer cpuTimer;
    private double cpuLoad = -1.0;
    private double mixedActivity = 0.16;
    private double randomInfluence = 0.15;
    private boolean animationPaused;

    public AllPrevUnifiedEngine() {
        super("AllPrev Unified Engine | CPU Flux Visualizer");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(980, 680));
        setSize(1280, 860);
        setLocationRelativeTo(null);

        JPanel root = new JPanel(new BorderLayout(12, 12));
        root.setBackground(BACKGROUND);
        root.setBorder(new EmptyBorder(15, 18, 14, 18));
        setContentPane(root);
        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildVisualization(), BorderLayout.CENTER);
        root.add(buildControls(), BorderLayout.SOUTH);

        animationTimer = new Timer(33, event -> {
            canvas.advance(mixedActivity);
            canvas.repaint();
        });
        cpuTimer = new Timer(750, event -> sampleCpu());
        animationTimer.start();
        cpuTimer.start();
        sampleCpu();
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout(12, 0));
        header.setOpaque(false);
        JPanel titleBlock = new JPanel(new GridLayout(2, 1, 0, 4));
        titleBlock.setOpaque(false);
        JLabel title = new JLabel("ALLPREV  /  UNIFIED FLUX ENGINE");
        title.setForeground(TEXT);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 21));
        JLabel subtitle = new JLabel(
                "Live system CPU utilization drives the orbit; adjustable randomness adds controlled variation.");
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        titleBlock.add(title);
        titleBlock.add(subtitle);

        JLabel liveBadge = new JLabel(" LIVE TELEMETRY ", SwingConstants.CENTER);
        liveBadge.setForeground(GREEN);
        liveBadge.setFont(new Font(Font.MONOSPACED, Font.BOLD, 11));
        liveBadge.setOpaque(true);
        liveBadge.setBackground(new Color(18, 49, 45));
        liveBadge.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(45, 118, 100)),
                new EmptyBorder(7, 10, 7, 10)));
        header.add(titleBlock, BorderLayout.CENTER);
        header.add(liveBadge, BorderLayout.EAST);
        return header;
    }

    private JPanel buildVisualization() {
        JPanel frame = new JPanel(new BorderLayout());
        frame.setBackground(PANEL);
        frame.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(PANEL_EDGE),
                new EmptyBorder(1, 1, 1, 1)));
        canvas.setPreferredSize(new Dimension(1000, 540));
        frame.add(canvas, BorderLayout.CENTER);
        return frame;
    }

    private JPanel buildControls() {
        JPanel controls = new JPanel(new GridBagLayout());
        controls.setBackground(PANEL);
        controls.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(PANEL_EDGE),
                new EmptyBorder(10, 12, 10, 12)));
        GridBagConstraints c = new GridBagConstraints();
        c.fill = GridBagConstraints.HORIZONTAL;
        c.gridy = 0;
        c.weightx = 0;
        c.gridx = 0;
        c.insets.set(2, 4, 2, 12);
        cpuReadout.setForeground(CYAN);
        cpuReadout.setFont(new Font(Font.MONOSPACED, Font.BOLD, 12));
        controls.add(cpuReadout, c);

        c.gridx = 1;
        c.weightx = 0.30;
        styleProgress(cpuBar, CYAN);
        controls.add(cpuBar, c);

        c.gridx = 2;
        c.weightx = 0;
        mixReadout.setForeground(GREEN);
        mixReadout.setFont(new Font(Font.MONOSPACED, Font.BOLD, 12));
        controls.add(mixReadout, c);

        c.gridx = 3;
        c.weightx = 0.30;
        styleProgress(mixedBar, GREEN);
        controls.add(mixedBar, c);

        c.gridx = 4;
        c.weightx = 0;
        randomMixLabel.setForeground(AMBER);
        randomMixLabel.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        controls.add(randomMixLabel, c);

        c.gridx = 5;
        c.weightx = 0.30;
        randomMixSlider.setOpaque(false);
        randomMixSlider.setMajorTickSpacing(25);
        randomMixSlider.setPaintTicks(true);
        randomMixSlider.setToolTipText("Set how much random variation is blended with measured CPU load.");
        randomMixSlider.addChangeListener(event -> {
            randomInfluence = randomMixSlider.getValue() / 100.0;
            randomMixLabel.setText("Random influence: " + randomMixSlider.getValue() + "%");
            canvas.setRandomInfluence(randomInfluence);
        });
        controls.add(randomMixSlider, c);

        c.gridx = 6;
        c.weightx = 0;
        c.insets.set(2, 8, 2, 4);
        pauseButton.setForeground(TEXT);
        pauseButton.setBackground(new Color(27, 43, 61));
        pauseButton.setFocusPainted(false);
        pauseButton.addActionListener(event -> toggleAnimation());
        resetButton.setForeground(TEXT);
        resetButton.setBackground(new Color(27, 43, 61));
        resetButton.setFocusPainted(false);
        resetButton.addActionListener(event -> canvas.resetMotion());
        JPanel actions = new JPanel(new GridLayout(1, 2, 6, 0));
        actions.setOpaque(false);
        actions.add(pauseButton);
        actions.add(resetButton);
        controls.add(actions, c);

        JLabel note = new JLabel(
                "CPU load is an OS utilization estimate; random influence is mixed into the animation signal. No kernel instructions are read.");
        note.setForeground(MUTED);
        note.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        c.gridx = 0;
        c.gridy = 1;
        c.gridwidth = 7;
        c.weightx = 1;
        c.insets.set(6, 4, 0, 4);
        controls.add(note, c);
        return controls;
    }

    private void styleProgress(JProgressBar bar, Color color) {
        bar.setStringPainted(true);
        bar.setForeground(color);
        bar.setBackground(new Color(8, 15, 26));
        bar.setBorder(BorderFactory.createLineBorder(new Color(43, 62, 82)));
        bar.setPreferredSize(new Dimension(120, 20));
    }

    private void sampleCpu() {
        double reading = -1.0;
        try {
            java.lang.management.OperatingSystemMXBean bean =
                    ManagementFactory.getOperatingSystemMXBean();
            if (bean instanceof OperatingSystemMXBean) {
                double value = ((OperatingSystemMXBean) bean).getSystemCpuLoad();
                if (value >= 0.0 && value <= 1.0) reading = value;
            }
        } catch (RuntimeException ignored) {
            // CPU utilization is optional on some JVM and operating-system combinations.
        }

        cpuLoad = reading;
        double measured = cpuLoad >= 0.0 ? cpuLoad : 0.12;
        double randomSample = random.nextDouble();
        double blended = measured * (1.0 - randomInfluence)
                + randomSample * randomInfluence;
        mixedActivity = clamp(mixedActivity * 0.58 + blended * 0.42, 0.0, 1.0);

        if (cpuLoad >= 0.0) {
            int percent = (int) Math.round(cpuLoad * 100.0);
            cpuReadout.setText(String.format("CPU: %3d%%", percent));
            cpuBar.setValue(percent);
            cpuBar.setString(percent + "% measured");
        } else {
            cpuReadout.setText("CPU: unavailable");
            cpuBar.setValue(0);
            cpuBar.setString("no OS reading");
        }
        int mixedPercent = (int) Math.round(mixedActivity * 100.0);
        mixReadout.setText(String.format("MIXED: %3d%%", mixedPercent));
        mixedBar.setValue(mixedPercent);
        mixedBar.setString(mixedPercent + "% flux");
        canvas.recordCpuSample(cpuLoad);
        canvas.setSignal(mixedActivity, randomInfluence);
    }

    private void toggleAnimation() {
        animationPaused = !animationPaused;
        if (animationPaused) {
            animationTimer.stop();
            pauseButton.setText("Resume animation");
        } else {
            animationTimer.start();
            pauseButton.setText("Pause animation");
        }
    }

    private static double clamp(double value, double minimum, double maximum) {
        return Math.max(minimum, Math.min(maximum, value));
    }

    private static final class ActivityCanvas extends JPanel {
        private final Random random = new Random();
        private final Particle[] particles = new Particle[96];
        private final MatrixColumn[] matrixColumns = new MatrixColumn[26];
        private final double[] cpuHistory = new double[120];
        private double rotation;
        private double activity = 0.16;
        private double randomInfluence = 0.15;
        private int historyPosition;
        private int historyCount;

        private ActivityCanvas() {
            setOpaque(true);
            setBackground(BACKGROUND);
            java.util.Arrays.fill(cpuHistory, -1.0);
            for (int i = 0; i < particles.length; i++) particles[i] = new Particle(random);
            for (int i = 0; i < matrixColumns.length; i++) matrixColumns[i] = new MatrixColumn(random);
        }

        private void setSignal(double activity, double randomInfluence) {
            this.activity = clamp(activity, 0.0, 1.0);
            this.randomInfluence = clamp(randomInfluence, 0.0, 0.5);
        }

        private void setRandomInfluence(double randomInfluence) {
            this.randomInfluence = clamp(randomInfluence, 0.0, 0.5);
            repaint();
        }

        private void recordCpuSample(double cpu) {
            cpuHistory[historyPosition] = cpu;
            historyPosition = (historyPosition + 1) % cpuHistory.length;
            historyCount = Math.min(historyCount + 1, cpuHistory.length);
        }

        private void advance(double activity) {
            this.activity = clamp(activity, 0.0, 1.0);
            rotation = (rotation + 0.004 + this.activity * 0.020) % (Math.PI * 2.0);
            double noise = 0.0015 + randomInfluence * 0.012 + this.activity * 0.003;
            for (Particle particle : particles) particle.advance(this.activity, noise, random);
            for (MatrixColumn column : matrixColumns) column.advance(this.activity);
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
            int width = getWidth();
            int height = getHeight();
            g.setPaint(new GradientPaint(0, 0, new Color(9, 19, 32),
                    0, height, new Color(4, 8, 17)));
            g.fillRect(0, 0, width, height);

            drawMatrixField(g, width, height);
            drawPerspectiveGrid(g, width, height);
            drawOrbitSystem(g, width, height);
            drawCpuGraph(g, width, height);
            drawTelemetry(g);
            g.dispose();
        }

        private void drawMatrixField(Graphics2D g, int width, int height) {
            g.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 11));
            for (MatrixColumn column : matrixColumns) {
                int x = (int) (column.x * width);
                int startY = (int) (column.y * height);
                for (int i = 0; i < column.glyphs.length; i++) {
                    int y = startY + i * 15;
                    if (y < 20 || y > height - 20) continue;
                    int alpha = i == 0 ? 115 : Math.max(12, 65 - i * 2);
                    g.setColor(i == 0 ? new Color(75, 231, 200, alpha)
                            : new Color(43, 171, 148, alpha));
                    g.drawString(column.glyphs[i], x, y);
                }
            }
        }

        private void drawPerspectiveGrid(Graphics2D g, int width, int height) {
            int horizon = (int) (height * 0.57);
            g.setStroke(new BasicStroke(1f));
            g.setColor(new Color(56, 119, 150, 34));
            for (int x = 0; x < width; x += 48) g.drawLine(x, 0, x, height);
            for (int y = 24; y < height; y += 38) g.drawLine(0, y, width, y);

            g.setColor(new Color(52, 177, 201, 42));
            for (int i = -10; i <= 10; i++) {
                int x = width / 2 + i * 48;
                g.drawLine(width / 2, horizon, x, height);
            }
            for (int i = 1; i <= 8; i++) {
                double t = i / 8.0;
                int y = horizon + (int) ((height - horizon) * t * t);
                g.drawLine(0, y, width, y);
            }
            g.setColor(new Color(71, 210, 223, 70));
            g.drawLine(0, horizon, width, horizon);
        }

        private void drawOrbitSystem(Graphics2D g, int width, int height) {
            int cx = (int) (width * 0.48);
            int cy = (int) (height * 0.45);
            double scale = Math.min(width, height);
            double pulse = 1.0 + activity * 0.11;
            double radiusX = scale * 0.27 * pulse;
            double radiusY = scale * 0.17 * pulse;

            g.setStroke(new BasicStroke(1.1f));
            g.setColor(new Color(94, 169, 223, 70));
            g.draw(new Ellipse2D.Double(cx - radiusX, cy - radiusY,
                    radiusX * 2.0, radiusY * 2.0));
            java.awt.geom.AffineTransform original = g.getTransform();
            g.rotate(Math.PI / 3.0, cx, cy);
            g.setColor(new Color(66, 211, 219, 55));
            g.draw(new Ellipse2D.Double(cx - radiusX * 0.93, cy - radiusY * 0.68,
                    radiusX * 1.86, radiusY * 1.36));
            g.rotate(-Math.PI * 2.0 / 3.0, cx, cy);
            g.setColor(new Color(189, 130, 255, 50));
            g.draw(new Ellipse2D.Double(cx - radiusX * 0.82, cy - radiusY * 0.56,
                    radiusX * 1.64, radiusY * 1.12));
            g.setTransform(original);

            g.setColor(new Color(154, 186, 208, 44));
            g.drawLine(cx, cy - (int) (scale * 0.31), cx, cy + (int) (scale * 0.31));
            g.drawLine(cx - (int) (scale * 0.34), cy, cx + (int) (scale * 0.34), cy);

            drawParticleCloud(g, cx, cy, radiusX, radiusY);
            drawOrbitNodes(g, cx, cy, radiusX, radiusY);
            drawCore(g, cx, cy, scale);
        }

        private void drawParticleCloud(Graphics2D g, int cx, int cy,
                                       double radiusX, double radiusY) {
            for (Particle particle : particles) {
                double angle = particle.angle + rotation * particle.orbitDirection;
                double x = cx + Math.cos(angle) * radiusX * particle.radius;
                double y = cy + Math.sin(angle) * radiusY * particle.radius
                        + particle.elevation * radiusY * 0.42;
                int alpha = (int) clamp(75 + activity * 120, 75, 195);
                int size = particle.size;
                g.setColor(particle.accent
                        ? new Color(88, 223, 235, alpha)
                        : new Color(180, 153, 255, alpha - 25));
                g.fill(new Ellipse2D.Double(x - size / 2.0, y - size / 2.0, size, size));
            }
        }

        private void drawOrbitNodes(Graphics2D g, int cx, int cy,
                                    double radiusX, double radiusY) {
            double angle = rotation * (0.55 + activity * 1.35);
            int sendX = (int) (cx + radiusX * Math.cos(angle));
            int sendY = (int) (cy + radiusY * Math.sin(angle));
            int receiveX = (int) (cx + radiusX * Math.cos(angle + Math.PI));
            int receiveY = (int) (cy + radiusY * Math.sin(angle + Math.PI));
            g.setStroke(new BasicStroke(1.4f));
            g.setColor(new Color(80, 202, 245, 125));
            g.drawLine(sendX, sendY, receiveX, receiveY);
            drawGlowingNode(g, sendX, sendY, CYAN, 10 + (int) (activity * 5));
            drawGlowingNode(g, receiveX, receiveY, AMBER, 10 + (int) (activity * 5));
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 11));
            g.setColor(new Color(178, 244, 249));
            g.drawString("SEND", sendX + 13, sendY - 10);
            g.setColor(new Color(255, 214, 166));
            g.drawString("RECEIVE", receiveX + 13, receiveY - 10);
        }

        private void drawGlowingNode(Graphics2D g, int x, int y, Color color, int size) {
            g.setColor(new Color(color.getRed(), color.getGreen(), color.getBlue(), 32));
            g.fill(new Ellipse2D.Double(x - size * 1.6, y - size * 1.6, size * 3.2, size * 3.2));
            g.setColor(new Color(color.getRed(), color.getGreen(), color.getBlue(), 90));
            g.fill(new Ellipse2D.Double(x - size, y - size, size * 2.0, size * 2.0));
            g.setColor(color);
            g.fill(new Ellipse2D.Double(x - size * 0.45, y - size * 0.45,
                    size * 0.9, size * 0.9));
        }

        private void drawCore(Graphics2D g, int cx, int cy, double scale) {
            double radius = scale * (0.047 + activity * 0.012);
            int r = (int) radius;
            g.setColor(new Color(49, 175, 210, 22));
            g.fill(new Ellipse2D.Double(cx - r * 2.4, cy - r * 2.4, r * 4.8, r * 4.8));
            g.setColor(new Color(70, 210, 235, 68));
            g.setStroke(new BasicStroke(1.4f));
            g.draw(new Ellipse2D.Double(cx - r * 1.55, cy - r * 1.55, r * 3.1, r * 3.1));

            Path2D diamond = new Path2D.Double();
            diamond.moveTo(cx, cy - r);
            diamond.lineTo(cx + r * 0.78, cy);
            diamond.lineTo(cx, cy + r);
            diamond.lineTo(cx - r * 0.78, cy);
            diamond.closePath();
            g.setColor(new Color(30, 94, 126, 205));
            g.fill(diamond);
            g.setColor(CYAN);
            g.draw(diamond);
            g.setColor(TEXT);
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 10));
            g.drawString(String.format("%.0f%%", activity * 100.0), cx - 15, cy + 4);
        }

        private void drawCpuGraph(Graphics2D g, int width, int height) {
            int graphWidth = Math.min(250, Math.max(190, width / 4));
            int graphHeight = 92;
            int x = width - graphWidth - 22;
            int y = height - graphHeight - 18;
            g.setColor(new Color(5, 12, 22, 220));
            g.fillRoundRect(x, y, graphWidth, graphHeight, 9, 9);
            g.setColor(new Color(57, 91, 115, 180));
            g.drawRoundRect(x, y, graphWidth, graphHeight, 9, 9);
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 9));
            g.setColor(MUTED);
            g.drawString("CPU HISTORY  /  ~90 SEC", x + 9, y + 14);

            int plotX = x + 9;
            int plotY = y + 22;
            int plotWidth = graphWidth - 18;
            int plotHeight = graphHeight - 31;
            g.setColor(new Color(62, 91, 112, 100));
            for (int i = 1; i <= 3; i++) {
                int gy = plotY + plotHeight * i / 4;
                g.drawLine(plotX, gy, plotX + plotWidth, gy);
            }
            if (historyCount < 2) return;

            int oldest = historyCount == cpuHistory.length ? historyPosition : 0;
            int previousX = -1;
            int previousY = -1;
            g.setStroke(new BasicStroke(1.8f));
            g.setColor(CYAN);
            for (int i = 0; i < historyCount; i++) {
                double value = cpuHistory[(oldest + i) % cpuHistory.length];
                if (value < 0.0) {
                    previousX = -1;
                    continue;
                }
                int pointX = plotX + (historyCount <= 1 ? 0 : i * plotWidth / (historyCount - 1));
                int pointY = plotY + plotHeight - (int) (value * plotHeight);
                if (previousX >= 0) g.drawLine(previousX, previousY, pointX, pointY);
                g.fill(new Ellipse2D.Double(pointX - 1.7, pointY - 1.7, 3.4, 3.4));
                previousX = pointX;
                previousY = pointY;
            }
        }

        private void drawTelemetry(Graphics2D g) {
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 11));
            g.setColor(new Color(220, 238, 247, 220));
            g.drawString("MEASURED CPU + STOCHASTIC FLUX", 18, 25);
            g.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 10));
            g.setColor(new Color(152, 179, 199, 205));
            double cpu = latestCpu();
            String cpuText = cpu >= 0.0 ? String.format("CPU %.1f%%", cpu * 100.0) : "CPU n/a";
            g.drawString(String.format("%s   RANDOM %.0f%%   MIX %.1f%%",
                    cpuText, randomInfluence * 100.0, activity * 100.0), 18, 43);
            g.setColor(new Color(133, 164, 185, 150));
            g.drawString("Signal is CPU utilization blended with a random sample.", 18, 61);
        }

        private double latestCpu() {
            if (historyCount == 0) return Double.NaN;
            return cpuHistory[(historyPosition - 1 + cpuHistory.length) % cpuHistory.length];
        }

        private void resetMotion() {
            rotation = 0.0;
            for (Particle particle : particles) particle.reset(random);
            for (MatrixColumn column : matrixColumns) column.reset(random);
            repaint();
        }
    }

    private static final class Particle {
        private double angle;
        private double radius;
        private double elevation;
        private double speed;
        private double orbitDirection;
        private int size;
        private boolean accent;

        private Particle(Random random) {
            reset(random);
        }

        private void reset(Random random) {
            angle = random.nextDouble() * Math.PI * 2.0;
            radius = 0.34 + random.nextDouble() * 0.72;
            elevation = (random.nextDouble() - 0.5) * 1.1;
            speed = 0.35 + random.nextDouble() * 0.9;
            orbitDirection = random.nextBoolean() ? 1.0 : -1.0;
            size = random.nextInt(3) + 2;
            accent = random.nextBoolean();
        }

        private void advance(double activity, double noise, Random random) {
            angle += orbitDirection * speed * (0.12 + activity * 0.65) * 0.035;
            angle += (random.nextDouble() - 0.5) * noise;
            radius += (random.nextDouble() - 0.5) * noise * 0.18;
            radius = clamp(radius, 0.28, 1.08);
            elevation = clamp(elevation + (random.nextDouble() - 0.5) * noise * 0.08,
                    -0.62, 0.62);
        }
    }

    private static final class MatrixColumn {
        private double x;
        private double y;
        private double speed;
        private String[] glyphs;

        private MatrixColumn(Random random) {
            reset(random);
        }

        private void reset(Random random) {
            x = random.nextDouble();
            y = random.nextDouble();
            speed = 0.00045 + random.nextDouble() * 0.0011;
            int length = 8 + random.nextInt(16);
            glyphs = new String[length];
            for (int i = 0; i < glyphs.length; i++) {
                glyphs[i] = random.nextBoolean() ? "1" : "0";
            }
        }

        private void advance(double activity) {
            y += speed * (0.35 + activity * 1.8);
            if (y > 1.12) y = -glyphs.length * 0.018;
        }
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
            // Use Swing's default appearance when the system theme is unavailable.
        }
        SwingUtilities.invokeLater(() -> {
            AllPrevUnifiedEngine engine = new AllPrevUnifiedEngine();
            engine.setVisible(true);
        });
    }
}
