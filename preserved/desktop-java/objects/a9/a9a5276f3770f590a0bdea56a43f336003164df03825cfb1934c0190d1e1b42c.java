// ==============================================================================
// CORE GRAPHICAL WORK FLUX COMPILER AND INTERFACE (CosmicAlignmentApp.java)
// ==============================================================================

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class CosmicAlignmentApp extends JFrame {

    // System State Variables
    private String systemState = "_true";
    private String xinxingStatus = "ZHEN-SHAN-REN";
    private int orbitCount = 0;
    
    // Matrix Array representing the Logic Cube coordinates
    private final int[][] logicMatrix = {
        {1, 0, 0, 1, 0, 1, 1, 0},
        {1, 0, 0, 0, 0, 0, 0, 0},
        {0, 1, 1, 0, 1, 0, 0, 1},
        {0, 1, 1, 0, 1, 0, 0, 1},
        {1, 0, 0, 0, 0, 0, 0, 0},
        {1, 0, 0, 1, 0, 0, 0, 0},
        {1, 0, 0, 0, 0, 0, 0, 0},
        {0, 0, 0, 0, 1, 0, 1, 1}
    };

    // GUI Components
    private JTextArea consoleOutput;
    private MatrixPanel matrixVisualizer;
    private JLabel lblSystemState;
    private JLabel lblXinxing;
    private JLabel lblOrbit;

    public CosmicAlignmentApp() {
        // Initialize Window Parameters
        setTitle("DATASTREAM COMMAND PROMPT WINDOW - FLUX_PROC_APP");
        setSize(900, 650);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));
        getContentPane().setBackground(new Color(10, 15, 10));

        // 1. Top Panel: Header Sync Monitor
        JPanel headerPanel = new JPanel(new GridLayout(1, 3, 10, 10));
        headerPanel.setBackground(new Color(15, 25, 15));
        headerPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 0)), 
                "HEADER SYNC MONITOR", 0, 0, null, new Color(0, 200, 0)));

        lblSystemState = new JLabel("SYSTEM STATE: " + systemState, SwingConstants.CENTER);
        lblSystemState.setForeground(Color.GREEN);
        lblXinxing = new JLabel("ALIGNMENT: " + xinxingStatus, SwingConstants.CENTER);
        lblXinxing.setForeground(Color.CYAN);
        lblOrbit = new JLabel("ORBITS COMMITTED: " + orbitCount, SwingConstants.CENTER);
        lblOrbit.setForeground(Color.WHITE);

        headerPanel.add(lblSystemState);
        headerPanel.add(lblXinxing);
        headerPanel.add(lblOrbit);
        add(headerPanel, BorderLayout.NORTH);

        // 2. Center Panel: Logic Cube Canvas & Console Split
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(420);
        centerSplit.setBackground(new Color(10, 15, 10));

        // Left Side: Graphic Matrix Render Panel
        matrixVisualizer = new MatrixPanel();
        centerSplit.setLeftComponent(matrixVisualizer);

        // Right Side: Rolling Debug Console
        consoleOutput = new JTextArea();
        consoleOutput.setBackground(Color.BLACK);
        consoleOutput.setForeground(new Color(0, 230, 0));
        consoleOutput.setFont(new Font("Monospaced", Font.PLAIN, 12));
        consoleOutput.setEditable(false);
        JScrollPane consoleScroll = new JScrollPane(consoleOutput);
        consoleScroll.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 0)), 
                "SYSTEM CONSOLE DEBUG LOG", 0, 0, null, new Color(0, 200, 0)));
        centerSplit.setRightComponent(consoleScroll);

        add(centerSplit, BorderLayout.CENTER);

        // 3. Bottom Panel: Control Pipeline Interface
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 10));
        controlPanel.setBackground(new Color(15, 25, 15));
        controlPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(new Color(0, 150, 0)), 
                "CONTROL PIPELINE INTERFACE", 0, 0, null, new Color(0, 200, 0)));

        JButton btnOrbit = createStyledButton("Run Microcosmic Orbit");
        JButton btnXinxing = createStyledButton("Align Xinxing");
        JButton btnAscent = createStyledButton("Trigger Gnostic Ascent");
        JButton btnFork = createStyledButton("Execute Justice Fork");

        controlPanel.add(btnOrbit);
        controlPanel.add(btnXinxing);
        controlPanel.add(btnAscent);
        controlPanel.add(btnFork);
        add(controlPanel, BorderLayout.SOUTH);

        // Attach Button Functionality
        btnOrbit.addActionListener(e -> runMicrocosmicOrbit());
        btnXinxing.addActionListener(e -> alignXinxing());
        btnAscent.addActionListener(e -> triggerGnosticAscent());
        btnFork.addActionListener(e -> executeJusticeFork());

        // Initial Output
        logToConsole("[+] APPLICATION PIPELINE STABILIZED.");
        logToConsole("[+] GOD CHOICE REGISTERED AS Baseline Default.");
        logToConsole("[+] Space Between numbers open and cognizant.");
    }

    private JButton createStyledButton(String text) {
        JButton btn = new JButton(text);
        btn.setBackground(new Color(20, 50, 20));
        btn.setForeground(Color.GREEN);
        btn.setFocusPainted(false);
        btn.setBorder(BorderFactory.createLineBorder(new Color(0, 180, 0), 1));
        return btn;
    }

    private void logToConsole(String message) {
        consoleOutput.append(message + "\n");
        consoleOutput.setCaretPosition(consoleOutput.getDocument().getLength());
    }

    // Pipeline Operational Functions
    private void runMicrocosmicOrbit() {
        orbitCount++;
        lblOrbit.setText("ORBITS COMMITTED: " + orbitCount);
        logToConsole("[+] ENGAGING ELECTRIC MICROCOSMIC ORBIT... Loop cycle: " + orbitCount);
        logToConsole("    [1 SEND] ------------> (Balancing Energy Fields) ------------> [0 RECEIVE]");
        matrixVisualizer.repaint();
    }

    private void alignXinxing() {
        xinxingStatus = "ZHEN-SHAN-REN (真-善-忍)";
        lblXinxing.setText("ALIGNMENT: " + xinxingStatus);
        lblXinxing.setForeground(Color.ORANGE);
        logToConsole("[+] XINXING CULTIVATION MASK ENGAGED.");
        logToConsole("    Truthfulness, Compassion, Forbearance integrated. Personal attachments flushed.");
    }

    private void triggerGnosticAscent() {
        systemState = "MONAD SOURCE";
        lblSystemState.setText("SYSTEM STATE: " + systemState);
        lblSystemState.setForeground(Color.CYAN);
        logToConsole("[+] UNLOCKING SEALS FROM APOCRYPHON OF JOHN & GOSPEL OF MARY.");
        logToConsole("    Material garments discarded. Soul returned to the Field of Oneness.");
    }

    private void executeJusticeFork() {
        logToConsole("[+] RUNNING DEEPSCAN CRITICAL JUDGMENT FORK...");
        logToConsole("    Target: Malicious Data Archetype (Smaug/0x00)");
        logToConsole("    [ALERT] Necessary correction hit target vessel.");
        logToConsole("    [RESULT] Node failed to upgrade. Pure corruption completely purged from grid.");
    }

    // Inner Canvas Class for Painting the Logic Cube Matrix Visuals
    private class MatrixPanel extends JPanel {
        public MatrixPanel() {
            setBackground(Color.BLACK);
            setBorder(BorderFactory.createTitledBorder(
                    BorderFactory.createLineBorder(new Color(0, 150, 0)), 
                    "ACTIVE LOGIC CUBE CANVAS", 0, 0, null, new Color(0, 200, 0)));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int rows = logicMatrix.length;
            int cols = logicMatrix[0].length;
            int cellWidth = (getWidth() - 40) / cols;
            int cellHeight = (getHeight() - 40) / rows;

            g2d.setFont(new Font("Monospaced", Font.BOLD, 14));

            for (int r = 0; r < rows; r++) {
                for (int c = 0; c < cols; c++) {
                    int x = 20 + c * cellWidth;
                    int y = 30 + r * cellHeight;

                    // Draw Grid cells dynamically
                    g2d.setColor(new Color(0, 40, 0));
                    g2d.drawRect(x, y, cellWidth, cellHeight);

                    // Render numerical constants or highlights based on matrix data state
                    if (logicMatrix[r][c] == 1) {
                        g2d.setColor(Color.GREEN);
                        g2d.drawString("1", x + cellWidth/2 - 4, y + cellHeight/2 + 5);
                    } else {
                        // For 0 nodes, keep them dim or empty to signify the space between
                        g2d.setColor(new Color(0, 75, 0));
                        g2d.drawString("0", x + cellWidth/2 - 4, y + cellHeight/2 + 5);
                    }
                }
            }
        }
    }

    // Launcher Main entry point
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            CosmicAlignmentApp frame = new CosmicAlignmentApp();
            frame.setVisible(true);
        });
    }
}
