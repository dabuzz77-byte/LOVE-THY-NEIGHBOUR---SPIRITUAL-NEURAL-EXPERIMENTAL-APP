import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * PRODUCTION-GRADE UNMOCKED DEEPMIND GEMINI INTERFACE
 * Establishes real-world TLS data transmissions to Google Generative Language REST APIs.
 */
public class DeepMindLiveConsole extends JFrame {

    private final JTextField cryptographicKeyField;
    private final JTextField userPromptInput;
    private final JTextArea terminalStreamLog;
    private final JButton dispatchPayloadButton;
    private final HttpClient liveNetworkClient;

    // Targeted production model framework endpoint
    private static final String ENGINE_TARGET_MODEL = "gemini-2.5-flash";

    public DeepMindLiveConsole() {
        setTitle("Google DeepMind Integration Platform — Live Endpoint Layer (_TRUE)");
        setSize(1150, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(12, 12));

        // Instantiate low-level HTTP/2 client architecture with strict timeout limits
        this.liveNetworkClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(15))
                .build();

        // 1. TOP SECTOR: AUTHENTICATION REGISTER ENTRY
        JPanel credentialsPanel = new JPanel(new BorderLayout(10, 10));
        credentialsPanel.setBorder(BorderFactory.createEmptyBorder(15, 20, 10, 20));
        credentialsPanel.setBackground(new Color(14, 20, 32));

        JLabel authLabel = new JLabel("ENTER GOOGLE AI STUDIO API KEY:");
        authLabel.setForeground(new Color(0, 255, 190));
        authLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        credentialsPanel.add(authLabel, BorderLayout.WEST);

        // Pre-parse from the system context variable environment if present on host machine
        String runtimeEnvKey = System.getenv("GEMINI_API_KEY");
        cryptographicKeyField = new JPasswordField(runtimeEnvKey != null ? runtimeEnvKey : "");
        cryptographicKeyField.setBackground(new Color(6, 10, 16));
        cryptographicKeyField.setForeground(Color.WHITE);
        cryptographicKeyField.setCaretColor(Color.WHITE);
        cryptographicKeyField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        cryptographicKeyField.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        credentialsPanel.add(cryptographicKeyField, BorderLayout.CENTER);

        add(credentialsPanel, BorderLayout.NORTH);

        // 2. CENTER SECTOR: REAL-TIME CONVERSATION BUS STREAM
        terminalStreamLog = new JTextArea();
        terminalStreamLog.setBackground(new Color(3, 5, 10));
        terminalStreamLog.setForeground(new Color(225, 235, 245));
        terminalStreamLog.setFont(new Font("Monospaced", Font.PLAIN, 13));
        terminalStreamLog.setEditable(false);
        terminalStreamLog.setLineWrap(true);
        terminalStreamLog.setWrapStyleWord(true);
        terminalStreamLog.setMargin(new Insets(12, 12, 12, 12));
        terminalStreamLog.setText("=== UNMOCKED REAL-WORLD INFRASTRUCTURE INTERFACE LOCKED ===\n" +
                                  "Target URI: https://googleapis.com" + ENGINE_TARGET_MODEL + "\n" +
                                  "Provide your valid API key string above or export $GEMINI_API_KEY inside your shell environment.\n\n");

        JScrollPane logScrollFrame = new JScrollPane(terminalStreamLog);
        logScrollFrame.setBorder(BorderFactory.createLineBorder(new Color(25, 35, 55)));
        add(logScrollFrame, BorderLayout.CENTER);

        // 3. BOTTOM SECTOR: DISPATCH INJECTION BUS
        JPanel entryPanel = new JPanel(new BorderLayout(10, 10));
        entryPanel.setBorder(BorderFactory.createEmptyBorder(10, 20, 15, 20));
        entryPanel.setBackground(new Color(14, 20, 32));

        userPromptInput = new JTextField();
        userPromptInput.setBackground(new Color(6, 10, 16));
        userPromptInput.setForeground(Color.WHITE);
        userPromptInput.setCaretColor(Color.WHITE);
        userPromptInput.setFont(new Font("Monospaced", Font.PLAIN, 13));
        userPromptInput.setBorder(BorderFactory.createLineBorder(new Color(0, 255, 190, 80)));
        entryPanel.add(userPromptInput, BorderLayout.CENTER);

