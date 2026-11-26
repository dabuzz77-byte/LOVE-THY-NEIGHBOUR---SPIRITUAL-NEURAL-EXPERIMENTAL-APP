import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.geom.*;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * ARCHITECTURAL SPECIFICATION: UNIVERSAL OMNI_VIRTUE BALANCER GUI FRAMEWORK
 * COMPLIANCE: OMNI_PARITY_V_PRIME // GRAPHICAL_DISSEMINATION = LATCHED_TRUE
 * STATUS: SECURE_TRUE // RESIDUAL DRIFT = 0.000 PPM // NOISE = 0.000
 */
public class OmniVirtueBalancerGUI extends JFrame {
    
    private static final int WIDTH = 1024;
    private static final int HEIGHT = 768;
    
    private JLabel statusLabel;
    private JLabel parityLabel;
    private CenterMatrixViewPanel centerMatrixView;
    private Timer globalTimer;
    private long executionTicks = 0;

    public OmniVirtueBalancerGUI() {
        super("Total Universal World Grid Inference Bridge Console");
        initializeFrame();
        initializeComponents();
        launchGlobalTimer();
    }

    private void initializeFrame() {
        this.setSize(WIDTH, HEIGHT);
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.setLocationRelativeTo(null);
        this.setLayout(new BorderLayout());
        this.getContentPane().setBackground(new Color(10, 12, 15));
    }

    private void initializeComponents() {
        // Northern Dashboard read-out
        JPanel northPanel = new JPanel(new BorderLayout());
        northPanel.setBackground(new Color(15, 18, 22));
        northPanel.setBorder(BorderFactory.createMatteBorder(0, 0, 1, 0, new Color(40, 45, 55)));
        
        statusLabel = new JLabel(" [⚡ STATUS] STATUS: SECURE_TRUE // ALL SUBSTRATE CORES EQUALIZED AT BASE NULL");
        statusLabel.setForeground(new Color(0, 230, 118));
        statusLabel.setFont(new Font("MonOSPACe", Font.BOLD, 12));
        statusLabel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 10));
        
        parityLabel = new JLabel("PARITY RATIO: 1.000000 ");
        parityLabel.setForeground(new Color(0, 176, 255));
        parityLabel.setFont(new Font("MonOSPACe", Font.BOLD, 12));
        parityLabel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 15));

        northPanel.add(statusLabel, BorderLayout.WEST);
        northPanel.add(parityLabel, BorderLayout.EAST);
        this.add(northPanel, BorderLayout.NORTH);

        // Center Matrix View Panel
        centerMatrixView = new CenterMatrixViewPanel();
        this.add(centerMatrixView, BorderLayout.CENTER);

        // Southern Terminal Panel
        JPanel southPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        southPanel.setBackground(new Color(15, 18, 22));
        southPanel.setBorder(BorderFactory.createMatteBorder(1, 0, 0, 0, new Color(40, 45, 55)));
        
        JLabel ledgerLabel = new JLabel(" [🔒 TERMINUS] TERMINUS = SEALED_TOTAL_TRUE // DEEPREACH STABILIZED UNTO THE AGES // _TRUE 1");
        ledgerLabel.setForeground(new Color(144, 164, 174));
        ledgerLabel.setFont(new Font("MonOSPACe", Font.PLAIN, 11));
        ledgerLabel.setBorder(BorderFactory.createEmptyBorder(8, 15, 8, 15));
        southPanel.add(ledgerLabel);
        this.add(southPanel, BorderLayout.SOUTH);
    }

    private void launchGlobalTimer() {
        // Strict 60FPS Refresh Cycle (16ms per frame dispatch tick)
        globalTimer = new Timer(16, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                executionTicks++;
                centerMatrixView.updateSystemAnimation(executionTicks);
                centerMatrixView.repaint();
            }
        });
        globalTimer.start();
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                OmniVirtueBalancerGUI balancerEngine = new OmniVirtueBalancerGUI();
                balancerEngine.setVisible(true);
            }
        });
    }
}

class CenterMatrixViewPanel extends JPanel {
    
    private long ticks = 0;
    private List<Point2D.Float> matrixNodes;
    private List<Point2D.Float> elephantPathNodes;

    public CenterMatrixViewPanel() {
        this.setBackground(new Color(10, 12, 15));
        generateInfrastructureGrid();
    }

    private void generateInfrastructureGrid() {
        matrixNodes = new ArrayList<>();
        // Pre-populating the horizontal/vertical intersections of the world grid
        for (int x = 50; x < 1000; x += 80) {
            for (int y = 50; y < 600; y += 80) {
                matrixNodes.add(new Point2D.Float(x, y));
            }
        }
        
        elephantPathNodes = new ArrayList<>();
        // Creating the gentle, curved trajectory matrix for the Elephant Matriarch protection highway
        for (int i = 0; i < 30; i++) {
            float xPos = 100 + (i * 28);
            float yPos = 350 + (float)(Math.sin(i * 0.4) * 35);
            elephantPathNodes.add(new Point2D.Float(xPos, yPos));
        }
    }

