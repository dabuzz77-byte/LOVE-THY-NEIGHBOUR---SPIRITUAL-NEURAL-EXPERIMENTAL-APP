import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.time.Duration;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

public class GodMindGhostBusGUI extends SectionFrame {

    // GLOBAL AXIOMS
    private static final long GLOBAL_SESSION_HEIGHT = 142857L;
    private static final double SCHUMANN_RESONANCE = 7.83;

    private final JTextArea terminalOutput;
    private final JButton scanButton;

    public GodMindGhostBusGUI() {
        setTitle("Ghost Inference Bus // God Mind Parity Sync");
        setSize(900, 600);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        getContentPane().setBackground(Color.BLACK);

        // Terminal Display Setup
        terminalOutput = new JTextArea();
        terminalOutput.setBackground(new Color(10, 10, 15));
        terminalOutput.setForeground(new Color(0, 255, 150)); // Phosphor Green
        terminalOutput.setFont(new Font("Consolas", Font.BOLD, 13));
        terminalOutput.setEditable(false);
        
        JScrollPane scrollPane = new JScrollPane(terminalOutput);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(0, 100, 50), 2));
        add(scrollPane, BorderLayout.CENTER);

        // Control Panel
        JPanel controlPanel = new JPanel();
        controlPanel.setBackground(Color.BLACK);
        
        scanButton = new JButton("INITIATE LOCAL JVM BUS SCAN (7.83Hz)");
        scanButton.setBackground(new Color(0, 80, 40));
        scanButton.setForeground(Color.WHITE);
        scanButton.setFont(new Font("Arial", Font.BOLD, 14));
        scanButton.setFocusPainted(false);
        scanButton.addActionListener(e -> executeGodMindParse());
        
        controlPanel.add(scanButton);
        add(controlPanel, BorderLayout.SOUTH);

        log("========================================================");
        log("[UI KERNEL LOADED] Awaiting command to bridge local Java apps...");
        log("[AXIOM] Target Session Height: " + GLOBAL_SESSION_HEIGHT);
        log("========================================================");
    }

    private void executeGodMindParse() {
        scanButton.setEnabled(false);
        terminalOutput.setText(""); // Clear buffer
        log("========================================================");
        log("[GHOST BUS] Scanning local OS for active Java Virtual Machines...");
        
        CompletableFuture.supplyAsync(this::gatherJavaProcesses)
                .thenApply(this::parseVirtueScores)
                .thenAccept(this::displayHighestVirtuePass)
                .thenRun(() -> SwingUtilities.invokeLater(() -> scanButton.setEnabled(true)));
    }

    private List<ProcessHandle> gatherJavaProcesses() {
        // Native Java 9+ OS process discovery
        return ProcessHandle.allProcesses()
                .filter(ph -> {
                    String cmd = ph.info().command().orElse("").toLowerCase();
                    return cmd.contains("java") || cmd.contains("javaw");
                })
                .collect(Collectors.toList());
    }

    private List<ParsedProcess> parseVirtueScores(List<ProcessHandle> processes) {
        if (processes.isEmpty()) {
            log("[WARNING] No external Java processes found on local PC.");
        }

        return processes.stream().map(ph -> {
            long pid = ph.pid();
            Optional<Instant> startTime = ph.info().startInstant();
            long uptimeSeconds = startTime.map(instant -> Duration.between(instant, Instant.now()).getSeconds()).orElse(1L);
            
            // Apply 7.83Hz Modulation to Uptime and PID (Naughtiest Variance)
            double variance = Math.abs(Math.sin((pid * uptimeSeconds) / SCHUMANN_RESONANCE));
            
            // Structural Alignment (Virtuous Anchor)
            double convergence = Math.abs(Math.cos(pid / 10.0));
            
            // Final Parity Calculation mapping to Session Height
            double parityScore = (variance * convergence) * (GLOBAL_SESSION_HEIGHT % 1000);
            
            String command = ph.info().command().orElse("Unknown JVM");
            
            log(String.format("[PID: %-6d] VARIANCE: %.4f | CONVERGENCE: %.4f | PARITY: %.2f", pid, variance, convergence, parityScore));
            
            return new ParsedProcess(pid, command, parityScore);
            
        }).sorted(Comparator.comparingDouble(ParsedProcess::getParityScore).reversed()) // Sort highest first
        .collect(Collectors.toList());
    }

    private void displayHighestVirtuePass(List<ParsedProcess> parsedProcesses) {
        if (parsedProcesses.isEmpty()) return;

        ParsedProcess primeNode = parsedProcesses.get(0);
        
        log("========================================================");
        log("[GOD MIND PARITY SYNC] Selection Complete.");
        log("[HIGHEST VIRTUE PASS ACHIEVED]");
        log(" -> TARGET PID:  " + primeNode.pid());
        log(" -> COMMAND:     " + primeNode.command());
        log(" -> PARITY SYNC: " + String.format("%.2f", primeNode.getParityScore()));
        log("========================================================");
        log("[STATUS] Prime node securely anchored to Session " + GLOBAL_SESSION_HEIGHT);
    }

    private void log(String message) {
        SwingUtilities.invokeLater(() -> {
            terminalOutput.append(message + "\n");
            // Auto-scroll to bottom
            terminalOutput.setCaretPosition(terminalOutput.getDocument().getLength());
        });
    }

    // Inner record-like class for state holding
    private static class ParsedProcess {
        private final long pid;
        private final String command;
        private final double parityScore;

        public ParsedProcess(long pid, String command, double parityScore) {
            this.pid = pid;
            this.command = command;
            this.parityScore = parityScore;
        }

        public long pid() { return pid; }
        public String command() { return command; }
        public double getParityScore() { return parityScore; }
    }

    public static void main(String[] args) {
        // Enforce dark mode system look and feel if available
        try {
            UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            GodMindGhostBusGUI gui = new GodMindGhostBusGUI();
            gui.setLocationRelativeTo(null); // Center on screen
            gui.setVisible(true);
        });
    }
}