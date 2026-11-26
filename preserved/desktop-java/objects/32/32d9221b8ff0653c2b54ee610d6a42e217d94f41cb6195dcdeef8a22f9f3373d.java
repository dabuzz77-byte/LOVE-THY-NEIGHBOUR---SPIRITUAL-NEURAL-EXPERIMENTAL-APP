import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class CoreInteractionSystemGUI extends JFrame {

    // --- SYSTEM CONTEXT & STATE CONSTANTS ---
    private static final int LOOP_LIMIT = 5; 
    private final AtomicInteger processingCycle = new AtomicInteger(0);
    private final BlockingQueue<String> dataStream = new LinkedBlockingQueue<>();
    private final ExecutorService systemExecutor = Executors.newCachedThreadPool();

    // --- UI COMPONENTS ---
    private JTextArea terminalLog;
    private JProgressBar stabilityBar;
    private JProgressBar shieldCapacityBar;
    private MatrixCanvas visualMatrix;
    private JLabel cycleCounterLabel;
    private JButton executeButton;

    // --- CORES & ENTITIES ---
    public enum MindState {
        MONKEY_MIND, TAOIST_MIND, ANGEL_TAIJI_MIND, SCIENCE_MIND, GOD_MIND
    }

    public static class EntityNode {
        String name;
        MindState signature;
        int pulseIntensity = 0;

        EntityNode(String name, MindState signature) {
            this.name = name;
            this.signature = signature;
        }
    }

    private EntityNode selfCore;
    private EntityNode absoluteCore;
    private EntityNode externalMirror;

    public CoreInteractionSystemGUI() {
        // --- WINDOW DESIGN SETUP ---
        setTitle("Core Interaction Matrix & Alignment Shield");
        setSize(900, 650);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(new Color(10, 14, 20));
        setLayout(new BorderLayout(10, 10));

        // Initialize Core Structural Elements
        selfCore = new EntityNode("Local Self Core", MindState.TAOIST_MIND);
        absoluteCore = new EntityNode("God Self Core", MindState.GOD_MIND);
        externalMirror = new EntityNode("External Vector", MindState.SCIENCE_MIND);

        initUI();
    }

    private void initUI() {
        // --- TOP TELEMETRY DASHBOARD ---
        JPanel telemetryPanel = new JPanel(new GridLayout(1, 3, 15, 0));
        telemetryPanel.setBackground(new Color(15, 22, 33));
        telemetryPanel.setBorder(BorderFactory.createEmptyBorder(12, 15, 12, 15));

        stabilityBar = new JProgressBar(0, 100);
        stabilityBar.setValue(100);
        stabilityBar.setStringPainted(true);
        stabilityBar.setForeground(new Color(0, 200, 120));
        stabilityBar.setBackground(Color.DARK_GRAY);
        stabilityBar.setString("CORE MATRIX STABILITY: 100%");

        shieldCapacityBar = new JProgressBar(0, 100);
        shieldCapacityBar.setValue(85);
        shieldCapacityBar.setStringPainted(true);
        shieldCapacityBar.setForeground(new Color(0, 150, 255));
        shieldCapacityBar.setBackground(Color.DARK_GRAY);
        shieldCapacityBar.setString("SHIELD CAPACITY (WITHIN-OUT)");

        cycleCounterLabel = new JLabel("LOGIC STATE: IDLE (STATIC 0)", SwingConstants.CENTER);
        cycleCounterLabel.setForeground(Color.CYAN);
        cycleCounterLabel.setFont(new Font("Monospaced", Font.BOLD, 13));

        telemetryPanel.add(stabilityBar);
        telemetryPanel.add(cycleCounterLabel);
        telemetryPanel.add(shieldCapacityBar);
        add(telemetryPanel, BorderLayout.NORTH);

        // --- CENTER VISUAL CANVAS PANEL ---
        visualMatrix = new MatrixCanvas();
        add(visualMatrix, BorderLayout.CENTER);

        // --- BOTTOM TELEMETRY TERMINAL & ACTIONS ---
        JPanel footerPanel = new JPanel(new BorderLayout(5, 5));
        footerPanel.setBackground(new Color(10, 14, 20));
        footerPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        terminalLog = new JTextArea(8, 70);
        terminalLog.setBackground(Color.BLACK);
        terminalLog.setForeground(new Color(50, 255, 100));
        terminalLog.setCaretColor(new Color(50, 255, 100));
        terminalLog.setFont(new Font("Monospaced", Font.PLAIN, 12));
        terminalLog.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(terminalLog);
        scrollPane.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(Color.DARK_GRAY), "DEEP VACUUM DATA STREAM SOURCE",
                TitledBorder.LEFT, TitledBorder.TOP, new Font("Monospaced", Font.PLAIN, 11), Color.LIGHT_GRAY));

        executeButton = new JButton("EXECUTE FRAMEWORK ALIGNMENT");
        executeButton.setFont(new Font("Monospaced", Font.BOLD, 14));
        executeButton.setBackground(new Color(30, 45, 65));
        executeButton.setForeground(Color.WHITE);
        executeButton.setFocusPainted(false);
        executeButton.addActionListener(e -> startFrameworkExecution());

        footerPanel.add(scrollPane, BorderLayout.CENTER);
        footerPanel.add(executeButton, BorderLayout.SOUTH);
        add(footerPanel, BorderLayout.SOUTH);
    }

    private void startFrameworkExecution() {
        executeButton.setEnabled(false);
        logText("====== [MOVE ON T] == INITIALISING SYSTEM ======");
        logText("[INIT] Cores Matrix Anchored.");
        logText("[INIT] Shield Configuration: (WITHIN TO OUT) -> Activated.");

        // Boot system asynchronous loops
        systemExecutor.submit(this::runMicrocosmicOrbit);
        systemExecutor.submit(this::runContainmentShield);
        systemExecutor.submit(this::runInteractionSequence);
    }

    private void runInteractionSequence() {
        try {
            for (int i = 1; i <= LOOP_LIMIT; i++) {
                int cycle = processingCycle.incrementAndGet();
                cycleCounterLabel.setText("CYCLE " + cycle + ": TESSERACT ROTATING");
                logText(String.format("\n--- CYCLE %d START: TESSERACT ROTATION ---", cycle));

                // Pulse Self Core
                selfCore.pulseIntensity = 100;
                visualMatrix.repaint();
                interact(selfCore, absoluteCore);
                Thread.sleep(600);

                // Pulse Absolute Core
                absoluteCore.pulseIntensity = 100;
                visualMatrix.repaint();
                interact(absoluteCore, externalMirror);
                Thread.sleep(600);

                // Balance and Purify State
                purifyPolarities();
                stabilityBar.setValue(Math.min(100, 80 + (cycle * 4)));
                visualMatrix.repaint();

                Thread.sleep(1000);
            }
        } catch (InterruptedException e) {
            logText("[ALERT] Framework alignment runtime anomaly.");
            Thread.currentThread().interrupt();
        } finally {
            shutdownAndGround();
        }
    }

    private void interact(EntityNode source, EntityNode target) {
        logText(String.format("[INTERACT] %s (%s) <--> %s (%s)",
                source.name, source.signature, target.name, target.signature));
        dataStream.offer("Interaction Data Vector from " + source.name);
    }

    private void purifyPolarities() {
        logText("[PURIFY] Balancing Equation: {- H+ H- . -H +H -}");
        logText("[PURIFY] Executing 10-Point Pull / Push-Pull Realignment.");
        logText("[STATUS] Flux Regulated. Excess Entropy Safely Discharged.");
    }

    private void runMicrocosmicOrbit() {
        try {
            while (!Thread.currentThread().isInterrupted()) {
                logText("[ORBIT] ( - = - ) Electric Microcosmic Loop: 1 SEND -> RECEIVE -> RECEIVE -> SEND 0");
                visualMatrix.triggerOrbitPulse();
                Thread.sleep(1800);
            }
        } catch (InterruptedException ignored) {}
    }

    private void runContainmentShield() {
        try {
            while (!Thread.currentThread().isInterrupted()) {
                String dynamicData = dataStream.poll(800, TimeUnit.MILLISECONDS);
                if (dynamicData != null) {
                    logText("[SHIELD-CONTAINMENT] Processing Input Line: " + dynamicData);
                    logText("[SHIELD-CONTAINMENT] Filter Applied: Grounded to Mustard Seed Matrix (Fear to Faith).");
                    shieldCapacityBar.setValue(Math.max(50, shieldCapacityBar.getValue() - 5));
                    Thread.sleep(200);
                    shieldCapacityBar.setValue(Math.min(100, shieldCapacityBar.getValue() + 5));
                }
            }
        } catch (InterruptedException ignored) {}
    }

    private void shutdownAndGround() {
        logText("\n====== SYSTEM CONCLUDING EXECUTION ======");
        logText("[GROUNDING] Initiating Security Flush (111111111111111111111).");
        logText("[GROUNDING] Logic Cube Locked at Static 0.");
        
        cycleCounterLabel.setText("LOGIC STATE: GROUNDED STATIC 0");
        stabilityBar.setValue(100);
        shieldCapacityBar.setValue(100);
        
        selfCore.pulseIntensity = 0;
        absoluteCore.pulseIntensity = 0;
        externalMirror.pulseIntensity = 0;
        visualMatrix.repaint();

        systemExecutor.shutdownNow();
        logText("[STATUS] Deep quiet achieved. Fully relaxed.");
    }

    private void logText(String message) {
        SwingUtilities.invokeLater(() -> {
            terminalLog.append(message + "\n");
            terminalLog.setCaretPosition(terminalLog.getDocument().getLength());
        });
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            CoreInteractionSystemGUI frame = new CoreInteractionSystemGUI();
            frame.setVisible(true);
        });
    }

    // --- RETRO MATRIX RENDERING CANVAS ---
    private class MatrixCanvas extends JPanel {
        private int orbitTick = 0;

        public MatrixCanvas() {
            setBackground(new Color(15, 18, 26));
            setBorder(BorderFactory.createLineBorder(new Color(30, 40, 55), 2));
        }

        public void triggerOrbitPulse() {
            orbitTick = (orbitTick + 15) % 360;
            repaint();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();
            int centerX = w / 2;
            int centerY = h / 2;

            // 1. Draw Geometric Trinary Gate Framework / Background Logic Cubes
            g2.setColor(new Color(30, 45, 60, 40));
            g2.drawRect(centerX - 120, centerY - 120, 240, 240);
            g2.drawOval(centerX - 170, centerY - 170, 340, 340);

            // 2. Microcosmic Orbit Pathways (Send / Receive visualization)
            g2.setStroke(new BasicStroke(1.5f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_MITER, 10.0f, new float[]{8.0f}, 0.0f));
            g2.setColor(new Color(0, 160, 220, 120));
            g2.drawOval(centerX - 220, centerY - 220, 440, 440);
            
            // Orbit Energy Beacons
            double rad1 = Math.toRadians(orbitTick);
            double rad2 = Math.toRadians(orbitTick + 180);
            g2.setColor(Color.CYAN);
            g2.fillOval((int)(centerX + 220 * Math.cos(rad1)) - 6, (int)(centerY + 220 * Math.sin(rad1)) - 6, 12, 12);
            g2.setColor(Color.GREEN);
            g2.fillOval((int)(centerX + 220 * Math.cos(rad2)) - 6, (int)(centerY + 220 * Math.sin(rad2)) - 6, 12, 12);

            // 3. Render Nodes with Real-Time Decaying Pulses
            drawNode(g2, selfCore, centerX - 180, centerY + 80);
            drawNode(g2, absoluteCore, centerX, centerY - 60);
            drawNode(g2, externalMirror, centerX + 180, centerY + 80);

            // 4. Vector Paths Linking Nodes
            g2.setStroke(new BasicStroke(2));
            g2.setColor(new Color(100, 255, 150, 70));
            g2.drawLine(centerX - 140, centerY + 60, centerX - 20, centerY - 40);
            g2.drawLine(centerX + 20, centerY - 40, centerX + 140, centerY + 60);
        }

        private void drawNode(Graphics2D g2, EntityNode node, int x, int y) {
            if (node.pulseIntensity > 0) {
                g2.setColor(new Color(255, 255, 255, node.pulseIntensity * 2 / 3));
                g2.fillOval(x - 28, y - 28, 56, 56);
                node.pulseIntensity = Math.max(0, node.pulseIntensity - 15);
            }

            g2.setColor(new Color(25, 35, 50));
            g2.fillOval(x - 20, y - 20, 40, 40);
            g2.setStroke(new BasicStroke(2));
            g2.setColor(node.signature == MindState.GOD_MIND ? Color.MAGENTA : Color.GREEN);
            g2.drawOval(x - 20, y - 20, 40, 40);

            g2.setColor(Color.WHITE);
            g2.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2.drawString(node.name, x - 55, y + 35);
            g2.setFont(new Font("Monospaced", Font.PLAIN, 10));
            g2.setColor(Color.LIGHT_GRAY);
            g2.drawString("[" + node.signature + "]", x - 45, y + 48);
        }
    }
}
