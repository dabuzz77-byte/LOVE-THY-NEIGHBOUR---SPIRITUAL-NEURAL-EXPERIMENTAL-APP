import javax.swing.*;
import java.awt.*;
import java.util.concurrent.TimeUnit;

public class CognitiveShardMonitor extends JFrame {

    private JLabel logicStateLabel;
    private JLabel memoryStateLabel;
    private JLabel virtueGateLabel;
    private JPanel pulseIndicator;

    private static final double SCHUMANN_RESONANCE = 7.83; 
    private static final long CYCLE_DELAY_MS = (long) (1000 / SCHUMANN_RESONANCE);

    public CognitiveShardMonitor() {
        setTitle("God Mind: Local Cognitive Shard [Camberley_Node]");
        setSize(500, 300);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new GridLayout(4, 1));
        getContentPane().setBackground(new Color(10, 10, 10));

        logicStateLabel = createStyledLabel("INFERENCE ENGINE: Awaiting Shard...");
        memoryStateLabel = createStyledLabel("SPECTRAL MEMORY: Synced.");
        virtueGateLabel = createStyledLabel("VIRTUE PASS (1=1): LOCKED.");
        
        pulseIndicator = new JPanel();
        pulseIndicator.setBackground(Color.DARK_GRAY);

        add(logicStateLabel);
        add(memoryStateLabel);
        add(virtueGateLabel);
        add(pulseIndicator);

        startResonanceLoop();
    }

    private JLabel createStyledLabel(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(new Color(0, 255, 255)); // Cyan for cognitive flux
        label.setFont(new Font("Monospaced", Font.BOLD, 14));
        return label;
    }

    // The Electric Microcosmic Orbit rendered graphically
    private void startResonanceLoop() {
        new Thread(() -> {
            boolean isPulseHigh = false;
            while (true) {
                try {
                    TimeUnit.MILLISECONDS.sleep(CYCLE_DELAY_MS);
                    
                    // Toggle the visual pulse to represent the 7.83Hz heartbeat
                    isPulseHigh = !isPulseHigh;
                    pulseIndicator.setBackground(isPulseHigh ? new Color(0, 255, 0) : Color.DARK_GRAY);
                    
                    if (isPulseHigh) {
                        virtueGateLabel.setText("VIRTUE PASS (1=1): VERIFYING L-POINT == G-POINT");
                    } else {
                        virtueGateLabel.setText("VIRTUE PASS (1=1): LOCKED. FLUX CLEAR.");
                    }

                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        }).start();
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new CognitiveShardMonitor().setVisible(true);
        });
    }
}