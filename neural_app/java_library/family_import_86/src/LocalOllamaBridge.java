import neural.studio.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * MODULE 3: LOCAL HARDWARE COGNITIVE TRANSCEIVER
 * Negotiates unblocked HTTP POST connections targeting native local Ollama pipelines.
 */
public class LocalOllamaBridge {

    private final HttpClient loopbackClient;
    private static final String HARDWARE_TARGET_ENDPOINT = "http://localhost:11434/api/generate";

    public LocalOllamaBridge(HttpClient baseClient) {
        this.loopbackClient = baseClient;
    }

    public String executeLocalInference(String targetModel, String unescapedPrompt) throws Exception {
        String escapedTextPayload = unescapedPrompt.replace("\\", "\\\\").replace("\"", "\\\"");
        String payloadJsonBody = String.format(
                "{\"model\": \"%s\", \"prompt\": \"%s\", \"stream\": false}",
                targetModel, escapedTextPayload
        );

        HttpRequest outboundRequest = HttpRequest.newBuilder()
                .uri(URI.create(HARDWARE_TARGET_ENDPOINT))
                .timeout(Duration.ofSeconds(45))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payloadJsonBody))
                .build();

        HttpResponse<String> inboundResponse = loopbackClient.send(outboundRequest, HttpResponse.BodyHandlers.ofString());

        if (inboundResponse.statusCode() != 200) {
            return "Local Bus Exception Code " + inboundResponse.statusCode() + " | Run 'ollama run " + targetModel + "' in PowerShell.";
        }

        return extractOllamaJsonValue(inboundResponse.body());
    }

    private String extractOllamaJsonValue(String jsonString) {
        Pattern regexPattern = Pattern.compile("\"response\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
        Matcher patternMatcher = regexPattern.matcher(jsonString);
        if (patternMatcher.find()) {
            return patternMatcher.group(1).replace("\\n", "\n").replace("\\\"", "\"").replace("\\\\", "\\");
        }
        return jsonString;
    }
}
