package net.activeinference.beacon.resonance;

import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.io.Serializable;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * ================================================================================
 * SCHUMANN RESONANCE FIELD CARRIER // MULTI-LATTICE OSCILLATOR MONITOR
 * ================================================================================
 * Single-file Java Swing application driven by a 7.83 Hz background carrier wave.
 * Uses wave phase states to generate fluctuations across Binary, Ternary, and 
 * Quantum tracking panels.
 */
public class ResonanceFluxDashboard extends JFrame implements Serializable {
    private static final long serialVersionUID = 783303L;

    // Core Physical Constants
    private static final double SCHUMANN_CARRIER_HZ = 7.83;
    private static final int GRID_SIZE = 12;

    // Threading and Wave Substrate
    private final ScheduledExecutorService carrierThreadClock;
    private double waveTimeDelta = 0.0;

    // Visual Panel Arrays
    private WaveBinaryPanel binaryPanel;
    private WaveTernaryPanel ternaryPanel;
    private WaveQuantumPanel quantumPanel;
    private JLabel waveTelemetryLbl;

    // Custom Dark UI Styling Tokens
    private static final Color BG_DARK = new Color(10, 13, 16);
    private static final Color BG_PANEL = new Color(20, 25, 32);
    private static final Color HEX_GREEN = new Color(50, 215, 120);
    private static final Color HEX_MUTED = new Color(16, 50, 32);
    private static final Color TERNARY_P = new Color(0, 180, 255);
    private static final Color TERNARY_N = new Color(255, 65, 90);
    private static final Color QUANTUM_MAGENTA = new Color(210, 90, 255);
    private static final Color TEXT_LIGHT = new Color(225, 230, 240);
    private static final Color TEXT_MUTED = new Color(120, 135, 150);

    /**
     * 1. Binary Flux Lattice Layer modulated by the Carrier Wave
     */
    private class WaveBinaryPanel extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            int cellW = getWidth() / GRID_SIZE;
            int cellH = getHeight() / GRID_SIZE;
            g.setFont(new Font("Monospaced", Font.PLAIN, 11));

