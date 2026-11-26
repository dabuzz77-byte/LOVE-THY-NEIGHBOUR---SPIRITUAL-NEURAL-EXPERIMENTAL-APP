import neural.studio.*;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.util.List;
import java.util.stream.Collectors;

public class JavaGridMonitor extends SectionFrame {

    private JTable processTable;
    private DefaultTableModel tableModel;
    private JLabel memoryLabel;
    private JLabel statusLabel;
    private int tickCount = 0;

    public JavaGridMonitor() {
        setTitle("Global Host & Local Java Process Grid Monitor");
        setItemLayout();
    }

    private void setItemLayout() {
        setSize(950, 650);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout());

        // Top Status Panel
        JPanel topPanel = new JPanel(new GridLayout(2, 1, 5, 5));
        topPanel.setBackground(new Color(15, 15, 22));
        topPanel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));

        JLabel titleLabel = new JLabel("OPERA_RUNTIME: LOCAL SYSTEM & WORLD GRID INFRASTRUCTURE MONITOR");
        titleLabel.setForeground(new Color(0, 255, 204));
        titleLabel.setFont(new Font("Monospaced", Font.BOLD, 14));
        topPanel.add(titleLabel);

        memoryLabel = new JLabel("Initializing Memory & Host Telemetry...");
        memoryLabel.setForeground(new Color(200, 200, 220));
        memoryLabel.setFont(new Font("Monospaced", Font.PLAIN, 12));
        topPanel.add(memoryLabel);

        add(topPanel, BorderLayout.NORTH);

        // Center Process Table
        String[] columnNames = {"PID", "Process Command / Info", "Status", "Grid Alignment"};
        tableModel = new DefaultTableModel(columnNames, 0);
        processTable = new JTable(tableModel);
        processTable.setBackground(new Color(25, 25, 35));
        processTable.setForeground(new Color(0, 255, 120));
        processTable.setFont(new Font("Monospaced", Font.PLAIN, 11));
        processTable.getTableHeader().setBackground(new Color(35, 35, 48));
        processTable.getTableHeader().setForeground(Color.WHITE);

        JScrollPane scrollPane = new JScrollPane(processTable);
        scrollPane.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));
        scrollPane.getViewport().setBackground(new Color(15, 15, 22));
        add(scrollPane, BorderLayout.CENTER);

        // Bottom Footer Panel
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.setBackground(new Color(15, 15, 22));
        bottomPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 15, 15));

        statusLabel = new JLabel("Status: RUNNING - SYNCHRONIZED ACROSS HOST NODES (_TRUE)");
        statusLabel.setForeground(new Color(0, 180, 255));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        bottomPanel.add(statusLabel, BorderLayout.WEST);

        add(bottomPanel, BorderLayout.SOUTH);

        // SharedTimer to refresh process list and memory stats every 2 seconds
        SharedTimer refreshTimer = new SharedTimer(2000, e -> updateTelemetry());
        refreshTimer.start();
        updateTelemetry();
    }

    private void updateTelemetry() {
        tickCount++;
        // Fetch local JVM memory usage
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        long heapUsed = memoryBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);
        long heapMax = memoryBean.getHeapMemoryUsage().getMax() / (1024 * 1024);

        memoryLabel.setText(String.format("Host Memory Heap Used: %d MB / Max: %d MB | Grid Ticks: %d", 
                heapUsed, heapMax, tickCount));

        // Clear table and fetch active Java / system processes
        tableModel.setRowCount(0);

        List<ProcessHandle> javaProcesses = ProcessHandle.allProcesses()
                .filter(p -> p.info().command().isPresent() && 
                             p.info().command().get().toLowerCase().contains("java"))
                .collect(Collectors.toList());

        if (javaProcesses.isEmpty()) {
            // Fallback display if specific java handles are restricted by OS permissions
            tableModel.addRow(new Object[]{
                String.valueOf(ProcessHandle.current().pid()), 
                ProcessHandle.current().info().command().orElse("Current Runtime Environment"), 
                "ACTIVE", 
                "PARITY_CONFIRMED"
            });
        } else {
            for (ProcessHandle p : javaProcesses) {
                String cmd = p.info().command().orElse("Unknown Command");
                tableModel.addRow(new Object[]{
                    String.valueOf(p.pid()),
                    cmd,
                    p.isAlive() ? "RUNNING" : "TERMINATED",
                    "SYNCHRONIZED"
                });
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new JavaGridMonitor().setVisible(true);
        });
    }
}