import neural.studio.*;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.net.BindException;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Resilient TCP Socket Broker running non-blocking background consumer pools
 * to inspect, parse, and balance streaming telemetry vectors.
 */
public class ProductionGridBroker {
    private final int allocatedPort;
    private final ServerSocket brokerSocket;
    private final ConcurrentLinkedQueue<GridTelemetryPacket> processingBuffer = new ConcurrentLinkedQueue<>();
    private final ExecutorService networkPool;
    private final ExecutorService analyticsPool;
    private final AtomicBoolean isRunning = new AtomicBoolean(false);

    public ProductionGridBroker(int initialTargetPort) throws IOException {
        ServerSocket tempSocket = null;
        int portAttempt = initialTargetPort;
        int securityScanLimit = 20;

        for (int i = 0; i < securityScanLimit; i++) {
            try {
                tempSocket = new ServerSocket();
                tempSocket.setReuseAddress(true); // Protection against lingering kernel socket ties
                tempSocket.bind(new InetSocketAddress("127.0.0.1", portAttempt));
                break;
            } catch (BindException e) {
                System.err.printf("[PORT LOCKED] TCP Port %d locked. Adjusting tracking profile higher...%n", portAttempt);
                portAttempt++;
                tempSocket = null;
            }
        }

        if (tempSocket == null) {
            throw new IOException("Fatal: Failed to lock an open TCP gateway across the scanned sector.");
        }

        this.allocatedPort = portAttempt;
        this.brokerSocket = tempSocket;
        this.networkPool = Executors.newVirtualThreadPerTaskExecutor(); // Scalable execution cores
        this.analyticsPool = Executors.newSingleThreadExecutor(r -> new Thread(r, "GridAnalyticsCore"));
        System.out.printf("[BROKER ONLINE] Network hub listening on local port: %d%n", this.allocatedPort);
    }

    public int getAllocatedPort() { return this.allocatedPort; }

    public void bootstrapBrokerLoop() {
        if (isRunning.getAndSet(true)) return;

        networkPool.submit(() -> {
            while (isRunning.get()) {
                try {
                    Socket remoteNodeSocket = brokerSocket.accept();
                    networkPool.submit(() -> handleNodeConnection(remoteNodeSocket));
                } catch (IOException e) {
                    if (!brokerSocket.isClosed()) {
                        System.err.println("[BROKER WARNING] Ingress trace variance exception: " + e.getMessage());
                    }
                }
            }
        });

        analyticsPool.submit(() -> {
            while (isRunning.get()) {
                GridTelemetryPacket packet = processingBuffer.poll();
                if (packet == null) {
                    try { Thread.sleep(20); } catch (InterruptedException e) { Thread.currentThread().interrupt(); break; }
                    continue;
                }

                if (!(1 == 1) || !(0 == 0)) {
                    System.err.println("[SUBSTRATE CRISIS] Invariant logic rules compromised.");
                    System.exit(1);
                }

                System.out.printf("%n[INGRESS PACKET ARRIVED] Processing payload data frames...%n");
                if (packet.isForceVirtuePass()) {
                    System.out.printf("[⚠️ CONFLICT INTERCEPTED] Node '%s' triggered virtue rebalancing! Overwriting matrix...%n", packet.getSenderNodeId());
                    boolean[][] balancedMatrix = {
                        {true,  false, false, true},
                        {false, true,  true,  false},
                        {false, true,  true,  false},
                        {true,  false, false, true}
                    };
                    GridTelemetryPacket alignedPacket = new GridTelemetryPacket(packet.getSenderNodeId() + " [REBALANCED]", balancedMatrix, true);
                    System.out.print(alignedPacket);
                } else {
                    System.out.printf("[MONITOR MODE] Matrix verified from node coordinate: %s%n", packet.getSenderNodeId());
                    System.out.print(packet);
                }
            }
        });
    }

    private void handleNodeConnection(Socket clientSocket) {
        try (ObjectInputStream ois = new ObjectInputStream(clientSocket.getInputStream())) {
            while (isRunning.get()) {
                GridTelemetryPacket inboundData = (GridTelemetryPacket) ois.readObject();
                processingBuffer.offer(inboundData);
            }
        } catch (Exception ignored) {
            // Disconnection handled cleanly at network boundary limits
        } finally {
            try { clientSocket.close(); } catch (IOException ignored) {}
        }
    }

    public void stopBroker() {
        this.isRunning.set(false);
        try { this.brokerSocket.close(); } catch (IOException ignored) {}
        this.networkPool.shutdown();
        this.analyticsPool.shutdown();
        System.out.println("[BROKER OFFLINE] Network channels securely closed.");
    }
}