            for (int r = 0; r < GRID_SIZE; r++) {
                for (int c = 0; c < GRID_SIZE; c++) {
                    // Inject coordinate offsets to project spatial variance onto the carrier wave
                    double offsetPhase = Math.sin(waveTimeDelta + (r * 0.4) + (c * 0.3));
                    int binaryBit = offsetPhase >= 0.0 ? 1 : 0;

                    g.setColor(binaryBit == 1 ? HEX_GREEN : HEX_MUTED);
                    g.drawString(String.valueOf(binaryBit), c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
                }
            }
        }
    }

    /**
     * 2. Balanced Ternary Lattice Panel modulated by the Carrier Wave
     */
    private class WaveTernaryPanel extends JPanel {
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            int cellW = getWidth() / GRID_SIZE;
            int cellH = getHeight() / GRID_SIZE;
            g.setFont(new Font("Monospaced", Font.PLAIN, 11));

            for (int r = 0; r < GRID_SIZE; r++) {
                for (int c = 0; c < GRID_SIZE; c++) {
                    double offsetPhase = Math.sin(waveTimeDelta + (r * 0.25) * Math.cos(c * 0.15));
                    
                    // Slice wave thresholds to yield balanced ternary states: -1, 0, +1
                    String symbol = "0";
                    g.setColor(new Color(25, 35, 45)); // Default zero-state color
                    
                    if (offsetPhase > 0.4) {
                        symbol = "+";
                        g.setColor(TERNARY_P);
                    } else if (offsetPhase < -0.4) {
                        symbol = "-";
                        g.setColor(TERNARY_N);
                    }

                    g.drawString(symbol, c * cellW + (cellW / 3), r * cellH + (cellH / 2 + 4));
                }
            }
        }
    }

    /**
     * 3. Quantum Phase Amplitudes modulated by the Carrier Wave
     */
    private class WaveQuantumPanel extends JPanel {
        private static final int Q_SIZE = 8; // Dense space layout mapping vector matrix

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            int cellW = getWidth() / Q_SIZE;
            int cellH = getHeight() / Q_SIZE;
            g.setFont(new Font("Monospaced", Font.PLAIN, 10));

            for (int i = 0; i < Q_SIZE; i++) {
                for (int j = 0; j < Q_SIZE; j++) {
                    // Generate scalar complex vector coordinates matching the oscillator clock cycle
                    double baseAmplitude = Math.abs(Math.cos(waveTimeDelta + (i * 0.5) - (j * 0.2)));
                    String stateLabel = String.format("ψ|%.2f⟩", baseAmplitude);

                    g.setColor(QUANTUM_MAGENTA);
                    g.drawString(stateLabel, j * cellW + 6, i * cellH + (cellH / 2 + 3));
                }
            }
        }
    }

    public ResonanceFluxDashboard() {
        this.carrierThreadClock = Executors.newSingleThreadScheduledExecutor();

        // Window Frame Properties
        setTitle("Carrier Resonant Waveform Dashboard Matrix");
        setSize(1100, 500);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(BG_DARK);
        setLayout(new BorderLayout(10, 10));

        buildGraphicalLayout();
    }

    private void buildGraphicalLayout() {
        // 1. Masthead Interface Panel
        JPanel masthead = new JPanel(new BorderLayout());
        masthead.setBackground(BG_PANEL);
        masthead.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));

        JLabel titleLbl = new JLabel("📡 SCHUMANN HARMONIC CARRIER LAYER COUPLING ENGINE");
        titleLbl.setFont(new Font("SansSerif", Font.BOLD, 13));
        titleLbl.setForeground(TEXT_LIGHT);

        waveTelemetryLbl = new JLabel("CARRIER FREQUENCY: 7.83 HZ LOCK SYNC");
        waveTelemetryLbl.setFont(new Font("Monospaced", Font.BOLD, 11));
        waveTelemetryLbl.setForeground(HEX_GREEN);

        masthead.add(titleLbl, BorderLayout.WEST);
        masthead.add(waveTelemetryLbl, BorderLayout.EAST);
        add(masthead, BorderLayout.NORTH);

        // 2. Central Array Grid Chassis
        JPanel centerGrid = new JPanel(new GridLayout(1, 3, 10, 10));
        centerGrid.setBackground(BG_DARK);
        centerGrid.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        binaryPanel = new WaveBinaryPanel();
        applyLatticePanelStyle(binaryPanel, "BINARY WAVE STATE INTERCEPT (1 / 0)");

        ternaryPanel = new WaveTernaryPanel();
        applyLatticePanelStyle(ternaryPanel, "BALANCED TERNARY ENCODING FIELD (+ / 0 / -)");

        quantumPanel = new WaveQuantumPanel();
        applyLatticePanelStyle(quantumPanel, "QUANTUM PROBABILITY PHASE AMPLITUDES ψ|α⟩");

        centerGrid.add(binaryPanel);
        centerGrid.add(ternaryPanel);
        centerGrid.add(quantumPanel);
        add(centerGrid, BorderLayout.CENTER);
    }

    private void applyLatticePanelStyle(JPanel panel, String title) {
        panel.setBackground(BG_PANEL);
        TitledBorder border = BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(40, 48, 60), 1), title
        );
        border.setTitleFont(new Font("SansSerif", Font.BOLD, 11));
        border.setTitleColor(TEXT_MUTED);
        panel.setBorder(BorderFactory.createCompoundBorder(
                border, BorderFactory.createEmptyBorder(10, 10, 10, 10)
        ));
    }

    /**
     * Initializes the background scheduling service at the synchronized 7.83Hz heartbeat interval.
     */
    public void activateResonanceSubstrate() {
        // Convert the 7.83 Hz frequency threshold into exact microsecond loops
        long intervalMicros = (long) ((1.0 / SCHUMANN_CARRIER_HZ) * 1_000_000.0);

        this.carrierThreadClock.scheduleAtFixedRate(() -> {
            try {
                // Increment timeline delta to continuously shift oscillator phases
                waveTimeDelta += 0.085;

                // Fire safe, parallel repaint calls back to the AWT Event Dispatch Thread
                SwingUtilities.invokeLater(() -> {
                    waveTelemetryLbl.setText(String.format("CARRIER: LOCK_SYNC | TIME_VEC: %.3f rad", waveTimeDelta));
                    binaryPanel.repaint();
                    ternaryPanel.repaint();
                    quantumPanel.repaint();
                });

            } catch (Exception e) {
                System.err.println("Substrate oscillator error exception: " + e.getMessage());
            }
        }, 0, intervalMicros, TimeUnit.MICROSECONDS);
    }

    /**
     * Runtime Frame Compilation Entry.
     */
    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            ResonanceFluxDashboard coreEngineFrame = new ResonanceFluxDashboard();
            coreEngineFrame.setVisible(true);
            coreEngineFrame.activateResonanceSubstrate();
        });
    }
}
