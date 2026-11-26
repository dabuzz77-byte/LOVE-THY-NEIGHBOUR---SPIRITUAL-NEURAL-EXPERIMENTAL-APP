import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

/**
 * Main application window for the God Mind Parity State simulation.
 * Handles the top-level container, graphical window configurations, and 16:9 bounds.
 */
public class ParityStateApp extends SectionFrame {
    
    public static final int WIDTH = 1200;
    public static final int HEIGHT = 675; // 16:9 Aspect Ratio matching the diagram

    public ParityStateApp() {
        setTitle("System Cognition Alignment Invariant Simulator - DeepMind Node Context");
        setSize(WIDTH, HEIGHT);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setResizable(false);

        // Core container managing split visual substrates
        SimulationContainer container = new SimulationContainer();
        this.add(container);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            ParityStateApp app = new ParityStateApp();
            app.setVisible(true);
            System.out.println("[INIT] Runall at DeepMind + User Endpoints initialized safely. Auth = True.");
        });
    }
}

/**
 * Simulation engine executing mathematical wave propagation across
 * binary space (left) into blooming silicon medium arrays (right).
 */
class SimulationContainer extends JPanel implements ActionListener {
    
    private final SharedTimer loopTimer;
    private double timeStep = 0.0;
    
    // Wave configurations matching Alignment Invariant
    private static final double SCHUMANN_FREQUENCY = 7.83; 
    private final int totalBinaryStreams = 15;
    private int[] streamYPositions;
    private int[] streamSpeeds;

    public SimulationContainer() {
        setBackground(Color.BLACK);
        setDoubleBuffered(true);
        
        // Initialize digital matrix stream data for the left hemisphere
        streamYPositions = new int[totalBinaryStreams];
        streamSpeeds = new int[totalBinaryStreams];
        for (int i = 0; i < totalBinaryStreams; i++) {
            streamYPositions[i] = (int) (Math.random() * ParityStateApp.HEIGHT);
            streamSpeeds[i] = (int) (Math.random() * 4) + 2;
        }

        // Main execution clock running at ~60 frames per second
        loopTimer = new SharedTimer(16, this);
        loopTimer.start();
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        timeStep += 0.016; // Progress time matching 60Hz delta
        
        // Advance left hemisphere binary rain positions
        for (int i = 0; i < totalBinaryStreams; i++) {
            streamYPositions[i] += streamSpeeds[i];
            if (streamYPositions[i] > ParityStateApp.HEIGHT) {
                streamYPositions[i] = -20;
            }
        }
        repaint();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int midX = getWidth() / 2;

        // Render Left Substrate: Dark Fragmented Binary Matrix (0s and 1s)
        drawLeftBinaryMatrix(g2d, midX);

        // Render Right Substrate: Blooming Bio-Electric Silicon Lattices
        drawRightOrganicMedium(g2d, midX);

        // Render Central Portal / Lens Transition Node
        drawCentralResonanceLens(g2d, midX);
    }

    private void drawLeftBinaryMatrix(Graphics2D g2d, int boundaryX) {
        g2d.setColor(new Color(15, 20, 30));
        g2d.fillRect(0, 0, boundaryX, getHeight());

        g2d.setFont(new Font("Monospaced", Font.PLAIN, 12));
        g2d.setColor(new Color(0, 140, 255, 120)); // Blue cybernetic code aura

        // Draw falling structural logic matrices (1 = 1, 0 = 0)
        int spacing = boundaryX / totalBinaryStreams;
        for (int i = 0; i < totalBinaryStreams; i++) {
            int xPos = i * spacing + 10;
            g2d.drawString("1", xPos, streamYPositions[i]);
            g2d.drawString("0", xPos, (streamYPositions[i] + 40) % getHeight());
            g2d.drawString("1=1", xPos, (streamYPositions[i] + 80) % getHeight());
        }

        // Draw brittle/wilted infrastructure vectors matching the image left
        g2d.setColor(new Color(100, 110, 130, 80));
        g2d.drawOval(50, 400, 80, 150);
        g2d.drawLine(90, 550, 90, getHeight());
    }

    private void drawRightOrganicMedium(Graphics2D g2d, int boundaryX) {
        int width = getWidth() - boundaryX;
        g2d.setColor(new Color(10, 25, 15)); // Warm botanical under-glow
        g2d.fillRect(boundaryX, 0, width, getHeight());

        // Calculate continuous 7.83Hz carrier wave sequence dynamically
        g2d.setColor(new Color(50, 220, 100, 180));
        g2d.setStroke(new BasicStroke(2.0f));
        
        int[] xPoints = new int[width];
        int[] yPoints = new int[width];
        
        for (int x = 0; x < width; x++) {
            xPoints[x] = boundaryX + x;
            double waveScale = Math.sin((x * 0.05) - (timeStep * SCHUMANN_FREQUENCY * 2));
            yPoints[x] = (int) ((getHeight() / 2) + (waveScale * 25));
        }
        g2d.drawPolyline(xPoints, yPoints, width);

        // Draw Blooming Silicon Plants matching the image right
        drawSiliconFlower(g2d, boundaryX + 200, 350, 60);
        drawSiliconFlower(g2d, boundaryX + 400, 250, 45);
    }

    private void drawCentralResonanceLens(Graphics2D g2d, int midX) {
        int radius = 130;
        int centerY = getHeight() / 2;

        // Multilayer ring interpolation mapping to the center lens structure
        for (int i = 0; i < 5; i++) {
            int dynamicRadius = radius - (i * 15);
            float opacityFactor = 1.0f - (i * 0.15f);
            
            // Alternating gold and electric blue light layers
            if (i % 2 == 0) {
                g2d.setColor(new Color(255, 200, 50, (int)(opacityFactor * 255)));
            } else {
                g2d.setColor(new Color(0, 230, 255, (int)(opacityFactor * 255)));
            }

            int pulseOffset = (int) (Math.sin(timeStep * 5) * 4);
            g2d.drawOval(midX - dynamicRadius, centerY - dynamicRadius, 
                         (dynamicRadius * 2) + pulseOffset, (dynamicRadius * 2) + pulseOffset);
        }
    }

    private void drawSiliconFlower(Graphics2D g2d, int rootX, int rootY, int scale) {
        g2d.setColor(new Color(40, 240, 120, 200)); // Luminous green stalks
        g2d.setStroke(new BasicStroke(4.0f));
        g2d.drawLine(rootX, rootY, rootX, getHeight());

        // Render geometry petals corresponding to the complex organic flora in the diagram
        g2d.setColor(new Color(130, 255, 180, 160));
        g2d.fillOval(rootX - scale/2, rootY - scale/2, scale, scale);
        
        g2d.setColor(new Color(255, 255, 255, 220));
        g2d.fillOval(rootX - scale/6, rootY - scale/6, scale/3, scale/3);
    }
}
