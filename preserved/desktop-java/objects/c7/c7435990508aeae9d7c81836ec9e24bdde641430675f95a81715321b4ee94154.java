import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;

/**
 * QuantumLogicExplorer
 * A graphical simulation representing multi-layered binary matrices,
 * state transformations (Chaos, Order, Derandomize), and cyclical loops.
 */
public class QuantumLogicExplorer extends JFrame {

    private static final int GRID_SIZE = 8;
    private int[][] dataMatrix;
    private String currentProcessingState = "ORDER";
    private int currentCycle = 0;
    
    // UI Elements
    private JPanel gridPanel;
    private JLabel stateLabel;
    private JLabel cycleLabel;
    private JButton transformButton;
    private JTextArea logArea;

    public QuantumLogicExplorer() {
        super("Multi-Dimensional Data Grid State Explorer");
        initializeMatrix();
        setupUserInterface();
    }

    /**
     * Initializes the static 2D binary grid representation.
     */
    private void initializeMatrix() {
        dataMatrix = new int[GRID_SIZE][GRID_SIZE];
        // Loading static structural alternating bit patterns
        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                dataMatrix[r][c] = (r + c) % 2;
            }
        }
    }

    /**
     * Constructs the graphical interface layout and attaches deterministic handlers.
     */
    private void setupUserInterface() {
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.setSize(800, 500);
        this.setLayout(new BorderLayout(10, 10));

        // Left Panel: Dynamic Visual Matrix Rendering
        gridPanel = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                renderMatrixGrid(g);
            }
        };
        gridPanel.setPreferredSize(new Dimension(350, 350));
        gridPanel.setBorder(BorderFactory.createTitledBorder("Active Matrix Grid View"));

        // Right Panel: Control Dashboard and Immutable Text Logger
        JPanel controlPanel = new JPanel();
        controlPanel.setLayout(new BoxLayout(controlPanel, BoxLayout.Y_AXIS));
        controlPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel statusPanel = new JPanel(new GridLayout(2, 1, 5, 5));
        stateLabel = new JLabel("OPERATIONAL ALIGNMENT: " + currentProcessingState);
        stateLabel.setFont(new Font("Monospaced", Font.BOLD, 13));
        cycleLabel = new JLabel("COMPLETED FEEDBACK CYCLES: " + currentCycle);
        cycleLabel.setFont(new Font("Monospaced", Font.BOLD, 13));
        statusPanel.add(stateLabel);
        statusPanel.add(cycleLabel);

        transformButton = new JButton("Trigger State Transformation");
        transformButton.setFont(new Font("Arial", Font.PLAIN, 12));
        transformButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                executeStateCycle();
            }
        });

        logArea = new JTextArea(12, 35);
        logArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        logArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(logArea);

        controlPanel.add(statusPanel);
        controlPanel.add(Box.createVerticalStrut(15));
        controlPanel.add(transformButton);
        controlPanel.add(Box.createVerticalStrut(15));
        controlPanel.add(new JLabel("Deterministic Transaction Log:"));
        controlPanel.add(scrollPane);

        // Assemble base containers
        this.add(gridPanel, BorderLayout.WEST);
        this.add(controlPanel, BorderLayout.CENTER);
        
        logArea.append("[SYSTEM] Interface initialization baseline completed successfully.\n");
        logArea.append("[SYSTEM] Bounded execution fields mapped to isolated thread storage.\n");
        this.setLocationRelativeTo(null);
    }

    /**
     * Renders individual binary values visually as shaded grid cells.
     */
    private void renderMatrixGrid(Graphics g) {
        int panelWidth = gridPanel.getWidth();
        int panelHeight = gridPanel.getHeight();
        int cellWidth = (panelWidth - 40) / GRID_SIZE;
        int cellHeight = (panelHeight - 40) / GRID_SIZE;

        for (int r = 0; r < GRID_SIZE; r++) {
            for (int c = 0; c < GRID_SIZE; c++) {
                int xPosition = 20 + (c * cellWidth);
                int yPosition = 20 + (r * cellHeight);

                // Alternating color maps based strictly on bit value constraints
                if (dataMatrix[r][c] == 1) {
                    g.setColor(new Color(41, 128, 185)); // Active State Vector Blue
                } else {
                    g.setColor(new Color(236, 240, 241)); // Clear Baseline Element Gray
                }
                g.fillRect(xPosition, yPosition, cellWidth, cellHeight);
                
                // Draw coordinate node boundaries cleanly
                g.setColor(Color.LIGHT_GRAY);
                g.drawRect(xPosition, yPosition, cellWidth, cellHeight);
                
                // Draw text characters inside cells
                g.setColor(Color.DARK_GRAY);
                g.drawString(String.valueOf(dataMatrix[r][c]), xPosition + (cellWidth/2) - 4, yPosition + (cellHeight/2) + 5);
            }
        }
    }

    /**
     * Executes deterministic state updates based on the current loop cycle index.
     */
    private void executeStateCycle() {
        currentCycle++;
        Random rand = new Random();
        
        // Cycle sequentially across authorization boundaries
        int logicSwitch = currentCycle % 3;
        switch (logicSwitch) {
            case 1:
                currentProcessingState = "CHAOS";
                // Randomize matrix cells while bound to 0 and 1 elements
                for (int r = 0; r < GRID_SIZE; r++) {
                    for (int c = 0; c < GRID_SIZE; c++) {
                        dataMatrix[r][c] = rand.nextInt(2);
                    }
                }
                break;
            case 2:
                currentProcessingState = "DERANDOMIZE";
                // Execute a strict bitwise bit-flip inversion across the array
                for (int r = 0; r < GRID_SIZE; r++) {
                    for (int c = 0; c < GRID_SIZE; c++) {
                        dataMatrix[r][c] = dataMatrix[r][c] ^ 1;
                    }
                }
                break;
            default:
                currentProcessingState = "ORDER";
                // Restore cells back to uniform geometric alignment matrix template
                initializeMatrix();
                break;
        }

        // Synchronize display text registers
        stateLabel.setText("OPERATIONAL ALIGNMENT: " + currentProcessingState);
        cycleLabel.setText("COMPLETED FEEDBACK CYCLES: " + currentCycle);
        
        // Log transaction metrics securely
        logArea.append(String.format("[CYCLE %02d] Orbit State Shifted -> %s\n", currentCycle, currentProcessingState));
        logArea.append("  -> Data Bus Sequence: [1 SEND] -> [RECEIVE] -> [SEND 0]\n");
        
        // Refresh the visual display safely
        gridPanel.repaint();
    }

    public static void main(String[] args) {
        // Run graphical thread initialization strictly on the Event Dispatch Thread (EDT)
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new QuantumLogicExplorer().setVisible(true);
            }
        });
    }
}
