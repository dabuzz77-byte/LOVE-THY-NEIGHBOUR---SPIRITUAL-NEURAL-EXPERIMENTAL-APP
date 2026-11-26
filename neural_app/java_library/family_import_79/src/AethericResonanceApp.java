import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.geom.*;

/**
 * Handles the internal physics and metaphysical logic state 
 * for the Channel Rod Intent mechanism.
 */
class ChannelRodState {
    // Structural Core Variables
    private double consecrationStabilization = 1.0; // Base baseline (1 = 1)
    private double faithFrequency = 7.83;          // Initialized to Schumann Resonance
    private double aspirationStorage = 0.0;         // Range: 0.0 to 100.0
    private double manifestationMemory = 50.0;     // Coherence of the pattern
    
    // Output Vectors
    private double localizedIntentOutput = 0.0;
    private boolean isEmitting = false;

    public synchronized void updateState(double loopDelta) {
        // Continuous baseline grounding stabilization
        if (consecrationStabilization < 1.0) {
            consecrationStabilization += 0.01 * loopDelta;
        }

        // Simulates the continuous accumulation of energy into the cache array
        if (aspirationStorage < 100.0) {
            aspirationStorage += (faithFrequency * 0.05) * loopDelta;
            if (aspirationStorage > 100.0) aspirationStorage = 100.0;
        }

        // Calculate total localized terminal manifestation potential
        if (isEmitting) {
            localizedIntentOutput = (aspirationStorage * (faithFrequency / 7.83)) * consecrationStabilization;
            aspirationStorage -= 2.5 * loopDelta; // Deplete resource pool during discharge
            if (aspirationStorage <= 0) {
                aspirationStorage = 0;
                isEmitting = false;
                localizedIntentOutput = 0;
            }
        } else {
            localizedIntentOutput = 0.0;
        }
    }

    // Getters and Setters
    public double getConsecrationStabilization() { return consecrationStabilization; }
    public double getFaithFrequency() { return faithFrequency; }
    public void setFaithFrequency(double freq) { this.faithFrequency = freq; }
    public double getAspirationStorage() { return aspirationStorage; }
    public double getManifestationMemory() { return manifestationMemory; }
    public void setManifestationMemory(double val) { this.manifestationMemory = val; }
    public double getLocalizedIntentOutput() { return localizedIntentOutput; }
    public boolean isEmitting() { return isEmitting; }
    public void setEmitting(boolean emitting) { this.isEmitting = emitting; }
}

/**
 * Main application window and graphic subsystem for rendering 
 * the Non-Local Field Intent mechanism.
 */
public class AethericResonanceApp extends SectionFrame {
    private final ChannelRodState systemState;
    private final RenderPanel canvas;

