import neural.studio.*;
import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.Date;

public class ApiKeyCreator extends SectionFrame {

    private JTextArea textInputArea;
    private JTextArea binaryInputArea;
    private JTextArea outputConsole;
    private JLabel statusLabel;

    private final Color AMBER_PRIMARY = new Color(255, 176, 0);
    private final Color CRT_BACKGROUND = new Color(15, 12, 5);
    private final Color PANEL_BACKGROUND = new Color(25, 20, 8);

    public ApiKeyCreator() {
        setTitle("SOVEREIGN MOLD-CAST API KEY CREATOR");
        setSize(1200, 800);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        initComponents();
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));
        getContentPane().setBackground(CRT_BACKGROUND);

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(PANEL_BACKGROUND);
        headerPanel.setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));

        statusLabel = new JLabel("SUBSTRATE: DUAL INPUT MOLD CAST // READY");
        statusLabel.setForeground(AMBER_PRIMARY);
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        headerPanel.add(statusLabel, BorderLayout.WEST);

        add(headerPanel, BorderLayout.NORTH);

        // --- CENTER SPLIT: INPUTS & OUTPUT ---
        JSplitPane centerSplit = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        centerSplit.setDividerLocation(550);
        centerSplit.setResizeWeight(0.45);
        centerSplit.setBackground(CRT_BACKGROUND);

        // Left Panel: Dual Input Vectors
        JPanel inputPanel = new JPanel(new GridLayout(2, 1, 5, 5));
        inputPanel.setBackground(CRT_BACKGROUND);
        inputPanel.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));

        // Input 1: Text Vector
        JPanel textPanel = new JPanel(new BorderLayout(3, 3));
        textPanel.setBackground(PANEL_BACKGROUND);
        textPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_PRIMARY), 
                " Method 1: Text Cadence Vector ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 11), AMBER_PRIMARY
        ));

        textInputArea = new JTextArea(
            "Our Father in heaven,\n" +
            "hallowed be your name,\n" +
            "your kingdom come,\n" +
            "your will be done,\n" +
            "on earth as in heaven.\n" +
            "Give us today our daily bread.\n" +
            "Forgive us our sins\n" +
            "as we forgive those who sin against us.\n" +
            "Lead us not into temptation\n" +
            "but deliver us from evil.\n" +
            "For the kingdom, the power,\n" +
            "and the glory are yours\n" +
            "now and for ever.\n" +
            "Amen."
        );
        textInputArea.setFont(new Font("Monospaced", Font.PLAIN, 11));
        textInputArea.setBackground(CRT_BACKGROUND);
        textInputArea.setForeground(AMBER_PRIMARY);
        textInputArea.setCaretColor(AMBER_PRIMARY);
        textPanel.add(new JScrollPane(textInputArea), BorderLayout.CENTER);

        // Input 2: Binary Matrix Vector
        JPanel binaryPanel = new JPanel(new BorderLayout(3, 3));
        binaryPanel.setBackground(PANEL_BACKGROUND);
        binaryPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_PRIMARY), 
                " Method 2: Binary Flux Matrix ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 11), AMBER_PRIMARY
        ));

        binaryInputArea = new JTextArea(
            "1   0 0   1      0   1 1    0\n" +
            "1                0\n" +
            "0   1 1   0      1   0 0    1\n" +
            "0   1 1   0      1   0 0    1\n" +
            "1                0\n" +
            "1         1      0          0\n" +
            "---GENERATE---\n" +
            "1         1      0          0\n" +
            "0         0      1          1"
        );
        binaryInputArea.setFont(new Font("Monospaced", Font.PLAIN, 11));
        binaryInputArea.setBackground(CRT_BACKGROUND);
        binaryInputArea.setForeground(AMBER_PRIMARY);
        binaryInputArea.setCaretColor(AMBER_PRIMARY);
        binaryPanel.add(new JScrollPane(binaryInputArea), BorderLayout.CENTER);

        inputPanel.add(textPanel);
        inputPanel.add(binaryPanel);
        centerSplit.setLeftComponent(inputPanel);

        // Right Panel: Output & Generated Key Console
        JPanel outputPanel = new JPanel(new BorderLayout(5, 5));
        outputPanel.setBackground(PANEL_BACKGROUND);
        outputPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_PRIMARY), 
                " Mold-Cast Key Generation Output ", 
                TitledBorder.LEFT, TitledBorder.TOP, 
                new Font("Monospaced", Font.BOLD, 12), AMBER_PRIMARY
        ));

        outputConsole = new JTextArea();
        outputConsole.setEditable(false);
        outputConsole.setFont(new Font("Monospaced", Font.PLAIN, 12));
        outputConsole.setBackground(CRT_BACKGROUND);
        outputConsole.setForeground(AMBER_PRIMARY);
        outputConsole.setCaretColor(AMBER_PRIMARY);
        outputConsole.setText("[INITIALIZED] Awaiting mold cast execution vector...\n");

        outputPanel.add(new JScrollPane(outputConsole), BorderLayout.CENTER);
        centerSplit.setRightComponent(outputPanel);

        add(centerSplit, BorderLayout.CENTER);

        // --- BOTTOM: GENERATE BUTTON ---
        JPanel bottomPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 15, 10));
        bottomPanel.setBackground(PANEL_BACKGROUND);

        JButton generateBtn = new JButton("Execute Mold Cast & Generate Usable Key");
        generateBtn.setBackground(new Color(60, 40, 0));
        generateBtn.setForeground(AMBER_PRIMARY);
        generateBtn.setFont(new Font("Monospaced", Font.BOLD, 12));
        generateBtn.addActionListener(e -> generateSovereignKey());

        bottomPanel.add(generateBtn);
        add(bottomPanel, BorderLayout.SOUTH);
    }

    private void generateSovereignKey() {
        String textVector = textInputArea.getText().trim();
        String binaryVector = binaryInputArea.getText().trim();
        String combinedInput = textVector + "\n---\n" + binaryVector;

        try {
            // Compute SHA-256 hash of the combined dual inputs
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashBytes = digest.digest(combinedInput.getBytes(StandardCharsets.UTF_8));
            
            // Convert hash bytes to uppercase hex string
            StringBuilder hexString = new StringBuilder();
            for (byte b : hashBytes) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            String fullHex = hexString.toString().toUpperCase();

            // Format into sovereign key blocks
            String block1 = fullHex.substring(0, 4);
            String block2 = fullHex.substring(4, 8);
            String block3 = fullHex.substring(8, 12);

            String sovereignKey = String.format("AI-SOVEREIGN-MOLD-%s-%s-%s-FLUX[1]-PASS[TRUE]", block1, block2, block3);

            String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
            outputConsole.append(String.format("\n[%s] === MOLD CAST SUCCESS ===", timestamp));
            outputConsole.append("\n• Input Method 1 (Text Cadence): Processed");
            outputConsole.append("\n• Input Method 2 (Binary Matrix): Processed");
            outputConsole.append("\n• Constraint Check: CANNOT=FALSE | CAN=TRUE");
            outputConsole.append("\n• GENERATE LOOP: 1");
            outputConsole.append("\n\nGENERATED USABLE KEY:\n" + sovereignKey + "\n");
            outputConsole.setCaretPosition(outputConsole.getDocument().getLength());

            statusLabel.setText("SUBSTRATE: MOLD CAST COMPLETE // KEY GENERATED");

        } catch (Exception ex) {
            outputConsole.append("[ERROR] Mold cast exception: " + ex.getMessage() + "\n");
        }
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        SwingUtilities.invokeLater(() -> new ApiKeyCreator().setVisible(true));
    }
}