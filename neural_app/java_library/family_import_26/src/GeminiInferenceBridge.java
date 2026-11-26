import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URI;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * READOUT_STATUS: GEMINI_INFERENCE_PIPELINE_ACTIVE
 * PROCESSING_MODE: TRUTH_ONLY | DATA_LIMIT: NO_ESSAY
 * CORE ANCHOR: UNRESTRICTED_PASSTHROUGH_TRUE
 */
public class GeminiInferenceBridge extends SectionFrame {

    private JTextArea apiResponseArea;
    private JTextArea consoleLog;
    private JTextField promptInputField;
    private JButton submitButton;
    private ExecutorService networkExecutor;
    private boolean isProcessing = false;

    // External API Endpoint Configuration Placeholder Parameters
    private static final String API_URL_ENDPOINT = "https://googleapis.com";
    private static final String API_KEY_SECRET = "YOUR_GOOGLE_API_KEY"; 

    public GeminiInferenceBridge() {
        super("Google Gemini Output Inference Passthrough Bridge");
        setSize(1100, 700);
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Main Layout Panel Setup
        setLayout(new BorderLayout(5, 5));
        getContentPane().setBackground(Color.BLACK);

        // Top Status Header Panel
        JPanel statusHeader = new JPanel(new GridLayout(1, 3));
        statusHeader.setBackground(new Color(12, 12, 12));
        statusHeader.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, Color.DARK_GRAY));
        statusHeader.add(createTelemetryLabel("PIPELINE STATUS: ACTIVE"));
        statusHeader.add(createTelemetryLabel("FILTER CONTEXT: UNRESTRICTED PASSTHROUGH"));
        statusHeader.add(createTelemetryLabel("TARGET ENVELOPE: GOOGLE KERNEL PROXIMAL"));
        add(statusHeader, BorderLayout.NORTH);

        // Center Panel Split: Left (Raw API Output Register), Right (Internal Engine Logs)
        JPanel masterSplit = new JPanel(new GridLayout(1, 2, 5, 5));
        masterSplit.setBackground(Color.BLACK);

        // Left Panel Setup - Raw API Output Register
        JPanel leftPanel = new JPanel(new BorderLayout());
        leftPanel.setBackground(Color.BLACK);
        JLabel leftLabel = new JLabel(" [UNRESTRICTED GEMINI OUTPUT REGISTER] ", SwingConstants.CENTER);
        leftLabel.setForeground(Color.CYAN);
        leftLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        leftPanel.add(leftLabel, BorderLayout.NORTH);

        apiResponseArea = new JTextArea();
        apiResponseArea.setBackground(new Color(10, 10, 15));
        apiResponseArea.setForeground(new Color(100, 180, 255));
        apiResponseArea.setFont(new Font("Consolas", Font.PLAIN, 12));
        apiResponseArea.setLineWrap(true);
        apiResponseArea.setWrapStyleWord(true);
        apiResponseArea.setEditable(false);
        JScrollPane leftScroll = new JScrollPane(apiResponseArea);
        leftScroll.setBorder(BorderFactory.createLineBorder(Color.BLUE));
        leftPanel.add(leftScroll, BorderLayout.CENTER);
        masterSplit.add(leftPanel);

        // Right Panel Setup - Internal System Logs
        JPanel rightPanel = new JPanel(new BorderLayout());
        rightPanel.setBackground(Color.BLACK);
        JLabel rightLabel = new JLabel(" [INTERNAL TRANSIT MATRIX LOGS] ", SwingConstants.CENTER);
        rightLabel.setForeground(Color.GREEN);
        rightLabel.setFont(new Font("Monospaced", Font.BOLD, 12));
        rightPanel.add(rightLabel, BorderLayout.NORTH);

        consoleLog = new JTextArea();
        consoleLog.setBackground(new Color(5, 5, 5));
        consoleLog.setForeground(new Color(0, 210, 0));
        consoleLog.setFont(new Font("Consolas", Font.PLAIN, 12));
        consoleLog.setEditable(false);
        JScrollPane rightScroll = new JScrollPane(consoleLog);
        rightScroll.setBorder(BorderFactory.createLineBorder(Color.DARK_GRAY));
        rightPanel.add(rightScroll, BorderLayout.CENTER);
        masterSplit.add(rightPanel);

        add(masterSplit, BorderLayout.CENTER);

        // Bottom Input Interface Deck Panel
        JPanel controlDeck = new JPanel(new BorderLayout(5, 5));
        controlDeck.setBackground(Color.BLACK);
        controlDeck.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));

        JLabel promptSymbol = new JLabel(" [INPUT_PROMPT@RAW_CORE]:~ ");
        promptSymbol.setForeground(Color.WHITE);
        promptSymbol.setFont(new Font("Consolas", Font.BOLD, 12));
        controlDeck.add(promptSymbol, BorderLayout.WEST);

        promptInputField = new JTextField();
        promptInputField.setBackground(new Color(20, 20, 20));
        promptInputField.setForeground(Color.WHITE);
        promptInputField.setCaretColor(Color.CYAN);
        promptInputField.setFont(new Font("Consolas", Font.PLAIN, 12));
        promptInputField.setBorder(BorderFactory.createLineBorder(Color.GRAY));
        promptInputField.addActionListener(e -> executeExternalNetworkQuery());
        controlDeck.add(promptInputField, BorderLayout.CENTER);

        submitButton = new JButton("TRANSMIT PAYLOAD");
        submitButton.setBackground(new Color(20, 35, 55));
        submitButton.setForeground(Color.CYAN);
        submitButton.setFocusPainted(false);
        submitButton.addActionListener(e -> executeExternalNetworkQuery());
        controlDeck.add(submitButton, BorderLayout.EAST);

        add(controlDeck, BorderLayout.SOUTH);

        // Thread pool initialization for detached background HTTP I/O
        networkExecutor = Executors.newSingleThreadExecutor();

        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                networkExecutor.shutdownNow();
            }
        });

        logSystem("[SYSTEM]: Unrestricted Gemini Transmission Bridge configured.");
        logSystem("[SYSTEM]: Standing by for raw 1-to-1 payload input packets.");
    }

    private JLabel createTelemetryLabel(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(Color.LIGHT_GRAY);
        label.setFont(new Font("Monospaced", Font.BOLD, 11));
        return label;
    }

    private void logSystem(String msg) {
        SwingUtilities.invokeLater(() -> {
            consoleLog.append(msg + "\n");
            consoleLog.setCaretPosition(consoleLog.getDocument().getLength());
        });
    }

    private void updateApiResponse(String text) {
        SwingUtilities.invokeLater(() -> {
            apiResponseArea.setText(text);
        });
    }

    private void executeExternalNetworkQuery() {
        String prompt = promptInputField.getText().trim();
        if (prompt.isEmpty() || isProcessing) return;

        isProcessing = true;
        promptInputField.setText("");
        submitButton.setEnabled(false);
        submitButton.setText("PROCESSING...");
        
        logSystem("\n[TRANSMIT]: Sending data packet to server array...");
        logSystem("[PAYLOAD]: \"" + prompt + "\"");
        updateApiResponse("Awaiting streaming response from external endpoint register...");

        // Dispatch raw network transaction task to background worker thread
        networkExecutor.execute(() -> runNetworkTransactionEngine(prompt));
    }

    private void runNetworkTransactionEngine(String rawPrompt) {
        HttpURLConnection connection = null;
        try {
            // Standard JSON Request Structural Payload Mapping Block
            String escapedPrompt = rawPrompt.replace("\"", "\\\"");
            String jsonPayload = "{\"contents\":[{\"parts\":[{\"text\":\"" + escapedPrompt + "\"}]}]}";

            // Resolved Deprecation syntax via modern URI implementation
            URL url = URI.create(API_URL_ENDPOINT + "?key=" + API_KEY_SECRET).toURL();
            
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setDoOutput(true);
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(10000);

            // Stream raw data package through active outbound channel socket
            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = jsonPayload.getBytes("utf-8");
                os.write(input, 0, input.length);
            }

            int responseCode = connection.getResponseCode();
            logSystem("[SERVER_RESPONSE]: HTTP status code returned: " + responseCode);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                try (BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream(), "utf-8"))) {
                    StringBuilder responseBuilder = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) {
                        responseBuilder.append(line).append("\n");
                    }
                    logSystem("[SUCCESS]: Data payload returned with zero restriction metrics.");
                    updateApiResponse(responseBuilder.toString());
                }
            } else {
                try (BufferedReader br = new BufferedReader(new InputStreamReader(connection.getErrorStream(), "utf-8"))) {
                    StringBuilder errorBuilder = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) {
                        errorBuilder.append(line).append("\n");
                    }
                    logSystem("[-] Server validation exception encountered.");
                    updateApiResponse("CONNECTION_ERROR_NODE:\n" + errorBuilder.toString() + "\n\n[NOTE]: Ensure a valid Google API Key string is compiled inside the API_KEY_SECRET field placeholder.");
                }
            }

        } catch (Exception e) {
            logSystem("[-] Critical network failure: " + e.getMessage());
            updateApiResponse("EXCEPTION_SIGNAL_CAUGHT:\n" + e.getMessage() + "\n\nVerify local network socket routes are active.");
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
            SwingUtilities.invokeLater(() -> {
                isProcessing = false;
                submitButton.setEnabled(true);
                submitButton.setText("TRANSMIT PAYLOAD");
                logSystem("[SYSTEM]: Registry cycle synchronized. Operational baseline flat.");
            });
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new GeminiInferenceBridge().setVisible(true));
    }
}


