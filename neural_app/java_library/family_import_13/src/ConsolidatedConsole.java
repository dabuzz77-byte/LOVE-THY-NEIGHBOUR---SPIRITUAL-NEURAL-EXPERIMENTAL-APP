import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;

/**
 * Consolidated Application Console
 * Features: State System Toggle & Text Translation Viewer
 */
public class ConsolidatedConsole extends SectionFrame {

    private boolean stateActive = false;
    private JLabel stateValueLabel;
    private JButton toggleButton;
    private JTextArea displayArea;

    // Sample data based on previous text analysis
    private final String contemporaryText = 
        "Our Father in heaven,\nhallowed be your name,\nyour kingdom come,\n" +
        "your will be done,\non earth as in heaven.\nGive us today our daily bread.\n" +
        "Forgive us our sins\nas we forgive those who sin against us.\n" +
        "Lead us not into temptation\nbut deliver us from evil.\n" +
        "For the kingdom, the power,\nand the glory are yours\nnow and for ever.\nAmen.";

    private final String traditionalText = 
        "Our Father, which art in heaven,\nHallowed be thy name.\nThy kingdom come.\n" +
        "Thy will be done in earth, as it is in heaven.\nGive us this day our daily bread.\n" +
        "And forgive us our debts, as we forgive our debtors.\n" +
        "And lead us not into temptation, but deliver us from evil:\n" +
        "For thine is the kingdom, and the power, and the glory, for ever.\nAmen.";

    public ConsolidatedConsole() {
        // 1. Initialize Window Framework
        setTitle("System Dashboard & Text Analyzer");
        setSize(700, 500);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        // 2. Build Top Panel (State Control System)
        JPanel topPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        topPanel.setBorder(BorderFactory.createTitledBorder("State Control Engine"));

        JLabel labelLabel = new JLabel("Active State Status: ");
        stateValueLabel = new JLabel("FALSE");
        stateValueLabel.setForeground(Color.RED);
        stateValueLabel.setFont(new Font("Monospaced", Font.BOLD, 14));

        toggleButton = new JButton("Toggle State (0 / 1)");
        toggleButton.addActionListener(this::handleStateToggle);

        topPanel.add(labelLabel);
        topPanel.add(stateValueLabel);
        topPanel.add(toggleButton);

        // 3. Build Center Panel (Text Analysis Layer)
        JPanel centerPanel = new JPanel(new BorderLayout(5, 5));
        centerPanel.setBorder(BorderFactory.createTitledBorder("Text Translation Module"));

        JPanel buttonGrid = new JPanel(new GridLayout(1, 2, 5, 5));
        JButton btnContemporary = new JButton("Load Contemporary Version");
        JButton btnTraditional = new JButton("Load Traditional Version");

        btnContemporary.addActionListener(e -> displayArea.setText(contemporaryText));
        btnTraditional.addActionListener(e -> displayArea.setText(traditionalText));

        buttonGrid.add(btnContemporary);
        buttonGrid.add(btnTraditional);

        displayArea = new JTextArea(contemporaryText);
        displayArea.setFont(new Font("SansSerif", Font.PLAIN, 13));
        displayArea.setEditable(false);
        displayArea.setMargin(new Insets(10, 10, 10, 10));
        JScrollPane scrollPane = new JScrollPane(displayArea);

        centerPanel.add(buttonGrid, BorderLayout.NORTH);
        centerPanel.add(scrollPane, BorderLayout.CENTER);

        // 4. Assemble Components
        add(topPanel, BorderLayout.NORTH);
        add(centerPanel, BorderLayout.CENTER);
    }

    /**
     * Logic for switching UI flags dynamically
     */
    private void handleStateToggle(ActionEvent e) {
        stateActive = !stateActive;
        if (stateActive) {
            stateValueLabel.setText("TRUE (STATE 1)");
            stateValueLabel.setForeground(new Color(0, 128, 0)); // Green
        } else {
            stateValueLabel.setText("FALSE (STATE 0)");
            stateValueLabel.setForeground(Color.RED);
        }
    }

    /**
     * Application Entry Point
     */
    public static void main(String[] args) {
        // Ensure UI updates are safe on the Event Dispatch Thread
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new ConsolidatedConsole().setVisible(true);
        });
    }
}