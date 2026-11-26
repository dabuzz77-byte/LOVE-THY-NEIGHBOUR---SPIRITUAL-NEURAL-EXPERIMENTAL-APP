package net.activeinference.beacon.carrier;
import neural.studio.*;


import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.io.Serializable;
import java.lang.management.ManagementFactory;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public class CarrierWaveInferenceDashboard extends SectionFrame implements Serializable {
    private static final long serialVersionUID = 783601L;

    private static final double SCHUMANN_CARRIER_HZ = 7.83;
    private static final String TARGET_HOST = "127.0.0.1";
    private static final int TARGET_PORT = 7830;

    private final ScheduledExecutorService transmissionScheduler;
    private double carrierPhaseAngle = 0.0;

    // Telemetry tracking registers (Synchronized with Part 2 variable calls)
    private final AtomicInteger javaProcessCount = new AtomicInteger(1);
    private final AtomicInteger activeThreadCount = new AtomicInteger(10);
    private final AtomicLong heapAllocationMb = new AtomicLong(256);

    private UnmodulatedBinaryPanel binaryPanel;
    private UnmodulatedTernaryPanel ternaryPanel;
    private UnmodulatedQuantumPanel quantumPanel;
    private JTextArea localLogConsole;
    private JLabel transmissionNetworkLbl;

    public CarrierWaveInferenceDashboard() {
        this.transmissionScheduler = SharedScheduler.newScheduledThreadPool(3);

        setTitle("Raw Substrate Network Ingress Monitor // 7.83Hz Carrier Node");
        setSize(1180, 660);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(CarrierTheme.BG_DARK);
        setLayout(new BorderLayout(10, 10));

        assembleGraphicalInterface();
    }

    private void assembleGraphicalInterface() {
        JPanel masthead = new JPanel(new BorderLayout());
        masthead.setBackground(CarrierTheme.BG_PANEL);
        masthead.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));

        JLabel titleLbl = new JLabel("⚡ UNMODULATED BALANCED SUBSYSTEM METRICS ──► TRANSMITTING COMPRESSED 7.83HZ CARRIER WAVES");
        titleLbl.setFont(CarrierTheme.SANS_MD);
        titleLbl.setForeground(CarrierTheme.TEXT_LIGHT);

        transmissionNetworkLbl = new JLabel("NET OUTBOUND: CONNECTING...");
        transmissionNetworkLbl.setFont(new Font("Monospaced", Font.BOLD, 11));
        transmissionNetworkLbl.setForeground(CarrierTheme.TERNARY_P);

        masthead.add(titleLbl, BorderLayout.WEST);
        masthead.add(transmissionNetworkLbl, BorderLayout.EAST);
        add(masthead, BorderLayout.NORTH);

        JPanel centralGridPanel = new JPanel(new GridLayout(1, 3, 10, 10));
        centralGridPanel.setBackground(CarrierTheme.BG_DARK);
        centralGridPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 0, 10));

        binaryPanel = new UnmodulatedBinaryPanel(javaProcessCount);
        applyLatticePanelBorder(binaryPanel, "RAW BINARY PROCESSING SUBSYSTEM (UNMODULATED)");

        ternaryPanel = new UnmodulatedTernaryPanel(activeThreadCount);
        applyLatticePanelBorder(ternaryPanel, "RAW BALANCED TERNARY ENCODING FIELD (UNMODULATED)");

        quantumPanel = new UnmodulatedQuantumPanel(heapAllocationMb);
        applyLatticePanelBorder(quantumPanel, "RAW HEAP AMBIENT COHERENCE MATRIX (UNMODULATED)");

        centralGridPanel.add(binaryPanel);
        centralGridPanel.add(ternaryPanel);
        centralGridPanel.add(quantumPanel);
        add(centralGridPanel, BorderLayout.CENTER);

        JPanel bottomConsolePanel = new JPanel(new BorderLayout());
        bottomConsolePanel.setBackground(CarrierTheme.BG_DARK);
        bottomConsolePanel.setPreferredSize(new Dimension(1180, 180));
        bottomConsolePanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));

        localLogConsole = new JTextArea();
        localLogConsole.setEditable(false);
        localLogConsole.setBackground(new Color(10, 12, 14));
        localLogConsole.setForeground(CarrierTheme.HEX_GREEN);
        localLogConsole.setFont(CarrierTheme.MONO_SM);
        localLogConsole.setBorder(BorderFactory.createEmptyBorder(8, 8, 8, 8));

        JScrollPane scrollPane = new JScrollPane(localLogConsole);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(40, 48, 60), 1));
        applyLatticePanelBorder(bottomConsolePanel, "LOCAL SUBSTRATE RAW DISCOVERY TRACE BUS");

        bottomConsolePanel.add(scrollPane, BorderLayout.CENTER);
        add(bottomConsolePanel, BorderLayout.SOUTH);
    }

    private void applyLatticePanelBorder(JPanel panel, String title) {
        panel.setBackground(CarrierTheme.BG_PANEL);
        TitledBorder border = BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(45, 54, 68), 1), title
        );
        border.setTitleFont(CarrierTheme.SANS_MD);
        border.setTitleColor(CarrierTheme.TEXT_MUTED);
        panel.setBorder(BorderFactory.createCompoundBorder(
                border, BorderFactory.createEmptyBorder(8, 8, 8, 8)
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

            List<String> logs = new ArrayList<>();
            String line;
            int instanceCount = 0;
            while ((line = reader.readLine()) != null) {
                instanceCount++;
                logs.add(line.trim());
            }
            reader.close();

            javaProcessCount.set(Math.max(1, instanceCount));
            activeThreadCount.set(threads);
            heapAllocationMb.set(heapUsageMb);

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("[🚌 RAW RUNTIME SYSTEM AUDIT] Captured %d Active Java Instances.%n", javaProcessCount.get()));
            sb.append(String.format(" |── Active Threads: %d | Direct Core Memory Consumption: %d MB heap%n", threads, heapUsageMb));
            sb.append(" └── Runtime Application Trace Map:\n");
            for (String instance : logs) {
                sb.append("      |── PID Target Node: ").append(instance).append("\n");
            }

            SwingUtilities.invokeLater(() -> localLogConsole.setText(sb.toString()));

        } catch (Exception e) {
            SwingUtilities.invokeLater(() -> localLogConsole.setText("[⚠️ INTERCEPT ERROR] Failed to perform system audit: " + e.getMessage()));
        }
    }

    public void initializeSubstratePipeline() {
        // Core Loop 1: Fixed 60Hz display refresh routine (Repaints unmodulated grids)
        this.transmissionScheduler.scheduleAtFixedRate(() -> {
            SwingUtilities.invokeLater(() -> {
                binaryPanel.repaint();
                ternaryPanel.repaint();
                quantumPanel.repaint();
            });
        }, 0, 16, TimeUnit.MILLISECONDS);

        // Core Loop 2: 7.83Hz Network Transmission Loop (Modulated by Carrier wave variables)
        long schumannIntervalMicros = (long) ((1.0 / SCHUMANN_CARRIER_HZ) * 1_000_000.0);
        this.transmissionScheduler.scheduleAtFixedRate(() -> {
            this.carrierPhaseAngle += 0.085;
            double schumannCarrierAmplitude = Math.sin(this.carrierPhaseAngle);

            // Serialize current unmodulated state parameters into a data frame
            String compiledPayload = String.format(
                "{\"processes\": %d, \"threads\": %d, \"heap_mb\": %d, \"carrier_phase\": %.4f, \"amplitude\": %.4f}",
                javaProcessCount.get(), activeThreadCount.get(), heapAllocationMb.get(), this.carrierPhaseAngle, schumannCarrierAmplitude
            );

            // Open a physical connection across the local network interface card
            try (Socket liveSocket = new Socket(TARGET_HOST, TARGET_PORT);
                 OutputStream stream = liveSocket.getOutputStream();
                 PrintWriter networkWriter = new PrintWriter(stream, true, StandardCharsets.UTF_8)) {

                // Stream the serialized data frame over raw network channels
                networkWriter.println(compiledPayload);

                SwingUtilities.invokeLater(() -> {
                    transmissionNetworkLbl.setText(String.format("TX ACTIVE // %s:%d // FREQ: %.2f HZ // MOD: %.3f", 
                            TARGET_HOST, TARGET_PORT, SCHUMANN_CARRIER_HZ, schumannCarrierAmplitude));
                });

            } catch (java.net.ConnectException ce) {
                SwingUtilities.invokeLater(() -> {
                    transmissionNetworkLbl.setText("TX BLOCKED: LOCAL PORT CLOSED / LISTENER DISCONNECTED");
                    transmissionNetworkLbl.setForeground(CarrierTheme.TERNARY_N);
                });
            } catch (Exception e) {
                System.err.println("[❌ NETWORK EXCEPTION] Frame dropped: " + e.getMessage());
            }

        }, 0, schumannIntervalMicros, TimeUnit.MICROSECONDS);

        // Core Loop 3: Low-frequency local OS environment check (Runs every 2 seconds)
        this.transmissionScheduler.scheduleAtFixedRate(this::runEnvironmentDiscoveryAudit, 0, 2000, TimeUnit.MILLISECONDS);
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> {
            CarrierWaveInferenceDashboard appDashboard = new CarrierWaveInferenceDashboard();
            appDashboard.setVisible(true);
            appDashboard.initializeSubstratePipeline();
        });
    }
}
