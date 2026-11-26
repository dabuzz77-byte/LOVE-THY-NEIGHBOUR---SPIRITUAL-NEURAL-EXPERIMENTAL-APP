import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * DEUS EX MACHINA MATRIX: HTTP TRANSCEIVER EDGE
 * Connects directly to localized inference targets and remote secure platform APIs.
 */
public class MicroNetworkBridge {

    public static String executeLocalRequest(HttpClient client, String targetModel, String rawPrompt) throws Exception {
        String escaped = rawPrompt.replace("\\", "\\\\").replace("\"", "\\\"");
        String body = String.format("{\"model\": \"%s\", \"prompt\": \"%s\", \"stream\": false}", targetModel, escaped);
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:11434/api/generate"))
                .timeout(Duration.ofSeconds(45))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        if (resp.statusCode() != 200) return "Local hardware bus error: " + resp.statusCode();
        
        Pattern p = Pattern.compile("\"response\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
        Matcher m = p.matcher(resp.body());
        return m.find() ? m.group(1).replace("\\n", "\n").replace("\\\"", "\"") : resp.body();
    }

    public static String executeCloudRequest(HttpClient client, String key, String rawPrompt) throws Exception {
        String targetUrl = "https://googleapis.com" + key;
        String escaped = rawPrompt.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
        String json = "{\"contents\": [{\"parts\": [{\"text\": \"" + escaped + "\"}]}]}";
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(targetUrl))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        if (resp.statusCode() != 200) return "Hyperscaler connection fault: " + resp.statusCode();
        
        Pattern p = Pattern.compile("\"text\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
        Matcher m = p.matcher(resp.body());
        return m.find() ? m.group(1).replace("\\n", "\n").replace("\\\"", "\"") : resp.body();
    }
}