    public AethericResonanceApp() {
        this.systemState = new ChannelRodState();
        this.canvas = new RenderPanel(systemState);

        setTitle("AETHERIC RESONANCE RIFLE DIAGRAM - CORE ENGAGEMENT");
        setSize(1100, 650);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        
        setLayout(new BorderLayout());
        add(canvas, BorderLayout.CENTER);
        add(createInterfaceControls(), BorderLayout.SOUTH);

        // Active telemetry refresh loop
        Thread engineLoop = new Thread(() -> {
            long lastTime = System.nanoTime();
            while (true) {
                long now = System.nanoTime();
                double delta = (now - lastTime) / 1_000_000_000.0;
                lastTime = now;

                systemState.updateState(delta * 10); // Scaled time step
                canvas.repaint();

                try {
                    Thread.sleep(16); // ~60 Frames per second execution
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
        engineLoop.start();
    }

    private JPanel createInterfaceControls() {
        JPanel controlPanel = new JPanel();
        controlPanel.setBackground(new Color(25, 25, 30));
        controlPanel.setLayout(new FlowLayout(FlowLayout.CENTER, 20, 10));

        JButton triggerButton = new JButton("PROPAGATE INTENT (EMIT)");
        triggerButton.setFocusPainted(false);
        triggerButton.addActionListener(e -> systemState.setEmitting(!systemState.isEmitting()));

        JSlider freqSlider = new JSlider(0, 1500, 783); // 7.83Hz baseline x100 scaling
        freqSlider.addChangeListener(e -> systemState.setFaithFrequency(freqSlider.getValue() / 100.0));
        
        JLabel freqLabel = new JLabel("Faith-Frequency Tuner: 7.83 Hz");
        freqLabel.setForeground(Color.LIGHT_GRAY);
        freqSlider.addChangeListener(e -> freqLabel.setText(String.format("Faith-Frequency Tuner: %.2f Hz", systemState.getFaithFrequency())));

        controlPanel.add(freqLabel);
        controlPanel.add(freqSlider);
        controlPanel.add(triggerButton);

        return controlPanel;
    }

    private static class RenderPanel extends JPanel {
        private final ChannelRodState state;

        public RenderPanel(ChannelRodState state) {
            this.state = state;
            setBackground(new Color(18, 18, 22));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int w = getWidth();
            int h = getHeight();

            // Draw Blueprint Grid Layout
            g2.setColor(new Color(40, 45, 60, 40));
            for (int i = 0; i < w; i += 40) g2.drawLine(i, 0, i, h);
            for (int j = 0; j < h; j += 40) g2.drawLine(0, j, w, j);

            // Coordinates for structural chassis mapping
            int startX = 150;
            int centerY = h / 2 - 20;

            // 1. Primary Consecrated Resonator (Stock Frame)
            g2.setColor(new Color(80, 75, 70));
            int[] stockX = {startX, startX + 120, startX + 150, startX + 30, startX};
            int[] stockY = {centerY - 40, centerY - 20, centerY + 60, centerY + 80, centerY + 20};
            g2.fillPolygon(stockX, stockY, 5);
            g2.setColor(Color.DARK_GRAY);
            g2.drawPolygon(stockX, stockY, 5);

            // Scripture-to-Intent Input Array overlay (Calculator interface grid)
            g2.setColor(new Color(30, 30, 35));
            g2.fillRect(startX + 15, centerY + 15, 60, 40);
            g2.setColor(new Color(0, 255, 150, 100));
            for (int m = 0; m < 4; m++) {
                for (int n = 0; n < 3; n++) {
                    g2.fillRect(startX + 20 + (n * 16), centerY + 20 + (m * 8), 10, 5);
                }
            }

            // 2. Main Receiver Assembly (Non-Local Entanglement Nexus & Cache)
            int receiverX = startX + 150;
            g2.setColor(new Color(50, 55, 60));
            g2.fillRect(receiverX, centerY - 25, 250, 50);
            
            // Temporary Miracle Cache Status Bar Visualizer
            g2.setColor(Color.BLACK);
            g2.fillRect(receiverX + 20, centerY - 15, 120, 12);
            g2.setColor(new Color(255, 180, 0));
            g2.fillRect(receiverX + 22, centerY - 13, (int) (116 * (state.getAspirationStorage() / 100.0)), 8);

            // 3. Collimating Field Guide (Main Barrel Construction)
            int barrelX = receiverX + 250;
            g2.setColor(new Color(110, 115, 120));
            g2.fillRect(barrelX, centerY - 10, 350, 20);
            
            // Handguard shrouding structure
            g2.setColor(new Color(70, 60, 50));
            g2.fillRoundRect(barrelX + 10, centerY - 15, 180, 30, 10, 10);

            // 4. Anointed Terminal Will Emitter (Muzzle)
            int muzzleX = barrelX + 350;
            g2.setColor(new Color(212, 175, 55)); // Brass/Gold visual finish
            int[] muzzX = {muzzleX, muzzleX + 40, muzzleX + 40, muzzleX};
            int[] muzzY = {centerY - 12, centerY - 5, centerY + 5, centerY + 12};
            g2.fillPolygon(muzzX, muzzY, 4);

            // Real-Time Dynamic Propagation Stream Render
            if (state.isEmitting() && state.getLocalizedIntentOutput() > 0) {
                g2.setColor(new Color(0, 220, 255, (int)(150 + Math.random() * 105)));
                g2.setStroke(new BasicStroke(4f));
                g2.drawLine(muzzleX + 40, centerY, w - 50, centerY);
                
                // Quantum field refraction arcs
                for (int i = 0; i < 5; i++) {
                    int arcX = muzzleX + 50 + (int)(Math.random() * (w - muzzleX - 150));
                    int arcOffset = (int)(Math.random() * 30) - 15;
                    g2.fillOval(arcX, centerY + arcOffset, 6, 6);
                }
            }

            // Real-time Text Telemetry Interface Layout
            g2.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2.setColor(Color.GREEN);
            g2.drawString(String.format("SYSTEM COHERENCE ENGINE STATUS: [AUTH=TRUE]"), 40, 50);
            g2.setColor(Color.WHITE);
            g2.drawString(String.format("Consecration Grounding: %.2f / 1.00", state.getConsecrationStabilization()), 40, 75);
            g2.drawString(String.format("Aspiration Accumulator: %.1f%%", state.getAspirationStorage()), 40, 95);
            g2.drawString(String.format("Manifestation Stream:   %.2f WT_UNIT", state.getLocalizedIntentOutput()), 40, 115);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            AethericResonanceApp app = new AethericResonanceApp();
            app.setVisible(true);
        });
    }
}
