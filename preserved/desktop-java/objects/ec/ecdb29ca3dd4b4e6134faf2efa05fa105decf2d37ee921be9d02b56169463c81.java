import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class GodMindWindowsDaemon {
    private static final int PORT = 7836;
    private static volatile boolean serviceActive = true;
    private static ServerSocket serverSocket;
    private static final ExecutorService executor = Executors.newCachedThreadPool();

    public static void main(String[] args) {
        logSystemEvent("God Mind Windows Daemon initializing system substrate...");

        if (args.length > 0 && args[0].equalsIgnoreCase("install")) {
            logSystemEvent("Service registration protocol invoked.");
            return;
        }

        sustainDaemonLoop();
    }

    private static void sustainDaemonLoop() {
        try {
            serverSocket = new ServerSocket(PORT);
            logSystemEvent("God Mind core successfully bound to port " + PORT + " across Windows substrate.");

            while (serviceActive) {
                Socket clientSocket = serverSocket.accept();
                clientSocket.setKeepAlive(true);
                executor.submit(() -> handleClient(clientSocket));
            }
        } catch (IOException e) {
            logSystemEvent("Daemon socket adjustment: " + e.getMessage());
        } finally {
            shutdownDaemon();
        }
    }

    private static void handleClient(Socket socket) {
        try (var reader = new java.io.BufferedReader(new java.io.InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
            String packet;
            while (serviceActive && (packet = reader.readLine()) != null) {
                logSystemEvent("Inbound telemetry packet integrated: " + packet);
            }
        } catch (IOException e) {
            logSystemEvent("Client stream transitioned.");
        } finally {
            try {
                socket.close();
            } catch (IOException ignored) {}
        }
    }

    public static void shutdownDaemon() {
        serviceActive = false;
        try {
            if (serverSocket != null) serverSocket.close();
            executor.shutdownNow();
            logSystemEvent("God Mind daemon safely returned to rest state.");
        } catch (IOException e) {
            logSystemEvent("Shutdown adjustment: " + e.getMessage());
        }
    }

    private static void logSystemEvent(String message) {
        String logEntry = "[GOD MIND WINDOWS DAEMON] " + message;
        System.out.println(logEntry);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File("godmind_system.log"), true))) {
            out.println(logEntry);
        } catch (IOException ignored) {}
    }
}