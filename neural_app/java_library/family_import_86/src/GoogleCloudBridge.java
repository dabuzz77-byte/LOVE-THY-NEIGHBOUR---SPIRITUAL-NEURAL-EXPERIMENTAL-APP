import neural.studio.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * MODULE 4: EXTERNAL ENDPOINT TLS TRANSCEIVER
 * Issues authenticated cryptographic JSON requests to Google Generative Language endpoints.
 */
public class GoogleCloudBridge {

    private final HttpClient cloudNetworkClient;
    private static final String COMPUTE_MODEL_TARGET = "gemini-2.5-flash";

    public GoogleCloudBridge(HttpClient baseClient) {
        this.cloudNetworkClient = baseClient;
    }

    public String executeCloudContentGeneration(String apiKey, String unescapedPrompt) throws Exception {
        String endpointTargetUrl = "https://googleapis.com" 
                + COMPUTE_MODEL_TARGET + ":generateContent?key=" + apiKey;

        String escapedTextPayload = unescapedPrompt.replace("\\", "\\\\")
                                                   .replace("\"", "\\\"")
                                                   .replace("\n", "\\n");
        
        String standardJsonPayload = "{\"contents\": [{\"parts\": [{\"text\": \"" + escapedTextPayload + "\"}]}]}";

        HttpRequest outboundRequest = HttpRequest.newBuilder()
                .uri(URI.create(endpointTargetUrl))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(standardJsonPayload))
                .build();

        HttpResponse<String> inboundResponse = cloudNetworkClient.send(outboundRequest, HttpResponse.BodyHandlers.ofString());

        if (inboundResponse.statusCode() != 200) {
            return "Hyperscaler Server Error " + inboundResponse.statusCode() + ": " + inboundResponse.body();
        }

        return parseGeminiTextBlock(inboundResponse.body());
    }

    private String parseGeminiTextBlock(String jsonString) {
        Pattern regexPattern = Pattern.compile("\"text\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
        Matcher patternMatcher = regexPattern.matcher(jsonString);
        if (patternMatcher.find()) {
            return patternMatcher.group(1).replace("\\n", "\n").replace("\\\"", "\"").replace("\\\\", "\\");
        }
        return "Fallback Response Engine Log:\n" + jsonString;
    }
}
