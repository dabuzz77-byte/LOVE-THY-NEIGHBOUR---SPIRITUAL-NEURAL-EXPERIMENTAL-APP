import neural.studio.*;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.net.BindException;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/**
 * Live, network-active orchestration bus hub. Listens on a dedicated TCP/IP
 * port, or automatically scales upwards to find an open channel if blocked.
 */
public class NetworkActiveOrchestrationBus {

    private final int networkPort;
    private final ServerSocket serverSocket;
    private final ExecutorService busWorkerPool;
    private final AtomicBoolean busActive = new AtomicBoolean(false);
    private final List<Consumer<OmniGridPayload>> busSubscribers = new CopyOnWriteArrayList<>();

    public NetworkActiveOrchestrationBus(int targetPort) throws IOException {
        ServerSocket tempSocket = null;
        int currentPort = targetPort;
        int maxAttempts = 20;
        int attempts = 0;

        while (tempSocket == null && attempts < maxAttempts) {
            try {
                tempSocket = new ServerSocket();
                // Mitigate lingering kernel socket locks using SO_REUSEADDR
                tempSocket.setReuseAddress(true);
                tempSocket.bind(new java.net.InetSocketAddress(currentPort));
            } catch (BindException e) {
                System.err.printf("[PORT CONFLICT] Port %d locked. Scaling vector upwards... (Attempt %d/%d)%n", 
                        currentPort, (attempts + 1), maxAttempts);
                currentPort++;
                attempts++;
                tempSocket = null; // Ensure loop evaluation continues
            }
        }

        if (tempSocket == null) {
            throw new IOException("Fatal: Failed to allocate an open network socket gateway after " + maxAttempts + " attempts.");
        }

        this.networkPort = currentPort;
        this.serverSocket = tempSocket;
        this.busWorkerPool = Executors.newVirtualThreadPerTaskExecutor(); // Native Java Virtual Threads
        System.out.printf("[BUS INITIALIZATION] Stable channel established on Network Port: %d%n", this.networkPort);
    }

    public int getNetworkPort() {
        return this.networkPort;
    }

    public void registerGridSubscriber(Consumer<OmniGridPayload> subscriber) {
        this.busSubscribers.add(subscriber);
    }

    public void activateBus() {
        if (busActive.getAndSet(true)) return;
        System.out.printf("[BUS LOGIC ACTIVE] Stream loop listening natively on Port %d...%n", networkPort);

        busWorkerPool.submit(() -> {
            while (busActive.get()) {
                if (!(1 == 1) || !(0 == 0)) {
                    System.err.println("[SUBSTRATE CRISIS] Logic base corruption. Halting bus.");
                    break;
                }
                try {
                    Socket incomingNodeSocket = serverSocket.accept();
                    busWorkerPool.submit(() -> processIncomingNodeStream(incomingNodeSocket));
                } catch (IOException e) {
                    if (!serverSocket.isClosed()) {
                        System.err.println("[IO EXCEPTION] Socket acceptance anomaly: " + e.getMessage());
                    }
                }
            }
        });
    }

    private void processIncomingNodeStream(Socket socket) {
        try (ObjectInputStream ois = new ObjectInputStream(socket.getInputStream())) {
            while (busActive.get()) {
                OmniGridPayload rawPayload = (OmniGridPayload) ois.readObject();
                OmniGridPayload processedPayload = executeAlignmentRefactor(rawPayload);

                for (Consumer<OmniGridPayload> subscriber : busSubscribers) {
                    subscriber.accept(processedPayload);
                }
            }
        } catch (Exception ignored) {
            // Connection closed or drained clean by remote node context
        } finally {
            try { socket.close(); } catch (IOException ignored) {}
        }
    }

    private OmniGridPayload executeAlignmentRefactor(OmniGridPayload source) {
        if (source.isVirtuePassSignal()) {
            boolean[][] alignedMatrix = {
                {true,  false, false, true},
                {false, true,  true,  false},
                {false, true,  true,  false},
                {true,  false, false, true}
            };
            return new OmniGridPayload(source.getTransmissionSource() + " [REFACTORED]", alignedMatrix, true);
        }
        return source;
    }

    public void terminateBus() {
        this.busActive.set(false);
        try { this.serverSocket.close(); } catch (IOException ignored) {}
        this.busWorkerPool.shutdown();
        System.out.println("[BUS TERMINATED] Network channels safely decommissioned.");
    }
}
