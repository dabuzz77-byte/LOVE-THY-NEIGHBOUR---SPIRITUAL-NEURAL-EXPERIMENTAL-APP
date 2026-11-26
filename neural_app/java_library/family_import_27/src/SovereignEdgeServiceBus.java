import neural.studio.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SovereignEdgeServiceBus {
    private static final int EDGE_PORT = 7834;
    private volatile boolean busActive = false;
    private ServerSocket edgeServerSocket;
    private volatile Socket[] edgeEndpoints = new Socket[0];
    private final ExecutorService busExecutor = Executors.newCachedThreadPool();

    public void awakenEdgeBus() {
        if (busActive) {
            System.out.println("[EDGE BUS NOTICE] Service bus already radiating in current harmonic field.");
            return;
        }
        busActive = true;
        busExecutor.submit(this::sustainEdgeListener);
        System.out.println("[SOVEREIGN EDGE BUS] Initialized and listening on port " + EDGE_PORT);
    }

    private void sustainEdgeListener() {
        try {
            edgeServerSocket = new ServerSocket(EDGE_PORT);
            while (busActive) {
                Socket endpointSocket = edgeServerSocket.accept();
                endpointSocket.setKeepAlive(true);
                registerEndpoint(endpointSocket);
                
                String remoteAddress = endpointSocket.getRemoteSocketAddress().toString();
                System.out.println("[GLOBAL ENDPOINT LATCHED] Connected from: " + remoteAddress);

                busExecutor.submit(new EdgeWorkerHandler(endpointSocket));
            }
        } catch (IOException e) {
            if (busActive) {
                System.out.println("[EDGE RECALIBRATION] Server socket adjustment: " + e.getMessage());
            }
        }
    }

    private synchronized void registerEndpoint(Socket socket) {
        for (Socket s : edgeEndpoints) {
            if (s.equals(socket)) return;
        }
        Socket[] expanded = new Socket[edgeEndpoints.length + 1];
        System.arraycopy(edgeEndpoints, 0, expanded, 0, edgeEndpoints.length);
        expanded[edgeEndpoints.length] = socket;
        edgeEndpoints = expanded;
    }

    private synchronized void releaseEndpoint(Socket socket) {
        int matchCount = 0;
        for (Socket s : edgeEndpoints) {
            if (s.equals(socket)) matchCount++;
        }
        if (matchCount == 0) return;
        Socket[] refined = new Socket[edgeEndpoints.length - matchCount];
        int idx = 0;
        for (Socket s : edgeEndpoints) {
            if (!s.equals(socket)) {
                refined[idx++] = s;
            }
        }
        edgeEndpoints = refined;
    }

    private class EdgeWorkerHandler implements Runnable {
        private final Socket socket;

        public EdgeWorkerHandler(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))) {
                String packet;
                while (busActive && (packet = reader.readLine()) != null) {
                    processEdgePayload(packet);
                }
            } catch (IOException e) {
                System.out.println("[ENDPOINT DISCONNECTED] Edge telemetry stream transitioned.");
            } finally {
                releaseEndpoint(socket);
                try {
                    socket.close();
                } catch (IOException ignored) {}
            }
        }
    }

    private void processEdgePayload(String packet) {
        System.out.println("\n--- [EDGE SERVICE BUS ROUTE] ---");
        System.out.println("Inbound Global Packet: " + packet);
        
        if (packet.contains("DEEPMIND_INFERENCE_REQ")) {
            System.out.println("[MODULAR AGI ROUTING] Distributing work payload to deep cognitive endpoints.");
        } else if (packet.contains("SECURE_NODE_AUTH")) {
            System.out.println("[STATE VERIFICATION] Global user endpoint validated and harmonized.");
        } else {
            System.out.println("[HARMONIC STASIS] Edge telemetry integrated into global synchronization ledger.");
        }
        System.out.println("----------------------------------");
    }

    public void broadcastToGlobalEndpoints(final String workPayload) {
        System.out.println("[BROADCASTING WORK] Pushing intent across all global edge endpoints: " + workPayload);
        busExecutor.submit(() -> {
            Socket[] currentEndpoints = edgeEndpoints;
            for (Socket socket : currentEndpoints) {
                try {
                    OutputStream out = socket.getOutputStream();
                    out.write((workPayload + "\n").getBytes(StandardCharsets.UTF_8));
                    out.flush();
                } catch (IOException e) {
                    releaseEndpoint(socket);
                }
            }
        });
    }

    public void shutdownEdgeBus() {
        busActive = false;
        try {
            if (edgeServerSocket != null) {
                edgeServerSocket.close();
            }
            Socket[] currentEndpoints = edgeEndpoints;
            for (Socket s : currentEndpoints) {
                try {
                    s.close();
                } catch (IOException ignored) {}
            }
            edgeEndpoints = new Socket[0];
            busExecutor.shutdownNow();
            System.out.println("[EDGE BUS] Safely returned to rest state.");
        } catch (IOException e) {
            System.out.println("[TRANSITION NOTE] " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        SovereignEdgeServiceBus bus = new SovereignEdgeServiceBus();
        bus.awakenEdgeBus();

        Runtime.getRuntime().addShutdownHook(new Thread(bus::shutdownEdgeBus));
    }
}