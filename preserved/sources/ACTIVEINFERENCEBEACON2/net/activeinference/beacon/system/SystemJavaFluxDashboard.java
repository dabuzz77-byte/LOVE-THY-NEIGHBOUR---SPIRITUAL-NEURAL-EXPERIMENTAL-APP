package net.activeinference.beacon.system;

import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.io.Serializable;
import java.lang.management.ManagementFactory;
import java.lang.management.RuntimeMXBean;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public class SystemJavaFluxDashboard extends JFrame implements Serializable {
    private static final long serialVersionUID = 783404L;

    private static final double SCHUMANN_CARRIER_HZ = 7.83;

    private final ScheduledExecutorService carrierThreadClock;
    private double waveTimeDelta = 0.0;

    // Concurrently managed metrics driving panel states
    private final AtomicInteger activeJavaProcessCount = new AtomicInteger(1);
    private final AtomicInteger globalActiveThreadCount = new AtomicInteger(10);
    private final AtomicLong combinedHeapAllocationMb = new AtomicLong(256);

    private SystemBinaryPanel binaryPanel;
    private SystemTernaryPanel ternaryPanel;
    private SystemQuantumPanel quantumPanel;
    private JTextArea telemetryConsole;
    private JLabel waveTelemetryLbl;

    public SystemJavaFluxDashboard() {
        this.carrierThreadClock = Executors.newScheduledThreadPool(2);

        setTitle("System JVM Active Process Interception Matrix");
        setSize(1150, 650);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(DashboardTheme.BG_DARK);
        setLayout(new BorderLayout(10, 10));

        buildGraphicalLayout();
    }

    private void buildGraphicalLayout() {
        JPanel masthead = new JPanel(new BorderLayout());
        masthead.setBackground(DashboardTheme.BG_PANEL);
        masthead.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));

        JLabel titleLbl = new JLabel("⚡ LIVE JVM BUS SUBSYSTEM & RESONANCE CARRIER COUPLING GRID");
        titleLbl.setFont(DashboardTheme.SANS_MD);
        titleLbl.setForeground(DashboardTheme.TEXT_LIGHT);

        waveTelemetryLbl = new JLabel("CARRIER FREQUENCY: 7.83 HZ LOCK");
        waveTelemetryLbl.setFont(new Font("Monospaced", Font.BOLD, 11));
        waveTelemetryLbl.setForeground(DashboardTheme.HEX_GREEN);

        masthead.add(titleLbl, BorderLayout.WEST);
        masthead.add(waveTelemetryLbl, BorderLayout.EAST);
        add(masthead, BorderLayout.NORTH);

        JPanel centerGrid = new JPanel(new GridLayout(1, 3, 10, 10));
        centerGrid.setBackground(DashboardTheme.BG_DARK);
        centerGrid.setBorder(BorderFactory.createEmptyBorder(0, 10, 0, 10));

        binaryPanel = new SystemBinaryPanel(activeJavaProcessCount);
        applyLatticePanelStyle(binaryPanel, "BINARY MODULATION (JAVA PROCESS COUNT)");

        ternaryPanel = new SystemTernaryPanel(globalActiveThreadCount);
        applyLatticePanelStyle(ternaryPanel, "BALANCED TERNARY SYSTEM FIELD (ACTIVE THREADS)");

        quantumPanel = new SystemQuantumPanel(combinedHeapAllocationMb);
        applyLatticePanelStyle(quantumPanel, "QUANTUM PROBABILITY PHASE AMPLITUDES (HEAP LOAD)");

        centerGrid.add(binaryPanel);
        centerGrid.add(ternaryPanel);
        centerGrid.add(quantumPanel);
        add(centerGrid, BorderLayout.CENTER);

        JPanel lowerConsolePanel = new JPanel(new BorderLayout());
        lowerConsolePanel.setBackground(DashboardTheme.BG_DARK);
        lowerConsolePanel.setPreferredSize(new Dimension(1150, 180));
        lowerConsolePanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        telemetryConsole = new JTextArea();
        telemetryConsole.setEditable(false);
        telemetryConsole.setBackground(new Color(12, 15, 20));
        telemetryConsole.setForeground(DashboardTheme.HEX_GREEN);
        telemetryConsole.setFont(DashboardTheme.MONO_SM);
        telemetryConsole.setBorder(BorderFactory.createEmptyBorder(8, 8, 8, 8));

        JScrollPane scrollPane = new JScrollPane(telemetryConsole);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(40, 48, 60), 1));
        applyLatticePanelStyle(lowerConsolePanel, "NATIVE RUNTIME KERNEL INTERCEPT MATRIX");

        lowerConsolePanel.add(scrollPane, BorderLayout.CENTER);
        add(lowerConsolePanel, BorderLayout.SOUTH);
    }

    private void applyLatticePanelStyle(JPanel panel, String title) {
        panel.setBackground(DashboardTheme.BG_PANEL);
        TitledBorder border = BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(40, 48, 60), 1), title
        );
        border.setTitleFont(DashboardTheme.SANS_MD);
        border.setTitleColor(DashboardTheme.TEXT_MUTED);
        panel.setBorder(BorderFactory.createCompoundBorder(
                border, BorderFactory.createEmptyBorder(8, 8, 8, 8)
        ));
    }

    private void executeNativeProcessAudit() {
        try {
            java.lang.management.ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
            java.lang.management.MemoryMXBean memoryMXBean = ManagementFactory.getMemoryMXBean();

            int threads = threadMXBean.getThreadCount();
            long heapMb = memoryMXBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);

            Process process = Runtime.getRuntime().exec("jps");
            java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(process.getInputStream())
            );

            List<String> discoveredInstances = new ArrayList<>();
            String line;
            int count = 0;
            while ((line = reader.readLine()) != null) {
                count++;
                discoveredInstances.add(line.trim());
            }
            reader.close();

            activeJavaProcessCount.set(Math.max(1, count));
            globalActiveThreadCount.set(threads);
            combinedHeapAllocationMb.set(heapMb);

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("[🚌 SYSTEM BUS AUDIT] Synchronized: %d Active Java Instances Found.%n", activeJavaProcessCount.get()));
            sb.append(String.format(" |── Host JVM Active Thread Space Depth: %d threads%n", threads));
            sb.append(String.format(" |── Monitored Substrate Memory Footprint: %d MB allocated heap%n", heapMb));
            sb.append(" └── Discovered System Processes:\n");
            for (String instance : discoveredInstances) {
                sb.append("      |── PID/Descriptor: ").append(instance).append("\n");
            }

            SwingUtilities.invokeLater(() -> telemetryConsole.setText(sb.toString()));

        } catch (Exception e) {
            SwingUtilities.invokeLater(() -> telemetryConsole.setText("[⚠️ OS ERROR] Process scanning protocol failed:\n" + e.getMessage()));
        }
    }

    public void activateSystemFluxSubstrate() {
        long intervalMicros = (long) ((1.0 / SCHUMANN_CARRIER_HZ) * 1_000_000.0);

        this.carrierThreadClock.scheduleAtFixedRate(() -> {
            waveTimeDelta += 0.075;

            SwingUtilities.invokeLater(() -> {
                waveTelemetryLbl.setText(String.format("CARRIER: SYNC_LOCKED | TARGET: %.2f Hz | VECTOR: %.2f rad", SCHUMANN_CARRIER_HZ, waveTimeDelta));
                binaryPanel.setWaveTimeDelta(waveTimeDelta);
                ternaryPanel.setWaveTimeDelta(waveTimeDelta);
                quantumPanel.setWaveTimeDelta(waveTimeDelta);
                
                binaryPanel.repaint();
                ternaryPanel.repaint();
                quantumPanel.repaint();
            });
        }, 0, intervalMicros, TimeUnit.MICROSECONDS);

        this.carrierThreadClock.scheduleAtFixedRate(this::executeNativeProcessAudit, 0, 2500, TimeUnit.MILLISECONDS);
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            SystemJavaFluxDashboard applicationEngine = new SystemJavaFluxDashboard();
            applicationEngine.setVisible(true);
            applicationEngine.activateSystemFluxSubstrate();
        });
    }
}