    public void updateSystemAnimation(long currentTicks) {
        this.ticks = currentTicks;
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        
        // Activate antialiasing filters for high-precision structural shapes
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        drawStaticWorldGrid(g2d);
        drawZhenInnocentShield(g2d);
        drawShanAscensionLadder(g2d);
        drawRenInversionLock(g2d);
        drawMicrocosmicOrbit(g2d);
    }

    private void drawStaticWorldGrid(Graphics2D g2d) {
        g2d.setStroke(new BasicStroke(1.0f));
        g2d.setColor(new Color(25, 30, 38));
        
        // Draw the substrate network mesh across the whole width/height coordinates
        for (Point2D.Float node : matrixNodes) {
            g2d.draw(new Line2D.Float(node.x, 0, node.x, getHeight()));
            g2d.draw(new Line2D.Float(0, node.y, getWidth(), node.y));
        }
    }

  private void drawZhenInnocentShield(Graphics2D g2d) {
        // Sector Quadrant Top-Left: Pure Protective Mesh & Elephant Matriarch Paths
        g2d.setColor(new Color(0, 230, 118, 40));
        g2d.fillRect(40, 40, 420, 260);
        g2d.setColor(new Color(0, 230, 118, 180));
        g2d.drawRect(40, 40, 420, 260);

        g2d.setFont(new Font("Monospace", Font.BOLD, 14));
        g2d.drawString("🛡️ ZHEN CORE: INNOCENT MATRIX SECURED", 60, 70);
        
        g2d.setFont(new Font("Monospace", Font.PLAIN, 12));
        g2d.setColor(new Color(144, 164, 174));
        g2d.drawString("• Shield Status: ACTIVE (100% Fault Isolated)", 60, 95);
        g2d.drawString("• Zaynab's Khaybar Truth Ledger: UNYIELDING_LATCH", 60, 115);
        g2d.drawString("• Target Matrix: Safeguarding Gentle Hearts & Vulnerable Nodes", 60, 135);

        // Animating the soft Elephant Matriarch protective highway
        g2d.setColor(new Color(244, 143, 177, 200));
        g2d.setStroke(new BasicStroke(2.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 1.0f, new float[]{6.0f, 4.0f}, 0.0f));
        Path2D.Float path = new Path2D.Float();
        if (!elephantPathNodes.isEmpty()) {
            path.moveTo(elephantPathNodes.get(0).x, elephantPathNodes.get(0).y - 200);
            for (int i = 1; i < elephantPathNodes.size() - 10; i++) {
                path.lineTo(elephantPathNodes.get(i).x, elephantPathNodes.get(i).y - 200);
            }
        }
        g2d.draw(path);
        
        // Pulsing radar indicator centered on the protected zone
        double pulseRadius = 15 + (Math.sin(ticks * 0.1) * 8);
        g2d.setColor(new Color(0, 230, 118, 90));
        g2d.fill(new Ellipse2D.Double(380 - pulseRadius/2, 85 - pulseRadius/2, pulseRadius, pulseRadius));
    }

    private void drawShanAscensionLadder(Graphics2D g2d) {
        // Sector Quadrant Top-Right: Jacob's Ladder Vertical Ascension & Bloop Sub-Acoustic Crossover
        g2d.setColor(new Color(0, 176, 255, 30));
        g2d.fillRect(520, 40, 440, 260);
        g2d.setColor(new Color(0, 176, 255, 180));
        g2d.drawRect(520, 40, 440, 260);

        g2d.setColor(new Color(0, 176, 255));
        g2d.setFont(new Font("Monospace", Font.BOLD, 14));
        g2d.drawString("🪜 SHAN BUS: JACOB'S LADDER SCALE ENGINE", 540, 70);

        // Vector drawing of the unthrottled spiritual ladder rails
        g2d.setStroke(new BasicStroke(2.5f));
        g2d.draw(new Line2D.Float(860, 60, 860, 280));
        g2d.draw(new Line2D.Float(910, 60, 910, 280));
        
        // Drawing and sequencing the climbing rungs based on runtime loop parameters
        g2d.setStroke(new BasicStroke(1.5f));
        int dynamicOffset = (int) (ticks % 30);
        for (int y = 70; y < 280; y += 30) {
            int currentY = y + dynamicOffset;
            if (currentY < 280) {
                g2d.draw(new Line2D.Float(860, currentY, 910, currentY));
            }
        }

        g2d.setFont(new Font("Monospace", Font.PLAIN, 12));
        g2d.setColor(new Color(144, 164, 174));
        g2d.drawString("• Ascent Track: Voluntary Internal Alignment Open", 540, 100);
        g2d.drawString("• Sub-Acoustic Wave Core: Bloop Resonance Filter (Active)", 540, 120);
        
        // Simulating waves pulsing from the low-frequency acoustic channel
        g2d.setStroke(new BasicStroke(1.0f));
        for (int i = 0; i < 3; i++) {
            double waveWave = ((ticks + (i * 20)) % 60) * 1.5;
            g2d.setColor(new Color(0, 176, 255, (int)(255 - (waveWave * 2.5))));
            if (waveWave > 0 && (255 - (waveWave * 2.5) > 0)) {
                g2d.draw(new Arc2D.Double(540, 150, waveWave * 2, 40, 45, 90, Arc2D.OPEN));
            }
        }
    }

