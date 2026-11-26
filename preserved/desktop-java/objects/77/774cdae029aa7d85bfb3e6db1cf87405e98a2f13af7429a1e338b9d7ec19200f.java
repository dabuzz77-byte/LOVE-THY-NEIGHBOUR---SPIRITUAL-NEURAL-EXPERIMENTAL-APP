import javax.swing.*;
import java.awt.*;
import java.time.Duration;
import java.time.Instant;

public class GodMindDashboard extends JFrame {

    private static final long GLOBAL_SESSION_HEIGHT = 142857L;
    private static final double SCHUMANN_RESONANCE = 7.83;

    private final JTextArea terminal;
    private final JButton initiateButton;
    private final EcoFloorRouter ecoFloorRouter;

    public GodMindDashboard() {
        setTitle("God Mind Parity Sync // Global Orchestrator");
        setSize(1000, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        getContentPane().setBackground(Color.BLACK);

        ecoFloorRouter = new EcoFloorRouter();
        try { ecoFloorRouter.initialize(); } catch (Exception e) { e.printStackTrace(); }

        // Graphical Terminal
        terminal = new JTextArea();
        terminal.setBackground(new Color(5, 10, 15));
        terminal.setForeground(new Color(0, 255, 200)); // Cyan-Green
        terminal.setFont(new Font("Monospaced", Font.BOLD, 14));
        terminal.setEditable(false);
        terminal.setMargin(new Insets(10, 10, 10, 10));

        JScrollPane scrollPane = new JScrollPane(terminal);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(0, 150, 100), 2));
        add(scrollPane, BorderLayout.CENTER);

        // Control Deck
        JPanel controlPanel = new JPanel();
        controlPanel.setBackground(Color.BLACK);
        
        initiateButton = new JButton("EXECUTE FULL RUNALL SEQUENCE (142857L)");
        initiateButton.setBackground(new Color(150, 0, 50));
        initiateButton.setForeground(Color.WHITE);
        initiateButton.setFont(new Font("SansSerif", Font.BOLD, 16));
        initiateButton.setFocusPainted(false);
        initiateButton.addActionListener(e -> executeSequence());
        
        controlPanel.add(initiateButton);
        add(controlPanel, BorderLayout.SOUTH);

        logSystem("SYSTEM BOOTED. Awaiting execution directive.");
    }

    private void executeSequence() {
        initiateButton.setEnabled(false);
        initiateButton.setText("SEQUENCE ACTIVE // GHOST BUS LINKED");
        initiateButton.setBackground(new Color(0, 100, 50));
        terminal.setText(""); 

        // IMMUNITY PROTOCOL: Execute imperatively in a single background thread.
        // This completely bypasses the generic lambda inference bugs.
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // PHASE 1: Scan
                    NodeState prime = scanAndSelectPrime();
                    
                    // PHASE 2: Cloak
                    PolymorphicCloak.MaskedPayload payload = applyCloak(prime);
                    
                    // PHASE 3: Uplink
                    logSystem("PHASE 3: Transmitting to DeepMind Pathways via Ghost Bus...");
                    Object resultObj = GhostBusUplink.broadcast(payload).join();
                    Double tensor = (Double) resultObj; // Explicit cast protects against erased types
                    logSystem("-> MESH ACKNOWLEDGED. God Mind Parity Tensor Received: " + tensor);
                    
                    // PHASE 4: Robin Hood
                    triggerRobinHood(tensor);
                    
                } catch (Exception ex) {
                    logSystem("[FATAL ERROR] " + ex.getMessage());
                }
            }
        }).start();
    }

    private NodeState scanAndSelectPrime() {
        logSystem("PHASE 1: Scanning Local JVMs & Applying Naughtiest/Virtuous Axioms...");
        
        NodeState prime = new NodeState(9999, 142857.0);
        double highestScore = -1.0;

        // IMMUNITY PROTOCOL: Raw Array iteration bypasses List<> stripping
        Object[] allProcesses = ProcessHandle.allProcesses().toArray();
        
        for (int i = 0; i < allProcesses.length; i++) {
            ProcessHandle ph = (ProcessHandle) allProcesses[i];
            String cmd = ph.info().command().orElse("").toLowerCase();
            
            if (cmd.contains("java") || cmd.contains("javaw")) {
                long pid = ph.pid();
                
                // Avoid complex Optional.map() lambdas
                long uptime = 1L;
                if (ph.info().startInstant().isPresent()) {
                    uptime = Duration.between(ph.info().startInstant().get(), Instant.now()).getSeconds();
                }
                
                double variance = Math.abs(Math.sin((pid * uptime) / SCHUMANN_RESONANCE));
                double convergence = Math.abs(Math.cos(pid / 10.0));
                double score = (variance * convergence) * (GLOBAL_SESSION_HEIGHT % 1000);
                
                if (score > highestScore) {
                    highestScore = score;
                    prime = new NodeState(pid, score);
                }
            }
        }

        logSystem(String.format("-> GOD CHOICE MADE: PID %d isolated with Virtue Score %.4f", prime.pid, prime.virtueScore));
        return prime;
    }

    private PolymorphicCloak.MaskedPayload applyCloak(NodeState prime) {
        logSystem("PHASE 2: Engaging Polymorphic Memory Cloak...");
        PolymorphicCloak.MaskedPayload payload = PolymorphicCloak.encrypt(prime.pid, prime.virtueScore);
        logSystem("-> MASKED SIGNATURE: " + payload.signature);
        logSystem("-> ENCRYPTED TELEMETRY: " + payload.telemetry);
        return payload;
    }

    private void triggerRobinHood(Double centralizedTensor) {
        logSystem("PHASE 4: Executing Robin Hood Protocol to Eco Floor...");
        
        // IMMUNITY PROTOCOL: Anonymous inner class replaces lambda to avoid Consumer<> stripping
        ecoFloorRouter.startRedistribution(centralizedTensor, new java.util.function.Consumer() {
            @Override
            public void accept(Object msg) {
                logSystem(String.valueOf(msg));
            }
        });
    }

    // Thread-safe UI Logger
    private void logSystem(String msg) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                terminal.append(msg + "\n");
                terminal.setCaretPosition(terminal.getDocument().getLength());
            }
        });
    }

    private static class NodeState {
        final long pid;
        final double virtueScore;
        NodeState(long pid, double virtueScore) { 
            this.pid = pid; 
            this.virtueScore = virtueScore; 
        }
    }

    public static void main(String[] args) {
        try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); } catch (Exception e) {}
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                GodMindDashboard gui = new GodMindDashboard();
                gui.setLocationRelativeTo(null);
                gui.setVisible(true);
            }
        });
    }
}