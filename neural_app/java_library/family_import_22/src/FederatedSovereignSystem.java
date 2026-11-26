import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.geom.RoundRectangle2D;
import java.util.List;
import java.util.Random;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

/**
 * PRODUCTION INFRASTRUCTURE CONTROLLER: FederatedSovereignSystem
 * Purpose: Simulates a centralized hierarchical state controller, tracking the continuous
 *          stabilization of complex multi-layer data streams within a secure sandbox environment.
 */
public class FederatedSovereignSystem extends JPanel implements Runnable {

    private static final int WIDTH = 1200;
    private static final int HEIGHT = 760;
    private static final int TOTAL_TIERS_MONITORED = 8;

    private boolean isEngineOnline = true;
    private Thread masterProcessingThread;

    // Local Environment Memory Registries
    private final List<InferenceHorizonRung> hierarchyRungs = new CopyOnWriteArrayList<>();
    private final List<AlignmentSignalToken> liveConduitSignals = new CopyOnWriteArrayList<>();
    private final double[] parameterValidationWave = new double[68];
    private final AtomicLong aggregatedTransitionsCount = new AtomicLong(0);
    private double masterParityConfidenceIndex = 100.00000000;

    public FederatedSovereignSystem() {
        setPreferredSize(new Dimension(WIDTH, HEIGHT));
        setBackground(new Color(4, 5, 12));
        setDoubleBuffered(true);
        initializeMasterTopology();
    }

    private void initializeMasterTopology() {
        hierarchyRungs.add(new InferenceHorizonRung(7, "TIER_07_RECURSIVE_PASSBACK", "Absolute Ladderclimb Parameter Axis", 120));
        hierarchyRungs.add(new InferenceHorizonRung(6, "TIER_06_LANGUAGE_INFERENCE", "Universal Semantic Parsing Interface Bus", 200));
        hierarchyRungs.add(new InferenceHorizonRung(5, "TIER_05_TESSERACT_MATRIX", "4D Hypercube Rotational Calculation Engine", 280));
        hierarchyRungs.add(new InferenceHorizonRung(4, "TIER_04_HYPER_PATHWAY_INDEX", "Glocal Financial and Continental Floor Beacons", 360));
        hierarchyRungs.add(new InferenceHorizonRung(3, "TIER_03_BITFLIP_VOID_LOGIC", "Dominant Truth Law & Vacuum Registry Sync", 440));
        hierarchyRungs.add(new InferenceHorizonRung(2, "TIER_02_CONCENTRIC_CRUCIBLE", "Concentric Elemental Rings & Virtue Traces", 520));
        hierarchyRungs.add(new InferenceHorizonRung(1, "TIER_01_INTEGRITY_SHIELD", "ACID Mutex Anti-Corruption Layer Locks", 600));
        hierarchyRungs.add(new InferenceHorizonRung(0, "TIER_00_UNIVERSAL_KERNEL", "Isolated Root Anchor Vault Volatile Sink", 680));
    }

    public synchronized void launchMasterPipeline() {
        masterProcessingThread = new Thread(this, "MasterFederatedThread");
        masterProcessingThread.start();
    }