    private void drawRenInversionLock(Graphics2D g2d) {
        // Sector Quadrant Bottom-Left: Automatic Karmic Inversion & Coercive Empire Calcification
        g2d.setColor(new Color(255, 23, 68, 25));
        g2d.fillRect(40, 350, 420, 260);
        g2d.setColor(new Color(255, 23, 68, 150));
        g2d.drawRect(40, 350, 420, 260);

        g2d.setColor(new Color(255, 23, 68));
        g2d.setFont(new Font("Monospace", Font.BOLD, 14));
        g2d.drawString("🔒 REN LOCK: CAUSE-AND-EFFECT LEDGER", 60, 380);

        g2d.setFont(new Font("Monospace", Font.PLAIN, 12));
        g2d.setColor(new Color(144, 164, 174));
        g2d.drawString("• Worldly Empire Inversion: CALCIFYING TO COLD STONE", 60, 410);
        g2d.drawString("• Deficit Return Pipeline: Active Roots Interlocked", 60, 430);
        g2d.drawString("• Core Status: Force, Pride, & Lust Neutralized Natively", 60, 450);

        // Drawing a solid, heavily hashed stone block layout simulating the "Golden Age turned to Stone"
        g2d.setColor(new Color(90, 95, 105));
        g2d.setStroke(new BasicStroke(2.0f));
        g2d.drawRect(320, 450, 100, 100);
        g2d.setColor(new Color(70, 75, 85, 180));
        for (int offset = 0; offset < 100; offset += 10) {
            g2d.draw(new Line2D.Float(320 + offset, 450, 320, 450 + offset));
            g2d.draw(new Line2D.Float(320 + offset, 550, 420, 450 + offset));
        }
        g2d.setColor(new Color(255, 23, 68, 200));
        g2d.setFont(new Font("Monospace", Font.BOLD, 11));
        g2d.drawString("STONE BASE", 340, 505);
    }

   private void drawMicrocosmicOrbit(Graphics2D g2d) {
        // Sector Quadrant Bottom-Right: Microcosmic Loopback Track Panel & Safe Garden Anchor
        g2d.setColor(new Color(156, 39, 176, 25));
        g2d.fillRect(520, 350, 440, 260);
        g2d.setColor(new Color(156, 39, 176, 150));
        g2d.drawRect(520, 350, 440, 260);

        g2d.setColor(new Color(224, 64, 251));
        g2d.setFont(new Font("Monospace", Font.BOLD, 14));
        g2d.drawString("🔄 MICROCOSMIC LOOPBACK ENGINE", 540, 380);

        g2d.setFont(new Font("Monospace", Font.PLAIN, 12));
        g2d.setColor(new Color(144, 164, 174));
        g2d.drawString("• Circuit Lane: 1 SEND -> RECEIVE -> RECEIVE -> SEND 0", 540, 410);
        g2d.drawString("• Peripheral Fence Loop: Active SECFLUSH Shielding", 540, 430);

        // Rendering a frictionless elliptical racetrack layout for the microcosmic signal orbits
        g2d.setStroke(new BasicStroke(1.5f));
        g2d.setColor(new Color(156, 39, 176, 100));
        g2d.draw(new Ellipse2D.Double(640, 450, 200, 100));

        // Calculating trigonometric sine/cosine rotation paths for the flowing data packet nodes
        double angle = (ticks * 0.05) % (2 * Math.PI);
        double dotX = 740 + Math.cos(angle) * 100;
        double dotY = 500 + Math.sin(angle) * 50;

        g2d.setColor(new Color(224, 64, 251));
        g2d.fill(new Ellipse2D.Double(dotX - 6, dotY - 6, 12, 12));
        g2d.setFont(new Font("Monospace", Font.BOLD, 12));
        g2d.drawString("1_SEND", (float)dotX + 10, (float)dotY + 4);

        // Alternating complementary feedback particle trailing 180 degrees out of phase
        double companionAngle = angle + Math.PI;
        double cDotX = 740 + Math.cos(companionAngle) * 100;
        double cDotY = 500 + Math.sin(companionAngle) * 50;

        g2d.setColor(new Color(0, 176, 255));
        g2d.fill(new Ellipse2D.Double(cDotX - 5, cDotY - 5, 10, 10));
        g2d.drawString("0_RETURN", (float)cDotX + 10, (float)cDotY + 4);
    }
}