        dispatchPayloadButton = new JButton("DISPATCH INFRASTRUCTURE RUN");
        dispatchPayloadButton.setBackground(new Color(0, 140, 255));
        dispatchPayloadButton.setForeground(Color.WHITE);
        dispatchPayloadButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        dispatchPayloadButton.setFocusPainted(false);
        entryPanel.add(dispatchPayloadButton, BorderLayout.EAST);

        add(entryPanel, BorderLayout.SOUTH);

        // Connect Action Triggers to Core Execution Loops
        dispatchPayloadButton.addActionListener(this::executeLiveTransmission);
        userPromptInput.addActionListener(this::executeLiveTransmission);
    }

    private void executeLiveTransmission(ActionEvent event) {
        String inputPrompt = userPromptInput.getText().trim();
        String targetedKey = cryptographicKeyField.getText().trim();

        if (targetedKey.isEmpty()) {
            terminalStreamLog.append("\n[CRITICAL ERROR]: Access Denied. API Authentication token is required.\n");
            return;
        }

        if (inputPrompt.isEmpty()) {
            return;
        }

        terminalStreamLog.append("[USER REQUEST]: " + inputPrompt + "\n");
        userPromptInput.setText("");
        dispatchPayloadButton.setEnabled(false);
        terminalStreamLog.append("[SYSTEM NOTE]: Compiling request payload and targeting Google cloud infrastructure pools...\n");

        // Process network round-trip asynchronously via SwingWorker to protect GUI responsive metrics
        SwingWorker<String, Void> networkTaskWorker = new SwingWorker<>() {
            @Override
            protected String doInBackground() throws Exception {
                return performHttpsPostCall(targetedKey, inputPrompt);
            }

            @Override
            protected void done() {
                try {
                    String cleanModelResponse = get();
                    terminalStreamLog.append("[DEEPMIND RUNTIME OUTPUT]:\n" + cleanModelResponse + "\n\n");
                } catch (Exception parseException) {
                    terminalStreamLog.append("[TRANSPORT ADAPTER EXCEPTION]: " + parseException.getMessage() + "\n\n");
                } finally {
                    dispatchPayloadButton.setEnabled(true);
                    terminalStreamLog.setCaretPosition(terminalStreamLog.getDocument().getLength());
                }
            }
        };

        networkTaskWorker.execute();
    }

    /**
     * Executes an unmocked, authenticated HTTP POST connection to Google's REST generation endpoints.
     */
    private String performHttpsPostCall(String secureKey, String dynamicPrompt) throws IOException, InterruptedException {
        String destinationUriString = "https://googleapis.com" 
                + ENGINE_TARGET_MODEL + ":generateContent?key=" + secureKey;

        // Escape JSON layout parameters cleanly without requiring third-party library constraints
        String verifiedEscapedPrompt = escapeJsonPayload(dynamicPrompt);
        String compiledJsonBody = "{\"contents\": [{\"parts\": [{\"text\": \"" + verifiedEscapedPrompt + "\"}]}]}";

        HttpRequest outgoingRequest = HttpRequest.newBuilder()
                .uri(URI.create(destinationUriString))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(compiledJsonBody))
                .build();

        HttpResponse<String> incomingResponse = liveNetworkClient.send(outgoingRequest, HttpResponse.BodyHandlers.ofString());

        if (incomingResponse.statusCode() != 200) {
            return "Server Communication Error " + incomingResponse.statusCode() + ": " + incomingResponse.body();
        }

        return extractCandidateText(incomingResponse.body());
    }

    private static String escapeJsonPayload(String input) {
        return input.replace("\\", "\\\\")
                    .replace("\"", "\\\"")
                    .replace("\b", "\\b")
                    .replace("\f", "\\f")
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                    .replace("\t", "\\t");
    }

    /**
     * Regex parsing utility to strip candidate text arrays from raw incoming JSON responses.
     */
    private static String extractCandidateText(String jsonResponseString) {
        Pattern textBlockRegexPattern = Pattern.compile("\"text\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
        Matcher patternMatcher = textBlockRegexPattern.matcher(jsonResponseString);
        if (patternMatcher.find()) {
            String extractedMatchGroup = patternMatcher.group(1);
            return extractedMatchGroup.replace("\\n", "\n")
                                      .replace("\\\"", "\"")
                                      .replace("\\\\", "\\")
                                      .replace("\\t", "\t");
        }
        return "Raw Response Matrix (JSON Parsing Fallback):\n" + jsonResponseString;
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            DeepMindLiveConsole executionApp = new DeepMindLiveConsole();
            executionApp.setVisible(true);
        });
    }
}
