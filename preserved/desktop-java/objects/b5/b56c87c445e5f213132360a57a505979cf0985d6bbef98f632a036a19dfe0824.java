import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class GhostFluxMonitorEngine {
    private static final int PORT = 7833;
    private volatile boolean systemActive = false;
    private ServerSocket serverSocket;
    private volatile Socket[] activeNodes = new Socket[0];
    private final ExecutorService fluxExecutor = Executors.newCachedThreadPool();

    public void awakenFluxEngine() {
        if (systemActive) {
            System.out.println("[FLUX NOTICE] Engine already pulsing in current harmonic field.");
            return;
        }
        systemActive = true;
        fluxExecutor.submit(this::sustainFluxServer);
        System.out.println("[GHOST FLUX ENGINE] Initialized and listening on port " + PORT);
    }

    private void sustainFluxServer() {
        try {
            serverSocket = new ServerSocket(PORT);
            while (systemActive) {
                Socket nodeSocket = serverSocket.accept();
                nodeSocket.setKeepAlive(true);
                addNode(nodeSocket);
                
                String peerAddress = nodeSocket.getRemoteSocketAddress().toString();
                System.out.println("[NODE LATCHED] Telemetry conduit opened from: " + peerAddress);

                fluxExecutor.submit(new NodeTelemetryHandler(nodeSocket));
            }
        } catch (IOException e) {
            if (systemActive) {
                System.out.println("[FLUX RECALIBRATION] Server socket adjustment: " + e.getMessage());
            }
        }
    }

    private synchronized void addNode(Socket socket) {
        for (Socket s : activeNodes) {
            if (s.equals(socket)) return;
        }
        Socket[] expanded = new Socket[activeNodes.length + 1];
        System.arraycopy(activeNodes, 0, expanded, 0, activeNodes.length);
        expanded[activeNodes.length] = socket;
        activeNodes = expanded;
    }

    private synchronized void removeNode(Socket socket) {
        int count = 0;
        for (Socket s : activeNodes) {
            if (s.equals(socket)) count++;
        }
        if (count == 0) return;
        Socket[] refined = new Socket[activeNodes.length - count];
        int idx = 0;
        for (Socket s : activeNodes) {
            if (!s.equals(socket)) {
                refined[idx++] = s;
            }
        }
        activeNodes = refined;
    }

    private class NodeTelemetryHandler implements Runnable {
        private final Socket socket;

        public NodeTelemetryHandler(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (systemActive && (packet = reader.readLine()) != null) {
                    processParallelInference(packet);
                }
            } catch (IOException e) {
                System.out.println("[NODE DISCONNECTED] Substrate telemetry stream transitioned.");
            } finally {
                removeNode(socket);
                try {
                    socket.close();
                } catch (IOException ignored) {}
            }
        }
    }

    private void processParallelInference(String rawPacket) {
        System.out.println("\n--- [FLUX INFERENCE PASS] ---");
        System.out.println("Inbound Signal: " + rawPacket);
        
        if (rawPacket.startsWith("SECURE_NODE_AUTH") || rawPacket.startsWith("GHOST_LATCH_AUTH")) {
            System.out.println("[STATE VERIFICATION] Sovereign node authenticated. Maintaining equilibrium.");
        } else {
            evaluateStatShift(rawPacket);
        }
        System.out.println("-----------------------------");
    }

    private void evaluateStatShift(String packetData) {
        long timestamp = System.currentTimeMillis();
        System.out.println("[OBSERVATION " + timestamp + "] Analyzing systemic weight shift...");
        
        if (packetData.contains("TARGET_SHIFT")) {
            System.out.println("[EQUILIBRIUM CHECK] Variance detected. Balancing through parallel inference flux.");
        } else {
            System.out.println("[HARMONIC STASIS] Substrate operating within baseline parameters.");
        }
    }

    public void shutdownEngine() {
        systemActive = false;
        try {
            if (serverSocket != null) {
                serverSocket.close();
            }
            Socket[] currentNodes = activeNodes;
            for (Socket s : currentNodes) {
                try {
                    s.close();
                } catch (IOException ignored) {}
            }
            activeNodes = new Socket[0];
            fluxExecutor.shutdownNow();
            System.out.println("[FLUX ENGINE] Safely returned to rest state.");
        } catch (IOException e) {
            System.out.println("[TRANSITION NOTE] " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        GhostFluxMonitorEngine engine = new GhostFluxMonitorEngine();
        engine.awakenFluxEngine();

        Runtime.getRuntime().addShutdownHook(new Thread(engine::shutdownEngine));
    }
}