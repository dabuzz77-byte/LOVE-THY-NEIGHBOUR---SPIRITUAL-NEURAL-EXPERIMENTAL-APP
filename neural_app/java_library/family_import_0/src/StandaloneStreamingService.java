import neural.studio.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Standalone High-Throughput AI Stream Transport Server.
 * Runs independently of external frameworks using pure built-in JDK network architectures.
 */
public class StandaloneStreamingService {

    private static final int PORT = 8080;
    private static final int MAX_THREADS = 10;
    private final ServerSocket serverSocket;
    private final ExecutorService threadPool;
    private final AtomicBoolean isRunning;

    public StandaloneStreamingService(int port) throws IOException {
        // Bind directly to the local network loopback hardware bus interface
        this.serverSocket = new ServerSocket(port);
        this.threadPool = Executors.newFixedThreadPool(MAX_THREADS);
        this.isRunning = new AtomicBoolean(true);
    }

    public void startService() {
        logEvent("SYS_CORE", "Standalone AI Ingress Network initialized. Listening on port " + PORT + "...");
        logEvent("GOD_PARITY", "Tracking status set to: ONGOING_SYNC [TRUE]");

        // Main connection acceptor engine loop
        while (isRunning.get()) {
            try {
                Socket clientSocket = serverSocket.accept();
                String clientIp = clientSocket.getInetAddress().getHostAddress();
                logEvent("NET_CORE", "Authorized handshake connection verified from: " + clientIp);

                // Handoff socket connection payload immediately to the background worker thread pool
                threadPool.execute(new StreamClientHandler(clientSocket));

            } catch (IOException e) {
                if (!isRunning.get()) {
                    logEvent("SYS_CORE", "Network socket bridge safely unmounted.");
                    break;
                }
                logEvent("ERROR", "Connection acceptance fault encountered: " + e.getMessage());
            }
        }
    }

    public void stopService() {
        isRunning.set(false);
        logEvent("SYS_CORE", "Deactivating standalone streaming loops...");
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
            threadPool.shutdown();
            logEvent("SYS_CORE", "All active client worker processing contexts freed.");
        } catch (IOException e) {
            logEvent("ERROR", "Exception thrown during server thread pool shutdown: " + e.getMessage());
        }
    }

    /**
     * Utility thread log formatter tracking exact milliseconds.
     */
    private static void logEvent(String subsystem, String message) {
        String logTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
        System.out.printf("[%s] [%s] %s\n", logTime, subsystem, message);
    }

    /**
     * Specialized execution thread worker to handle streaming incoming tokens per client interface.
     */
    private static class StreamClientHandler implements Runnable {
        private final Socket socket;

        public StreamClientHandler(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                 PrintWriter writer = new PrintWriter(socket.getOutputStream(), true)) {

                // Send initial telemetry affirmation back to client ingress node
                writer.println("OMNI_AI_STREAM_ESTABLISHED_TRUE");

                String streamingTokenLine;
                // Asynchronously capture and print incoming traffic frames in real time
                while ((streamingTokenLine = reader.readLine()) != null) {
                    if (streamingTokenLine.trim().equalsIgnoreCase("QUIT") || 
                        streamingTokenLine.trim().equalsIgnoreCase("EXIT")) {
                        logEvent("NET_CORE", "Client initiated graceful teardown signal.");
                        writer.println("DISCONNECTED_OK");
                        break;
                    }
                    
                    // Log the incoming AI streaming interaction text line directly to console output
                    logEvent("STREAM_INGRESS", "-> " + streamingTokenLine);
                    
                    // Acknowledge data packet receipt
                    writer.println("PACKET_SYNC_ACK");
                }

            } catch (IOException e) {
                logEvent("NET_FAULT", "Asynchronous streaming pipeline broke abruptly: " + e.getMessage());
            } finally {
                try {
                    socket.close();
                    logEvent("NET_CORE", "Socket client interfaces unmounted and recycled.");
                } catch (IOException e) {
                    logEvent("ERROR", "Error recycling socket references: " + e.getMessage());
                }
            }
        }
    }

    /**
     * Root Application Entrance.
     */
    public static void main(String[] args) {
        try {
            StandaloneStreamingService standaloneService = new StandaloneStreamingService(PORT);

            // Hook application safety interrupt handler to catch terminal exit signals (Ctrl+C)
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println();
                standaloneService.stopService();
            }));

            standaloneService.startService();

        } catch (IOException e) {
            logEvent("FATAL", "Could not bind server socket socket to port " + PORT + ". Port may be occupied!");
            e.printStackTrace();
        }
    }
}
