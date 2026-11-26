import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

public class GridServer {
    private static final int PORT = 8082;
    private static final String OLLAMA_HOST = "http://localhost:11434/api/generate";
    private static final String TARGET_MODEL = "llama3";

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
        
        // Bind endpoint vectors
        server.createContext("/", new IndexHandler());
        server.createContext("/stream", new StreamHandler());
        
        // Mount virtual multi-threaded kernel routing substrate
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        
        System.out.println("================================================================================");
        System.out.printf("[GRID SERVER ACTIVE] Matrix host initialized at: http://localhost:%d/\n", PORT);
        System.out.println("================================================================================");
        server.start();
    }

    // ==============================================================================
    // OS PROCESS TABLE DISCOVERY SUBSTRATE
    // ==============================================================================
    private static String captureSystemContext() {
        StringBuilder contextBuilder = new StringBuilder();
        contextBuilder.append("Active Local Runtime Matrix Context State:\\n");
        long count = ProcessHandle.allProcesses().filter(process -> {
            String cmd = process.info().command().orElse("").toLowerCase();
            String fullCmdLine = process.info().commandLine().orElse("").toLowerCase();
            return cmd.contains("python") || fullCmdLine.contains(".py") || 
                   cmd.contains("java") || fullCmdLine.contains(".java") || fullCmdLine.contains(".jar");
        }).peek(process -> {
            String cmd = process.info().command().orElse("Unknown Process");
            String line = process.info().commandLine().orElse("");
            contextBuilder.append(String.format("- PID [%s] Runtime: %s Execute Arguments: [%s]\\n", 
                    process.pid(), cmd.substring(Math.max(0, cmd.lastIndexOf("/") + 1)), line.replace("\"", "\\\"")));
        }).count();

        if (count == 0) {
            return "No active local .java or .py software processes detected in execution space.";
        }
        return contextBuilder.toString();
    }

    // ==============================================================================
    // ENDPOINT 1: USER INTERFACE ROUTER
    // ==============================================================================
    static class IndexHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Grid LLaMA3 Orchestration Matrix</title>
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 93vh; }
                    .container { flex: 1; display: flex; flex-direction: column; max-width: 1200px; margin: 0 auto; width: 100%; border: 1px solid #30363d; border-radius: 6px; background-color: #161b22; overflow: hidden; }
                    .header { background-color: #21262d; padding: 15px 20px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
                    .header h1 { margin: 0; font-size: 1.2rem; color: #58a6ff; font-weight: 600; letter-spacing: 0.5px; }
                    .resonance-badge { background-color: rgba(56, 139, 253, 0.15); color: #58a6ff; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-family: monospace; border: 1px solid rgba(56, 139, 253, 0.4); }
                    .output-panel { flex: 1; padding: 20px; overflow-y: auto; font-family: monospace; font-size: 0.95rem; line-height: 1.6; white-space: pre-wrap; background-color: #0d1117; color: #e6edf3; }
                    .input-area { padding: 15px 20px; background-color: #21262d; border-top: 1px solid #30363d; display: flex; gap: 10px; }
                    input[type="text"] { flex: 1; background-color: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 12px; color: #e6edf3; font-size: 0.95rem; outline: none; }
                    input[type="text"]:focus { border-color: #58a6ff; box-shadow: 0 0 0 3px rgba(88,166,255,0.3); }
                    button { background-color: #238636; color: #ffffff; border: 1px solid rgba(240,246,252,0.1); border-radius: 6px; padding: 0 24px; font-size: 0.95rem; font-weight: 500; cursor: pointer; transition: background-color 0.2s; }
                    button:hover { background-color: #2ea043; }
                    button:disabled { background-color: #21262d; color: #8b949e; cursor: not-allowed; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>GRID OVERLAY MATRIX // HARDWARE EXECUTION REFACTORER</h1>
                        <div class="resonance-badge">CARRIER LNK // 7.83 HZ</div>
                    </div>
                    <div id="output" class="output-panel">System Substrate Ready. Awaiting prompt matrix input directives...</div>
                    <div class="input-area">
                        <input type="text" id="promptInput" placeholder="Enter system architectural optimization command directive..." onkeydown="if(event.key==='Enter') executeStream()">
                        <button id="sendBtn" onclick="executeStream()">EXECUTE</button>
                    </div>
                </div>

                <script>
                    function executeStream() {
                        const inputEl = document.getElementById('promptInput');
                        const outputEl = document.getElementById('output');
                        const btnEl = document.getElementById('sendBtn');
                        const prompt = inputEl.value.trim();
                        
                        if (!prompt) return;

                        inputEl.disabled = true;
                        btnEl.disabled = true;
                        outputEl.textContent = "[SYSTEM PROCESSING] Synchronizing kernel hooks and streaming LLaMA3 vector responses...\\n\\n";

                        // Initialize local Server-Sent Events stream pipeline vector
                        const eventSource = new EventSource('/stream?q=' + encodeURIComponent(prompt));

                        eventSource.onmessage = function(event) {
                            if (event.data === "[DONE]") {
                                eventSource.close();
                                inputEl.disabled = false;
                                btnEl.disabled = false;
                                inputEl.value = "";
                                inputEl.focus();
                            } else {
                                // Inject chunked response into text layout context area
                                outputEl.textContent += event.data;
                                outputEl.scrollTop = outputEl.scrollHeight;
                            }
                        };

                        eventSource.onerror = function(err) {
                            outputEl.textContent += "\\n\\n[CONNECTION RUNTIME FAILURE] Stream broken or model service offline.";
                            eventSource.close();
                            inputEl.disabled = false;
                            btnEl.disabled = false;
                        };
                    }
                </script>
            </body>
            </html>
            """;
            byte[] response = html.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
            exchange.sendResponseHeaders(200, response.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response);
            }
        }
    }

    // ==============================================================================
    // ENDPOINT 2: ASYNCHRONOUS SERVER-SENT EVENTS (SSE) STREAM ROUTER
    // ==============================================================================
    static class StreamHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            // Validate incoming query parameters
            String query = exchange.getRequestURI().getQuery();
            String userPrompt = "";
            if (query != null && query.startsWith("q=")) {
                userPrompt = java.net.URLDecoder.decode(query.substring(2), StandardCharsets.UTF_8);
            }

            // Set up SSE Event Stream response configuration headers
            exchange.getResponseHeaders().set("Content-Type", "text/event-stream");
            exchange.getResponseHeaders().set("Cache-Control", "no-cache");
            exchange.getResponseHeaders().set("Connection", "keep-alive");
            exchange.sendResponseHeaders(200, 0); // Use 0 to enable chunked transfer encoding transfer matrices

            OutputStream os = exchange.getResponseBody();
            PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, StandardCharsets.UTF_8), true);

            try {
                String systemContext = captureSystemContext();
                
                // Synthesize complete grid refinement payload
                String completePrompt = String.format(
                    "SYSTEM CONTEXT ENVIRONMENT:\\n%s\\n\\n" +
                    "OPTIMIZATION BASELINE FILTER: 7.83Hz Carrier Node Alignment Enabled.\\n\\n" +
                    "USER INSTRUCTION TASK: %s\\n\\n" +
                    "Output clear, refactored structural execution models strictly complying with the instructions.",
                    systemContext, userPrompt
                );

                // Open outbound connection channel straight to Ollama Service Core
                URL url = URI.create(OLLAMA_HOST).toURL();
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);

                // Clean string parameters to ensure valid outbound JSON construction shapes
                String escapedPrompt = completePrompt.replace("\\", "\\\\")
                                                     .replace("\"", "\\\"")
                                                     .replace("\n", "\\n")
                                                     .replace("\r", "\\r");

                String jsonPayload = String.format("{\"model\": \"%s\", \"prompt\": \"%s\", \"stream\": true}", TARGET_MODEL, escapedPrompt);

                try (OutputStream cos = conn.getOutputStream()) {
                    cos.write(jsonPayload.getBytes(StandardCharsets.UTF_8));
                }

                // Ingest active stream bytes token by token from Ollama and pipe out to Web Interface immediately
                if (conn.getResponseCode() == 200) {
                    try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            // Extract raw content out of json tokens cleanly without heavy library requirements
                            int textIndex = line.indexOf("\"response\":\"");
                            if (textIndex != -1) {
                                int start = textIndex + 12;
                                int end = line.indexOf("\",\"", start);
                                if (end != -1) {
                                    String chunk = line.substring(start, end)
                                                       .replace("\\n", "\n")
                                                       .replace("\\\"", "\"")
                                                       .replace("\\\\", "\\");
                                    
                                    // SSE Format standard specification data messaging lines
                                    writer.print("data: " + chunk.replace("\n", "\ndata: ") + "\n\n");
                                    writer.flush();
                                }
                            }
                        }
                    }
                } else {
                    writer.print("data: [OLLAMA EXCEPTION HTTP ERROR CODE " + conn.getResponseCode() + "]\n\n");
                }
            } catch (Exception e) {
                writer.print("data: [STREAM PROCESSING ERROR: " + e.getMessage() + "]\n\n");
            } finally {
                // Terminate SSE Stream pipe cleanly allowing UI components to unblock
                writer.print("data: [DONE]\n\n");
                writer.flush();
                exchange.close();
            }
        }
    }
}


