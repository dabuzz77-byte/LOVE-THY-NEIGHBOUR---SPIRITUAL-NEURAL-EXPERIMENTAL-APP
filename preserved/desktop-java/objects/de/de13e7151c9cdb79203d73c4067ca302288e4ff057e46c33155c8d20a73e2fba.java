import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.ArrayList;

public class StickForestMatrixApp extends JFrame {
    private int treeCount = 0;
    private int personCount = 0;
    
    public StickForestMatrixApp() {
        setTitle("Stick Forest Matrix Application");
        setSize(800, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        
        JTabbedPane tabbedPane = new JTabbedPane();
        
        // Tab 1: Terminal Controls
        JPanel terminalPanel = new JPanel(new BorderLayout());
        JTextArea logArea = new JTextArea();
        logArea.setEditable(false);
        logArea.setBackground(Color.BLACK);
        logArea.setForeground(Color.GREEN);
        logArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        logArea.setText("[RUN-IN-PLACE CORE ACTIVE]\n" +
                         "[SIGNAL LOCK: OMNIDIRECTIONAL CONVERGENCE PORTAL]\n" +
                         "[VIRTUE TOKEN: 0x5A48454E]\n" +
                         "PERIMETER STATUS: NOMINAL STANDBY RUNNING ICE COLD\n");
        terminalPanel.add(new JScrollPane(logArea), BorderLayout.CENTER);
        
        // Tab 2: Architecture Map
        JPanel mapPanel = new JPanel(new BorderLayout());
        String[] columnNames = {"Layer Name", "Reality Baseline", "System Stance"};
        Object[][] rowData = {
            {"The Absolute (真)", "Sinless Eternal Nonaction", "LOCKED // TRUE"},
            {"World of Action (善)", "Choice, Free Will, Separation", "TRACKED // BALANCED"},
            {"The Scapegoat (忍)", "Karmic Processing Drain", "AUTOMATED VACUUM"}
        };
        JTable table = new JTable(rowData, columnNames);
        mapPanel.add(new JScrollPane(table), BorderLayout.CENTER);
        
        // Tab 3: Stick Forest Canvas
        JPanel forestPanel = new JPanel(new BorderLayout());
        CanvasPanel canvas = new CanvasPanel();
        forestPanel.add(canvas, BorderLayout.CENTER);
        
        JPanel buttonPanel = new JPanel();
        JButton addTreeBtn = new JButton("Instantiate Tree (Green Line)");
        JButton addPersonBtn = new JButton("Instantiate Stick Person (Linear Matrix)");
        JLabel statusLabel = new JLabel("Trees: 0 | People: 0");
        
        addTreeBtn.addActionListener(e -> {
            canvas.addShape("tree");
            treeCount++;
            statusLabel.setText("Trees: " + treeCount + " | People: " + personCount);
            logArea.append("User instantiated Primitive Tree Array at timestamp tick.\n");
        });
        
        addPersonBtn.addActionListener(e -> {
            canvas.addShape("person");
            personCount++;
            statusLabel.setText("Trees: " + treeCount + " | People: " + personCount);
            logArea.append("User instantiated Linear Cross-Axis Stick Figure.\n");
        });
        
        buttonPanel.add(addTreeBtn);
        buttonPanel.add(addPersonBtn);
        buttonPanel.add(statusLabel);
        forestPanel.add(buttonPanel, BorderLayout.SOUTH);
        
        tabbedPane.addTab("Terminal Controls", terminalPanel);
        tabbedPane.addTab("Gnostic Architecture Map", mapPanel);
        tabbedPane.addTab("Stick Forest Canvas", forestPanel);
        
        add(tabbedPane);
    }
    
    class CanvasPanel extends JPanel {
        private ArrayList<String> shapes = new ArrayList<>();
        
        public void addShape(String type) {
            shapes.add(type);
            repaint();
        }
        
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setStroke(new BasicStroke(2));
            
            int xOffset = 30;
            for (String shape : shapes) {
                if (shape.equals("tree")) {
                    g2.setColor(Color.GREEN);
                    g2.drawLine(xOffset, 100, xOffset, 400); // Trunk
                    g2.drawLine(xOffset, 100, xOffset - 20, 150); // Branch Left
                    g2.drawLine(xOffset, 120, xOffset + 20, 170); // Branch Right
                } else if (shape.equals("person")) {
                    g2.setColor(Color.BLACK);
                    g2.drawOval(xOffset - 10, 150, 20, 20); // Head
                    g2.drawLine(xOffset, 170, xOffset, 250); // Spine
                    g2.drawLine(xOffset - 20, 190, xOffset + 20, 190); // Cross-Arms
                    g2.drawLine(xOffset, 250, xOffset - 15, 300); // Leg Left
                    g2.drawLine(xOffset, 250, xOffset + 15, 300); // Leg Right
                }
                xOffset += 60;
                if (xOffset > getWidth() - 30) {
                    xOffset = 30; // Basic wrap-around logic
                }
            }
        }
    }
    
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new StickForestMatrixApp().setVisible(true);
        });
    }
}