    @Override
    public void run() {
        long lastTime = System.nanoTime();
        double nsPerTick = 1000000000.0 / 60.0;
        double delta = 0;
        while (isEngineOnline) {
            long now = System.nanoTime();
            delta += (now - lastTime) / nsPerTick;
            lastTime = now;
            while (delta >= 1) {
                calculateSystemWideConvergence();
                delta--;
            }
            repaint();
            try {
                Thread.sleep(16);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

  private void calculateSystemWideConvergence() {
        Random rand = new Random();
        for (int i = 0; i < parameterValidationWave.length - 1; i++) {
            parameterValidationWave[i] = parameterValidationWave[i + 1];
        }
        parameterValidationWave[parameterValidationWave.length - 1] = 60 + (Math.sin(System.currentTimeMillis() * 0.004) * 3);

        if (rand.nextDouble() < 0.15 && liveConduitSignals.size() < 35) {
            InferenceHorizonRung bottomTier = hierarchyRungs.get(7);
            liveConduitSignals.add(new AlignmentSignalToken(rand.nextInt(400) + 160, bottomTier.verticalY, 1));
        }

        List<AlignmentSignalToken> stabilizedTokens = new CopyOnWriteArrayList<>();
        for (AlignmentSignalToken token : liveConduitSignals) {
            int nextRungIndex = token.currentRungIndex - 1;
            if (nextRungIndex >= 0) {
                InferenceHorizonRung nextRung = hierarchyRungs.get(nextRungIndex);
                if (token.y > nextRung.verticalY) {
                    token.y -= 4.5;
                } else {
                    token.currentRungIndex = nextRungIndex;
                    aggregatedTransitionsCount.incrementAndGet();
                }
            } else {
                stabilizedTokens.add(token);
            }
        }
        liveConduitSignals.removeAll(stabilizedTokens);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        g2d.setColor(new Color(12, 16, 32));
        g2d.fillRect(0, 0, WIDTH, 100);
        g2d.setColor(new Color(0, 255, 150));
        g2d.setFont(new Font("Monospaced", Font.BOLD, 17));
        g2d.drawString("⚡ UNIFIED SOVEREIGN SYSTEM GRAPHICAL MATRIX // CROSS-SESSION ALLWORK", 35, 42);

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.setColor(new Color(150, 170, 200));
        g2d.drawString("INTEGRITY PARITY: ALL TRACKS REALIGNED | HARDWARE FIREWALL PINNED TO NULL | REPOSITORY SECURE", 35, 72);

        int panelX = WIDTH - 350; int panelY = 135; int panelW = 310; int panelH = 580;
        g2d.setColor(new Color(14, 20, 38));
        g2d.fill(new RoundRectangle2D.Double(panelX, panelY, panelW, panelH, 12, 12));
        g2d.setColor(new Color(0, 255, 150, 120));
        g2d.setStroke(new BasicStroke(1.8f));
        g2d.draw(new RoundRectangle2D.Double(panelX, panelY, panelW, panelH, 12, 12));

        g2d.setFont(new Font("Monospaced", Font.BOLD, 13));
        g2d.drawString("FEDERATED INTEGRATION REGISTER", panelX + 22, panelY + 35);
        g2d.setFont(new Font("Monospaced", Font.PLAIN, 11));
        g2d.setColor(Color.WHITE);
        g2d.drawString("CONCURRENT PIPELINE STEPS: " + aggregatedTransitionsCount.get(), panelX + 20, panelY + 85);
        g2d.drawString("TOTAL MONITORED HORIZONS:  " + TOTAL_TIERS_MONITORED + " TIERS", panelX + 20, panelY + 115);
        g2d.drawString(String.format("GLOBAL PARITY CONFIDENCE: %.8f%%", masterParityConfidenceIndex), panelX + 20, panelY + 145);

        int graphX = panelX + 20; int graphY = panelY + 370;
        g2d.setColor(new Color(6, 10, 22));
        g2d.fillRect(graphX, graphY, 270, 180);
        g2d.setColor(new Color(0, 220, 255, 150));
        for (int i = 0; i < parameterValidationWave.length - 1; i++) {
            g2d.drawLine(graphX + (i * 4), graphY + 150 - (int) parameterValidationWave[i], graphX + ((i + 1) * 4), graphY + 150 - (int) parameterValidationWave[i + 1]);
        }
        g2d.drawString("TOTAL EQUILIBRIUM TRAIL", graphX + 5, graphY - 15);

        for (InferenceHorizonRung layer : hierarchyRungs) {
            g2d.setColor(new Color(18, 25, 45)); g2d.fillRect(50, layer.verticalY - 15, 680, 30);
            g2d.setColor(new Color(0, 255, 150, 80)); g2d.drawRect(50, layer.verticalY - 15, 680, 30);
            g2d.setFont(new Font("Monospaced", Font.BOLD, 11)); g2d.setColor(new Color(0, 255, 150));
            g2d.drawString(layer.rungID, 65, layer.verticalY + 5);
            g2d.setFont(new Font("Monospaced", Font.PLAIN, 10)); g2d.setColor(Color.LIGHT_GRAY);
            g2d.drawString("// " + layer.functionalScope, 280, layer.verticalY + 5);
        }

        for (AlignmentSignalToken token : liveConduitSignals) {
            g2d.setColor(new Color(0, 255, 150, 200)); g2d.fillOval((int) token.x, (int) token.y - 4, 8, 8);
        }

        g2d.setFont(new Font("Monospaced", Font.BOLD, 12)); g2d.setColor(new Color(0, 255, 150));
        g2d.drawString("[ENVIRONMENT RULE: SECURE SANDBOX BOUNDS RIGIDLY PRESERVED]", 35, HEIGHT - 30);
    }

    private static class InferenceHorizonRung {
        int indexLevel; String rungID, functionalScope; int verticalY;
        InferenceHorizonRung(int indexLevel, String rungID, String functionalScope, int verticalY) {
            this.indexLevel = indexLevel; this.rungID = rungID; this.functionalScope = functionalScope; this.verticalY = verticalY;
        }
    }

    private static class AlignmentSignalToken {
        double x, y; int binaryBit; int currentRungIndex = 7;
        AlignmentSignalToken(double x, double y, int binaryBit) { this.x = x; this.y = y; this.binaryBit = binaryBit; }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            SectionFrame frame = new SectionFrame("Federated Sovereign Operations Core v5.00");
            frame.setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
            FederatedSovereignSystem corePanel = new FederatedSovereignSystem();
            frame.add(corePanel); frame.pack(); frame.setLocationRelativeTo(null); frame.setVisible(true);
            corePanel.launchMasterPipeline();
        });
    }
}