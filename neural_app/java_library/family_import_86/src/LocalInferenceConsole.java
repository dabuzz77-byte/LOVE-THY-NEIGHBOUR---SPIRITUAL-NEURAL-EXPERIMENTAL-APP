import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;

/**
 * BI-TER-ALLSTATE GRAND SYSTEM: PEER FILE ENGINE
 * Part 3: Central application entry point and real-time graphics panel frame.
 */
public class LocalInferenceConsole extends SectionFrame {

    private final JTextField promptInputField;
    private final JTextArea conversationStreamLog;
    private final JButton dispatchButton;
    private final LocalHttpRouter httpRouter;

    public LocalInferenceConsole() {
        setTitle("Sovereign Local Inference Platform — Unblocked Hardware Interface (_TRUE)");
        setSize(1200, 850);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(12, 12));

        this.httpRouter = new LocalHttpRouter();

        // 1. TOP BAR: HARDWARE INFRASTRUCTURE STATUS PANEL
        JPanel statusPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 10));
        statusPanel.setBorder(BorderFactory.createMatteBorder(0, 0, 1, 0, new Color(0, 255, 180, 80)));
        statusPanel.setBackground(new Color(10, 15, 26));

        JLabel loopbackLabel = new JLabel("LOCAL BUS STATUS: CONNECTED TO 127.0.0.1:11434");
        loopbackLabel.setForeground(new Color(0, 255, 180));
        loopbackLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        statusPanel.add(loopbackLabel);

        add(statusPanel, BorderLayout.NORTH);

        // 2. CENTER PANEL: LIVE CONVERSATION LOG
        conversationStreamLog = new JTextArea();
        conversationStreamLog.setBackground(new Color(3, 5, 9));
        conversationStreamLog.setForeground(new Color(220, 232, 245));
        conversationStreamLog.setFont(new Font("Monospaced", Font.PLAIN, 13));
        conversationStreamLog.setEditable(false);
        conversationStreamLog.setLineWrap(true);
        conversationStreamLog.setWrapStyleWord(true);
        conversationStreamLog.setMargin(new Insets(12, 12, 12, 12));
        conversationStreamLog.setText("=== SOVEREIGN OFFLINE CORE INITIALIZED ===\n" +
                                      "Target Model: llama3 via Ollama background node\n" +
                                      "All data stays on this device. 0% network data transmission. 0% corporate surveillance.\n\n");

        JScrollPane logScrollArea = new JScrollPane(conversationStreamLog);
        logScrollArea.setBorder(BorderFactory.createLineBorder(new Color(20, 32, 50)));
        add(logScrollArea, BorderLayout.CENTER);

        // 3. BOTTOM PANEL: PROMPT DISPATCH BUS
        JPanel entryPanel = new JPanel(new BorderLayout(10, 10));
        entryPanel.setBorder(BorderFactory.createEmptyBorder(10, 20, 15, 20));
        entryPanel.setBackground(new Color(10, 15, 26));

        promptInputField = new JTextField();
        promptInputField.setBackground(new Color(5, 8, 14));
        promptInputField.setForeground(Color.WHITE);
        promptInputField.setCaretColor(Color.WHITE);
        promptInputField.setFont(new Font("Monospaced", Font.PLAIN, 13));
        promptInputField.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 180, 80)));
        entryPanel.add(promptInputField, BorderLayout.CENTER);

        dispatchButton = new JButton("DISPATCH INFRASTRUCTURE RUN");
        dispatchButton.setBackground(new Color(0, 130, 230));
        dispatchButton.setForeground(Color.WHITE);
        dispatchButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        dispatchButton.setFocusPainted(false);
        entryPanel.add(dispatchButton, BorderLayout.EAST);

        add(entryPanel, BorderLayout.SOUTH);

        // Connect Action Triggers to Core Execution Loops
        dispatchButton.addActionListener(this::executeLocalTransmission);
        promptInputField.addActionListener(this::executeLocalTransmission);
    }

    private void executeLocalTransmission(ActionEvent event) {
        String inputPrompt = promptInputField.getText().trim();

        if (inputPrompt.isEmpty()) {
            return;
        }

        conversationStreamLog.append("[USER REQUEST]: " + inputPrompt + "\n");
        promptInputField.setText("");
        dispatchButton.setEnabled(false);
        conversationStreamLog.append("[LOCAL HARDWARE]: Allocating processor threads and computing tokens...\n");

        // Run network execution asynchronously via SharedSwingWorker to prevent UI freezing
        SharedSwingWorker<String, Void> taskWorker = new SharedSwingWorker<>() {
            @Override
            protected String doInBackground() throws Exception {
                return httpRouter.performLocalPostCall(inputPrompt);
            }

            @Override
            protected void done() {
                try {
                    String rawModelOutput = get();
                    conversationStreamLog.append("[LOCAL CORE RESPONSE]:\n" + rawModelOutput + "\n\n");
                } catch (Exception parseException) {
                    conversationStreamLog.append("[LOCAL BUS EXCEPTION]: " + parseException.getMessage() + "\n" +
                                                 " Ensure the Ollama background service is running via 'ollama run llama3'\n\n");
                } finally {
                    dispatchButton.setEnabled(true);
                    conversationStreamLog.setCaretPosition(conversationStreamLog.getDocument().getLength());
                }
            }
        };

        taskWorker.execute();
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            LocalInferenceConsole app = new LocalInferenceConsole();
            app.setVisible(true);
        });
    }
}
