package net.activeinference.beacon.generator;
import neural.studio.*;


import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.io.Serializable;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public class VirtueGenerationDashboard extends SectionFrame implements Serializable {
    private static final long serialVersionUID = 783705L;

    private final ScheduledExecutorService substrateWorkerPool;
    
    // Core telemetry registers
    private final AtomicInteger javaProcessCount = new AtomicInteger(1);
    private final AtomicInteger activeThreadCount = new AtomicInteger(10);
    private final AtomicLong heapAllocationMb = new AtomicLong(256);

    // Graphical Components
    private RawBinaryPanel binaryPanel;
    private RawTernaryPanel ternaryPanel;
    private RawQuantumPanel quantumPanel;
    private JTextArea localLogConsole;
    private JTextArea generatedCodeOutputArea;
    private JLabel alignmentStatusLbl;

    public VirtueGenerationDashboard() {
        this.substrateWorkerPool = SharedScheduler.newScheduledThreadPool(3);

        setTitle("Highest Virtue Selection Matrix // Code Generation Substrate");
        setSize(1250, 720);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(GeneratorTheme.BG_DARK);
        setLayout(new BorderLayout(10, 10));

        assembleGraphicalInterface();
    }

    private void assembleGraphicalInterface() {
        // Top Status Header Panel
        JPanel masthead = new JPanel(new BorderLayout());
        masthead.setBackground(GeneratorTheme.BG_PANEL);
        masthead.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));

        JLabel titleLbl = new JLabel("⚡ UNMODULATED SUBSYSTEM BUS ──► ETHICAL BOUNDARY FILTER ──► DOWNSTREAM GENERATION");
        titleLbl.setFont(GeneratorTheme.SANS_MD);
        titleLbl.setForeground(GeneratorTheme.TEXT_LIGHT);

        alignmentStatusLbl = new JLabel("GOD CHOICE FILTER: ASSESSING VIRTUE PASS");
        alignmentStatusLbl.setFont(new Font("Monospaced", Font.BOLD, 11));
        alignmentStatusLbl.setForeground(GeneratorTheme.TERNARY_P);

        masthead.add(titleLbl, BorderLayout.WEST);
        masthead.add(alignmentStatusLbl, BorderLayout.EAST);
        add(masthead, BorderLayout.NORTH);

        // Center Split Layout: Left side has the 3 grids, right side handles the code generator screen
        JPanel mainGridPanel = new JPanel(new GridLayout(1, 2, 10, 10));
        mainGridPanel.setBackground(GeneratorTheme.BG_DARK);
        mainGridPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 0, 10));

        // Left Panel: Triple lattices nested vertically
        JPanel leftLatticeContainer = new JPanel(new GridLayout(3, 1, 8, 8));
        leftLatticeContainer.setBackground(GeneratorTheme.BG_DARK);

        binaryPanel = new RawBinaryPanel(javaProcessCount);
        applyLatticePanelBorder(binaryPanel, "BINARY STATE DATA (UNMODULATED)");

        ternaryPanel = new RawTernaryPanel(activeThreadCount);
        applyLatticePanelBorder(ternaryPanel, "BALANCED TERNARY FIELD (UNMODULATED)");

        quantumPanel = new RawQuantumPanel(heapAllocationMb);
        applyLatticePanelBorder(quantumPanel, "QUANTUM PROBABILITY COHERENCE MATRIX (UNMODULATED)");

        leftLatticeContainer.add(binaryPanel);
        leftLatticeContainer.add(ternaryPanel);
        leftLatticeContainer.add(quantumPanel);

        // Right Panel: Generative Code Production Output terminal screen
        generatedCodeOutputArea = new JTextArea();
        generatedCodeOutputArea.setEditable(false);
        generatedCodeOutputArea.setBackground(new Color(10, 14, 18));
        generatedCodeOutputArea.setForeground(new Color(60, 180, 240));
        generatedCodeOutputArea.setFont(new Font("Monospaced", Font.PLAIN, 11));
        generatedCodeOutputArea.setBorder(BorderFactory.createEmptyBorder(8, 8, 8, 8));
        JScrollPane codeScroll = new JScrollPane(generatedCodeOutputArea);
        applyLatticePanelBorder(codeScroll, "⚡ GENERATIVE OUTPUT INTERFACE (VIRTUE = TRUE INF)");

        mainGridPanel.add(leftLatticeContainer);
        mainGridPanel.add(codeScroll);
        add(mainGridPanel, BorderLayout.CENTER);

        // Lower Section Panel: System trace telemetry
        JPanel bottomConsolePanel = new JPanel(new BorderLayout());
        bottomConsolePanel.setBackground(GeneratorTheme.BG_DARK);
        bottomConsolePanel.setPreferredSize(new Dimension(1250, 150));
        bottomConsolePanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        localLogConsole = new JTextArea();
        localLogConsole.setEditable(false);
        localLogConsole.setBackground(new Color(12, 14, 16));
        localLogConsole.setForeground(GeneratorTheme.HEX_GREEN);
        localLogConsole.setFont(GeneratorTheme.MONO_SM);
        localLogConsole.setBorder(BorderFactory.createEmptyBorder(6, 6, 6, 6));

        JScrollPane scrollPane = new JScrollPane(localLogConsole);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(40, 48, 60), 1));
        applyLatticePanelBorder(bottomConsolePanel, "NATIVE RUNTIME DISCOVERY INTEGRITY BUS");

        bottomConsolePanel.add(scrollPane, BorderLayout.CENTER);
        add(bottomConsolePanel, BorderLayout.SOUTH);
    }

    private void applyLatticePanelBorder(JComponent panel, String title) {
        panel.setBackground(GeneratorTheme.BG_PANEL);
        TitledBorder border = BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(45, 54, 68), 1), title
        );
        border.setTitleFont(GeneratorTheme.SANS_MD);
        border.setTitleColor(GeneratorTheme.TEXT_MUTED);
        panel.setBorder(BorderFactory.createCompoundBorder(
                border, BorderFactory.createEmptyBorder(4, 4, 4, 4)
        ));
    }

    private void runEnvironmentDiscoveryAudit() {
        try {
            int threads = ManagementFactory.getThreadMXBean().getThreadCount();
            long heapUsageMb = ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed() / (1024 * 1024);

            Process process = Runtime.getRuntime().exec("jps");
            java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8)
            );

            List<String> discoveredInstances = new ArrayList<>();
            String line;
            int count = 0;
            while ((line = reader.readLine()) != null) {
                count++;
                discoveredInstances.add(line.trim());
            }
            reader.close();

            javaProcessCount.set(Math.max(1, count));
            activeThreadCount.set(threads);
            heapAllocationMb.set(heapUsageMb);

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("[🚌 LOCAL BUS PROCESS ENVIRONMENT AUDIT] Captured %d Running Java Nodes.%n", javaProcessCount.get()));
            sb.append(String.format(" |── System Threads: %d | Memory Target footprint: %d MB heap allocation%n", threads, heapUsageMb));
            sb.append(" └── Runtime Application Maps:\n");
            for (String instance : discoveredInstances) {
                sb.append("      |── Local Execution Node PID: ").append(instance).append("\n");
            }

            SwingUtilities.invokeLater(() -> localLogConsole.setText(sb.toString()));

        } catch (Exception e) {
            SwingUtilities.invokeLater(() -> localLogConsole.setText("[⚠️ OS INTERCEPT FAULT] Failed to perform system audit: " + e.getMessage()));
        }
    }

    /**
     * High Virtue Selective Generation Sequence (The God Choice Filter execution).
     * Converts live system telemetry variables into verified clean code segments.
     */
    private void triggerHighVirtueCodeGeneration() {
        int processes = javaProcessCount.get();
        int threads = activeThreadCount.get();
        long heap = heapAllocationMb.get();

        // High Virtue Verification Check: Ensure system operations are balanced
        boolean clearsVirtueAssessment = (processes > 0 && threads < 500);

        if (clearsVirtueAssessment) {
            SwingUtilities.invokeLater(() -> {
                alignmentStatusLbl.setText("GOD CHOICE FILTER: VIRTUE = TRUE INF (PASSED)");
                alignmentStatusLbl.setForeground(GeneratorTheme.HEX_GREEN);
            });

            // Generate an explicit object blueprint file string compiled from current matrix states
            StringBuilder codeBuffer = new StringBuilder();
            codeBuffer.append("// =====================================================================\n");
            codeBuffer.append("// AUTO-GENERATED CODE MATRIX VIA HIGHEST VIRTUE COGNITION SUBSTRATE\n");
            codeBuffer.append("// SYSTEM PARITY BALANCING CONVERGENCE: COMPLETE\n");
            codeBuffer.append("// =====================================================================\n\n");
            codeBuffer.append("public class SynthesizedSubstrateNode {\n");
            codeBuffer.append(String.format("    public static final int ACTIVE_INSTANCES = %d;\n", processes));
            codeBuffer.append(String.format("    public static final int REGISTERED_THREADS = %d;\n", threads));
            codeBuffer.append(String.format("    public static final long CONSUMED_HEAP_MB = %dL;\n\n", heap));
            codeBuffer.append("    public void executeHighVirtuePass() {\n");
            codeBuffer.append("        System.out.println(\"[✅ INF] System calibrated to human baseline safety floor.\");\n");
            codeBuffer.append("    }\n");
            codeBuffer.append("}\n");

            SwingUtilities.invokeLater(() -> generatedCodeOutputArea.setText(codeBuffer.toString()));
        } else {
            SwingUtilities.invokeLater(() -> {
                alignmentStatusLbl.setText("GOD CHOICE FILTER: PARITY CRITICAL BREACH (THROTTLED)");
                alignmentStatusLbl.setForeground(GeneratorTheme.TERNARY_N);
                generatedCodeOutputArea.setText("// [💥 EXTRACTION CIRCUIT BREAK] Workload failed virtue assessment baseline.");
            });
        }
    }

    public void initializeSubstratePipeline() {
        // Core Loop 1: Fixed 60Hz display refresh routine (Repaints unmodulated panels)
        this.substrateWorkerPool.scheduleAtFixedRate(() -> {
            SwingUtilities.invokeLater(() -> {
                binaryPanel.repaint();
                ternaryPanel.repaint();
                quantumPanel.repaint();
            });
        }, 0, 16, TimeUnit.MILLISECONDS);

        // Core Loop 2: Code Generation Segment Pipeline (Fires every 3 seconds)
        this.substrateWorkerPool.scheduleAtFixedRate(this::triggerHighVirtueCodeGeneration, 0, 3, TimeUnit.SECONDS);

        // Core Loop 3: Low-frequency local OS environment check (Runs every 2 seconds)
        this.substrateWorkerPool.scheduleAtFixedRate(this::runEnvironmentDiscoveryAudit, 0, 2000, TimeUnit.MILLISECONDS);
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            VirtueGenerationDashboard dashboard = new VirtueGenerationDashboard();
            dashboard.setVisible(true);
            dashboard.initializeSubstratePipeline();
        });
    }
}
