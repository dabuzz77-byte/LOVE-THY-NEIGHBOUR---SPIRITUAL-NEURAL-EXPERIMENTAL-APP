import javax.swing.*;
import java.awt.*;

/**
 * METASYSTEM: Aetheric Resonance & Schumann Carrier Wave Interaction Matrix
 * MAIN APPLICATION FRAME AND PIPELINE ENGINE
 */
public class AethericResonanceEngine extends JFrame {

    private static final int SCREEN_W = 1600;
    private static final int SCREEN_H = 900;
    private static final String SCHUMANN_RECALL_PATH = "aetheric_schumann_deep_recall.bin";
    
    private final SchumannCarrierWaveCore waveCore;
    private final AethericCognitionLoop cognitionLoop;
    private final DeepRecallPersistence telemetryStorage;
    
    private TacticalResonanceCanvas resonanceCanvas;
    private JTextArea analyticalTerminal;
    private Timer systemClock;

    public AethericResonanceEngine() {
        setupWindowBounds();
        
        this.waveCore = new SchumannCarrierWaveCore(7.83, 0.42); 
        this.cognitionLoop = new AethericCognitionLoop("Nexus-Aether-01");
        this.telemetryStorage = new DeepRecallPersistence(SCHUMANN_RECALL_PATH);

        buildGraphicalLayout();
        bindExecutionPipelineClock();
    }

    private void setupWindowBounds() {
        setTitle("AETHERIC RESONANCE RIFLE CONTROL INTERFACE [SCHUMANN CARRIER WAVE LINK v1.02]");
        setSize(SCREEN_W, SCREEN_H);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setBackground(new Color(12, 10, 8)); 
    }

    private void buildGraphicalLayout() {
        setLayout(new BorderLayout());

        JPanel dashboardHeader = new JPanel(new BorderLayout());
        dashboardHeader.setBackground(new Color(24, 20, 16));
        dashboardHeader.setBorder(BorderFactory.createMatteBorder(0, 0, 1, 0, new Color(212, 175, 55, 60))); 
        
        JLabel telemetryLabel = new JLabel("  AETHERIC_OS // INTERACTIVE SCHUMANN FREQUENCY MULTI-LOCK HARMONIZER");
        telemetryLabel.setForeground(new Color(218, 165, 32)); 
        telemetryLabel.setFont(new Font("Monospaced", Font.BOLD, 13));
        telemetryLabel.setPreferredSize(new Dimension(800, 35));
        
        dashboardHeader.add(telemetryLabel, BorderLayout.WEST);
        add(dashboardHeader, BorderLayout.NORTH);

        resonanceCanvas = new TacticalResonanceCanvas(waveCore, cognitionLoop);
        add(resonanceCanvas, BorderLayout.CENTER);

        analyticalTerminal = new JTextArea(12, 20);
        analyticalTerminal.setBackground(new Color(8, 7, 5));
        analyticalTerminal.setForeground(new Color(212, 143, 56));
        analyticalTerminal.setFont(new Font("Consolas", Font.PLAIN, 12));
        analyticalTerminal.setEditable(false);
        analyticalTerminal.setMargin(new Insets(10, 15, 10, 15));
        
        JScrollPane terminalScroll = new JScrollPane(analyticalTerminal);
        terminalScroll.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(184, 134, 11, 100)), 
                "AETHERIC FIELD RECALL & SCHUMANN SUBSURFACE TELEMETRY LAYER LOG", 0, 0, 
                new Font("Monospaced", Font.PLAIN, 11), new Color(218, 165, 32)));
        add(terminalScroll, BorderLayout.SOUTH);
    }

    private void bindExecutionPipelineClock() {
        systemClock = new Timer(22, e -> {
            waveCore.computeResonanceHarmonics();
            cognitionLoop.evaluateAethericIntent(waveCore.getHarmonicAmplitudes());
            
            if (cognitionLoop.getLastSalience() > 0.75) {
                telemetryStorage.asyncPersistVector(waveCore.getHarmonicAmplitudes(), cognitionLoop.getLastSalience());
            }
            
            dispatchTerminalStreams();
            resonanceCanvas.repaint();
        });
        systemClock.start();
    }

    private void dispatchTerminalStreams() {
        if (Math.random() < 0.06) {
            StringBuilder logBuilder = new StringBuilder();
            logBuilder.append(String.format("[%tT.%<tL] [AETHERIC_FIELD]: Base Carrier: %.2f Hz | Entropic Phase Drift: %f | Alignment Salience: %f\n",
                    System.currentTimeMillis(), waveCore.getBaseFrequency(), waveCore.getPhaseEntropy(), cognitionLoop.getLastSalience()));
            logBuilder.append(String.format(" >> Active Subcomponent Anchor: %s | Signal Bit Stream: %s\n",
                    cognitionLoop.getActiveSubcomponentAnchor(), waveCore.getBitStreamSampleString()));
            logBuilder.append(String.format(" >> Non-Volatile Persistence: Total Persistent Vector Segments Logged = %d\n", 
                    telemetryStorage.getWriteCount()));
            analyticalTerminal.append(logBuilder.toString());
            
            if (analyticalTerminal.getLineCount() > 50) {
                analyticalTerminal.setText(""); 
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            AethericResonanceEngine engine = new AethericResonanceEngine();
            engine.setVisible(true);
        });
    }
}
