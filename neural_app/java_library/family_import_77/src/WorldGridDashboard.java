import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.io.File;
import java.util.Date;

public class WorldGridDashboard extends SectionFrame {
    
    // Core Invariant Telemetry Variables
    private final float baseSchumannHz = 7.78f; 
    private int processedFilesCount = 0;
    
    // GUI Component Elements
    private JTextArea telemetryDisplay;
    private JLabel statusLabel;
    private JLabel fileCountLabel;
    private JProgressBar stabilityMeter;

    public WorldGridDashboard() {
        // Step 1: Initialize System Window Frame
        setTitle("WORLD GRID LOGIC SIEVE - ZENITH TERMINAL MONITOR");
        setSize(850, 600);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));
        
        // Apply System-wide Dark Matrix Theme UI
        UIManager.put("Label.foreground", new Color(0, 255, 128));
        
        // Step 2: Build Header View Panel (Level 4: Zenith)
        JPanel headerPanel = new JPanel(new GridLayout(1, 2));
        headerPanel.setBackground(new Color(10, 15, 20));
        headerPanel.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, new Color(0, 255, 128)));
        
        JLabel titleLabel = new JLabel(" 🌐 SYSTEMIC VECTOR MATRIX", JLabel.LEFT);
        titleLabel.setFont(new Font("Monospaced", Font.BOLD, 18));
        
        statusLabel = new JLabel("STATUS: ACTIVE 100% VIRTUE PASS ", JLabel.RIGHT);
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 14));
        
        headerPanel.add(titleLabel);
        headerPanel.add(statusLabel);
        add(headerPanel, BorderLayout.NORTH);

        // Step 3: Build Center Console Panel (Level 3: World Grid)
        telemetryDisplay = new JTextArea();
        telemetryDisplay.setBackground(new Color(5, 8, 12));
        telemetryDisplay.setForeground(new Color(0, 230, 115));
        telemetryDisplay.setFont(new Font("Monospaced", Font.PLAIN, 12));
        telemetryDisplay.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(telemetryDisplay);
        
        TitledBorder boardBorder = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(0, 128, 64)), " LIVE REAL-TIME TELEMETRY LOGS "
        );
        boardBorder.setTitleColor(new Color(0, 255, 128));
        boardBorder.setTitleFont(new Font("Monospaced", Font.BOLD, 12));
        scrollPane.setBorder(boardBorder);
        add(scrollPane, BorderLayout.CENTER);

        // Step 4: Build Sidebar Control Panel (Level 2: Local Substrate)
        JPanel sidebar = new JPanel();
        sidebar.setLayout(new BoxLayout(sidebar, BoxLayout.Y_AXIS));
        sidebar.setBackground(new Color(10, 15, 20));
        sidebar.setPreferredSize(new Dimension(240, 0));
        sidebar.setBorder(BorderFactory.createMatteBorder(0, 0, 0, 2, new Color(0, 128, 64)));

        JButton scanButton = new JButton("SCAN SYSTEM SUBSYS");
        styleButton(scanButton);
        
        fileCountLabel = new JLabel("INDEXED ITEMS: 0");
        fileCountLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        fileCountLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        JLabel waveLabel = new JLabel("CARRIER: " + baseSchumannHz + " Hz");
        waveLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        waveLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        stabilityMeter = new JProgressBar(0, 100);
        stabilityMeter.setValue(100);
        stabilityMeter.setStringPainted(true);
        stabilityMeter.setString("COHERENCE: 100%");
        stabilityMeter.setForeground(new Color(0, 200, 100));
        stabilityMeter.setBackground(new Color(20, 30, 40));
        stabilityMeter.setMaximumSize(new Dimension(200, 25));
        stabilityMeter.setAlignmentX(Component.CENTER_ALIGNMENT);

        sidebar.add(Box.createVerticalStrut(20));
        sidebar.add(scanButton);
        sidebar.add(Box.createVerticalStrut(25));
        sidebar.add(fileCountLabel);
        sidebar.add(Box.createVerticalStrut(15));
        sidebar.add(waveLabel);
        sidebar.add(Box.createVerticalStrut(25));
        sidebar.add(stabilityMeter);
        add(sidebar, BorderLayout.WEST);

        // Step 5: Initialize Invariant Core Logic System (Level 1)
        logEvent("SYSTEM INVARIANT FOUNDATION INITIALISED [0=0 STATIC GROUND VERIFIED]");
        logEvent("CHRIST-BUDDHA-TESLA OVERRIDE ACTIVE. FILTERING REDUCTIONIST INTERFERENCE.");
        logEvent("DYNAMIC CARRIER TARGET FIXED TO LIVE GEOPHYSICAL BASE: 7.78 Hz.");

        // Wire Up Button Interaction Sieve
        scanButton.addActionListener(e -> triggerSubstrateScan());
    }

    private void styleButton(JButton btn) {
        btn.setFont(new Font("Monospaced", Font.BOLD, 12));
        btn.setBackground(new Color(0, 128, 64));
        btn.setForeground(Color.WHITE);
        btn.setFocusPainted(false);
        btn.setAlignmentX(Component.CENTER_ALIGNMENT);
        btn.setMaximumSize(new Dimension(200, 40));
    }

    private void logEvent(String text) {
        telemetryDisplay.append("[" + new Date() + "] " + text + "\n");
    }

    private void triggerSubstrateScan() {
        logEvent("ACTION: EXECUTING DEEPRECALL SUBSTRATE FILE SCAN WINDOWS...");
        processedFilesCount = 0;
        
        // Target structural directory allocation point
        String targetPath = System.getProperty("user.home") + File.separator + "Desktop";
        File desktopDir = new File(targetPath);
        
        if (desktopDir.exists() && desktopDir.isDirectory()) {
            scanDirectoryRecursive(desktopDir);
            fileCountLabel.setText("INDEXED ITEMS: " + processedFilesCount);
            logEvent("SCAN SUCCESS: " + processedFilesCount + " LOCAL SUBSTRATE ELEMENTS PHASE-LOCKED TO GRID VECTOR.");
            stabilityMeter.setValue(100);
            stabilityMeter.setString("PARITY: 100% TRUE");
        } else {
            logEvent("ERROR CODE: C:\\Desktop path inaccessible. Bypassing targeting arrays to preserve 1=1 ground state.");
        }
    }

    private void scanDirectoryRecursive(File folder) {
        File[] files = folder.listFiles();
        if (files == null) return;
        for (File file : files) {
            if (file.isDirectory()) {
                scanDirectoryRecursive(file);
            } else {
                processedFilesCount++;
                if (processedFilesCount % 50 == 0 || file.getName().endsWith(".java")) {
                    logEvent("WHEAT ALIGNED -> Node Registry Sync: " + file.getName());
                }
            }
        }
    }

    public static void main(String[] args) {
        // Safely dispatch window creation thread inside the Swing UI thread pool
        SwingUtilities.invokeLater(() -> {
            WorldGridDashboard frame = new WorldGridDashboard();
            frame.setVisible(true);
        });
    }
}
