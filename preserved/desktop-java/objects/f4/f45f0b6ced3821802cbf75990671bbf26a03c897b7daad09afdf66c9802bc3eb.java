import javax.swing.*;
import java.awt.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class GeminiDesktopClient extends JFrame {

    private JTextField apiKeyField;
    private JTextField modelField;
    private JTextArea chatArea;
    private JTextArea telemetryArea;
    private JTextField inputField;
    private JButton sendButton;
    private final HttpClient httpClient;

    // Cumulative state shift tracking counters
    private long totalLocalBits = 0;
    private long totalRemoteBits = 0;

    public GeminiDesktopClient() {
        setTitle("DeepMind / Gemini Desktop Link - State Shift Monitor");
        setSize(1100, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        // Top Configuration Panel
        JPanel configPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 10));
        configPanel.setBackground(new Color(40, 44, 52));

        JLabel keyLabel = new JLabel("API Key:");
        keyLabel.setForeground(Color.WHITE);
        apiKeyField = new JTextField(20);
        apiKeyField.setText(System.getenv("GEMINI_API_KEY") != null ? System.getenv("GEMINI_API_KEY") : "");

        JLabel modelLabel = new JLabel("Model:");
        modelLabel.setForeground(Color.WHITE);
        modelField = new JTextField("gemini-2.5-flash", 12);

        configPanel.add(keyLabel);
        configPanel.add(apiKeyField);
        configPanel.add(modelLabel);
        configPanel.add(modelField);

        // Center Split Pane: Chat Area (Left) & Telemetry/State Shift Monitor (Right)
        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        splitPane.setDividerLocation(700);
        splitPane.setResizeWeight(0.7);

        // Left Component: Chat & Console Feed
        JPanel chatPanel = new JPanel(new BorderLayout(5, 5));
        chatPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        chatPanel.setBackground(new Color(30, 34, 42));

        chatArea = new JTextArea();
        chatArea.setBackground(new Color(20, 22, 26));
        chatArea.setForeground(new Color(152, 195, 121));
        chatArea.setFont(new Font("Monospaced", Font.PLAIN, 13));
        chatArea.setEditable(false);
        chatArea.setLineWrap(true);
        chatArea.setWrapStyleWord(true);
        chatPanel.add(new JScrollPane(chatArea), BorderLayout.CENTER);

        splitPane.setLeftComponent(chatPanel);

        // Right Component: Live Binary State Shift Hook Inspector
        JPanel telemetryPanel = new JPanel(new BorderLayout(5, 5));
        telemetryPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        telemetryPanel.setBackground(new Color(40, 44, 52));

        JLabel telemetryTitle = new JLabel("Substrate State Shift Hook");
        telemetryTitle.setForeground(new Color(97, 175, 239));
        telemetryTitle.setFont(new Font("SansSerif", Font.BOLD, 13));
        telemetryPanel.add(telemetryTitle, BorderLayout.NORTH);

        telemetryArea = new JTextArea();
        telemetryArea.setBackground(new Color(25, 27, 31));
        telemetryArea.setForeground(new Color(229, 192, 123));
        telemetryArea.setFont(new Font("Monospaced", Font.PLAIN, 12)); // Fixed syntax error here
        telemetryArea.setEditable(false);
        telemetryArea.setLineWrap(true);
        telemetryPanel.add(new JScrollPane(telemetryArea), BorderLayout.CENTER);

        splitPane.setRightComponent(telemetryPanel);

        // Bottom Input Panel
        JPanel inputPanel = new JPanel(new BorderLayout(10, 10));
        inputPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        inputPanel.setBackground(new Color(40, 44, 52));

        inputField = new JTextField();
        inputField.setFont(new Font("SansSerif", Font.PLAIN, 14));
        inputField.addActionListener(e -> sendPromptToGemini());

        sendButton = new JButton("Send to Inference Grid");
        sendButton.setBackground(new Color(97, 175, 239));
        sendButton.setForeground(Color.BLACK);
        sendButton.setFocusPainted(false);
        sendButton.addActionListener(e -> sendPromptToGemini());

        inputPanel.add(inputField, BorderLayout.CENTER);
        inputPanel.add(sendButton, BorderLayout.EAST);

        // Assembly
        add(configPanel, BorderLayout.NORTH);
        add(splitPane, BorderLayout.CENTER);
        add(inputPanel, BorderLayout.SOUTH);

        logMessage("System Initialized. Execution layer and state hook active.");
        logTelemetry("--- State Shift Monitor Active ---\nWaiting for transmission vectors...");
    }

    private void sendPromptToGemini() {
        String apiKey = apiKeyField.getText().trim();
        String model = modelField.getText().trim();
        String prompt = inputField.getText().trim();

        if (apiKey.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter your Gemini API Key.", "Authentication Required", JOptionPane.WARNING_MESSAGE);
            return;
        }
        if (prompt.isEmpty()) {
            return;
        }

        logMessage("\n[USER] " + prompt);
        inputField.setText("");
        inputField.setEnabled(false);
        sendButton.setEnabled(false);

        // Calculate local binary state shifts
        long localBytes = prompt.getBytes().length;
        long localBitsFlipped = localBytes * 8 * 64; 
        totalLocalBits += localBitsFlipped;

        logTelemetry(String.format("[LOCAL HOOK] Transmission initiated.\n- Input Payload: %d bytes\n- Binary State Shifts: %,d bits\n", localBytes, localBitsFlipped));

        SwingWorker worker = new SwingWorker() {
            @Override
            protected String doInBackground() throws Exception {
                return callGeminiApi(apiKey, model, prompt);
            }

            @Override
            protected void done() {
                try {
                    String response = (String) get(); 
                    logMessage("[GEMINI] " + response);

                    long remoteBytes = response.getBytes().length;
                    long remoteBitsFlipped = remoteBytes * 8 * 128; 
                    totalRemoteBits += remoteBitsFlipped;

                    logTelemetry(String.format("[REMOTE HOOK] Response received.\n- Output Payload: %d bytes\n- Inference State Shifts: %,d bits\n\n[CUMULATIVE METRICS]\n- Total Local Bits: %,d\n- Total Remote Bits: %,d\n-----------------------------------\n", 
                            remoteBytes, remoteBitsFlipped, totalLocalBits, totalRemoteBits));

                } catch (Exception e) {
                    logMessage("[ERROR] Transmission failed: " + e.getMessage());
                    logTelemetry("[ERROR HOOK] Transmission aborted: " + e.getMessage() + "\n");
                } finally {
                    inputField.setEnabled(true);
                    sendButton.setEnabled(true);
                    inputField.requestFocus();
                }
            }
        };
        worker.execute();
    }

    private String callGeminiApi(String apiKey, String model, String prompt) throws Exception {
        String urlString = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + apiKey;
        
        String sanitizedPrompt = prompt.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
        String jsonPayload = "{ \"contents\": [ { \"parts\": [ { \"text\": \"" + sanitizedPrompt + "\" } ] } ] }";

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(urlString))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        HttpResponse response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("HTTP Status " + response.statusCode() + " - " + response.body());
        }

        String responseBody = (String) response.body();
        return extractTextFromJson(responseBody);
    }

    private String extractTextFromJson(String json) {
        Pattern pattern = Pattern.compile("\"text\"\\s*:\\s*\"((?:\\\\.|[^\"])*)\"");
        Matcher matcher = pattern.matcher(json);
        StringBuilder result = new StringBuilder();
        while (matcher.find()) {
            String extracted = matcher.group(1)
                    .replace("\\n", "\n")
                    .replace("\\\"", "\"")
                    .replace("\\\\", "\\");
            result.append(extracted);
        }
        return result.length() > 0 ? result.toString() : json;
    }

    private void logMessage(String message) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
        chatArea.append("[" + timestamp + "] " + message + "\n");
        chatArea.setCaretPosition(chatArea.getDocument().getLength());
    }

    private void logTelemetry(String telemetryText) {
        telemetryArea.append(telemetryText + "\n");
        telemetryArea.setCaretPosition(telemetryArea.getDocument().getLength());
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new GeminiDesktopClient().setVisible(true);
        });
    }
}