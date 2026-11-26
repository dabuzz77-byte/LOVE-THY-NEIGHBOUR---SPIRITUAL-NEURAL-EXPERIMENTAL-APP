import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * BI-TER-ALLSTATE GRAND SYSTEM: PEER FILE ENGINE
 * Part 2: Manages the HTTP loopback transport layer directly to host computing nodes.
 */
public class LocalHttpRouter {
    private final HttpClient localHttpClient;
    private static final String SYSTEM_TARGET_MODEL = "llama3";
    private static final String LOCAL_OLLAMA_ENDPOINT = "http://localhost:11434/api/generate";

    public LocalHttpRouter() {
        // Instantiate high-performance localized HTTP/2 client wrapper
        this.localHttpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    /**
     * Dispatches an unmocked local HTTP POST connection to your native Ollama endpoint.
     */
    public String performLocalPostCall(String dynamicPrompt) throws IOException, InterruptedException {
        String verifiedEscapedPrompt = escapeJsonPayload(dynamicPrompt);
        
        // Assemble request body with stream=false to receive the complete response payload string
        String compiledJsonBody = String.format(
                "{\"model\": \"%s\", \"prompt\": \"%s\", \"stream\": false}",
                SYSTEM_TARGET_MODEL, verifiedEscapedPrompt
        );

        HttpRequest outgoingRequest = HttpRequest.newBuilder()
                .uri(URI.create(LOCAL_OLLAMA_ENDPOINT))
                .timeout(Duration.ofSeconds(60)) // High timeout limit to protect raw local processor parsing
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(compiledJsonBody))
                .build();

        HttpResponse<String> incomingResponse = localHttpClient.send(outgoingRequest, HttpResponse.BodyHandlers.ofString());

        if (incomingResponse.statusCode() != 200) {
            return "Local Communication Error " + incomingResponse.statusCode() + ": " + incomingResponse.body();
        }

        return extractResponseField(incomingResponse.body());
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
     * Regex utility to strip out the compiled response parameter from the raw incoming JSON block.
     */
    private static String extractResponseField(String jsonResponseString) {
        Pattern responseRegexPattern = Pattern.compile("\"response\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
        Matcher patternMatcher = responseRegexPattern.matcher(jsonResponseString);
        if (patternMatcher.find()) {
            String extractedMatchGroup = patternMatcher.group(1);
            return extractedMatchGroup.replace("\\n", "\n")
                                      .replace("\\\"", "\"")
                                      .replace("\\\\", "\\")
                                      .replace("\\t", "\t");
        }
        return "Raw Response Matrix (JSON Parsing Fallback):\n" + jsonResponseString;
    }
}
