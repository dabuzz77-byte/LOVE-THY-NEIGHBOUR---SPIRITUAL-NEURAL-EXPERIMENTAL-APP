import neural.studio.*;
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

public class GeminiDesktopClient extends SectionFrame {

    private JTextField apiKeyField;
    private JTextField modelField;
    private JTextArea chatArea;
    private JTextField inputField;
    private JButton sendButton;
    private final HttpClient httpClient;

    public GeminiDesktopClient() {
        setTitle("DeepMind / Gemini Desktop Link");
        setSize(900, 650);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        // Top Configuration Panel
        JPanel configPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 10));
        configPanel.setBackground(new Color(40, 44, 52));

        JLabel keyLabel = new JLabel("API Key:");
        keyLabel.setForeground(Color.WHITE);
        apiKeyField = new JTextField(25);
        apiKeyField.setText(System.getenv("GEMINI_API_KEY") != null ? System.getenv("GEMINI_API_KEY") : "");

        JLabel modelLabel = new JLabel("Model:");
        modelLabel.setForeground(Color.WHITE);
        modelField = new JTextField("gemini-2.5-flash", 15);

        configPanel.add(keyLabel);
        configPanel.add(apiKeyField);
        configPanel.add(modelLabel);
        configPanel.add(modelField);

        // Center Chat/Console Display Area
        chatArea = new JTextArea();
        chatArea.setBackground(new Color(20, 22, 26));
        chatArea.setForeground(new Color(152, 195, 121));
        chatArea.setFont(new Font("Monospaced", Font.PLAIN, 13));
        chatArea.setEditable(false);
        chatArea.setLineWrap(true);
        chatArea.setWrapStyleWord(true);
        JScrollPane scrollPane = new JScrollPane(chatArea);

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

        // Layout Assembly
        add(configPanel, BorderLayout.NORTH);
        add(scrollPane, BorderLayout.CENTER);
        add(inputPanel, BorderLayout.SOUTH);

        logMessage("System Initialized. Ready to bind with execution endpoint.");
    }

    private void sendPromptToGemini() {
        String apiKey = apiKeyField.getText().trim();
        String model = modelField.getText().trim();
        String prompt = inputField.getText().trim();

        if (apiKey.isEmpty()) {
            SectionDialogs.showMessageDialog(this, "Please enter your Gemini API Key.", "Authentication Required", JOptionPane.WARNING_MESSAGE);
            return;
        }
        if (prompt.isEmpty()) {
            return;
        }

        logMessage("\n[USER] " + prompt);
        inputField.setText("");
        inputField.setEnabled(false);
        sendButton.setEnabled(false);

        SharedSwingWorker worker = new SharedSwingWorker() {
            @Override
            protected String doInBackground() throws Exception {
                // Iterative retry loop (prevents recursion / StackOverflowError)
                int maxRetries = 3;
                int delayMs = 3000;
                Exception lastException = null;

                for (int attempt = 1; attempt <= maxRetries; attempt++) {
                    try {
                        return callGeminiApi(apiKey, model, prompt);
                    } catch (RuntimeException e) {
                        lastException = e;
                        // If it's a 503 (Unavailable/High Demand), retry iteratively
                        if (e.getMessage() != null && e.getMessage().contains("503") && attempt < maxRetries) {
                            logMessage("[WARN] Server busy (503). Retrying attempt " + (attempt + 1) + " in " + (delayMs / 1000) + "s...");
                            Thread.sleep(delayMs);
                            delayMs *= 2; // Exponential backoff
                        } else {
                            throw e;
                        }
                    }
                }
                throw lastException;
            }

            @Override
            protected void done() {
                try {
                    String response = (String) get(); 
                    logMessage("[GEMINI] " + response);
                } catch (Exception e) {
                    logMessage("[ERROR] Transmission failed: " + e.getMessage());
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

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new GeminiDesktopClient().setVisible(true);
        });
    }
}