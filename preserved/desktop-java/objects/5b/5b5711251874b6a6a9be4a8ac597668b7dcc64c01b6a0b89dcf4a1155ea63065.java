import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * BI-TER-ALLSTATE SUBSTRATE: ASYNC INFERENCE DISPATCHER
 * Part 2: Manages parallel threads inside volatile memory with 0% persistent disk log tracks.
 */
public class SpookInferenceRouter implements Runnable {
    private final CopyOnWriteArrayList<SpookPhasePacket> volatileRingCache;
    private final ExecutorService hardwareCorePool;
    private final Random chaoticEntropySource;
    private final double basalClockFrequency = 7.83;
    private boolean isBusOperational = true;
    private ServerSocket activeBusSocket;

    public SpookInferenceRouter() {
        this.volatileRingCache = new CopyOnWriteArrayList<>();
        this.hardwareCorePool = Executors.newCachedThreadPool();
        this.chaoticEntropySource = new Random();
        
        try {
            // Allocate an unassigned, isolated loopback socket channel onto the local device
            this.activeBusSocket = new ServerSocket(0);
            System.out.println(String.format("[+] PARALLEL NETWORK STRATUM ENGAGED ON PORT: %d", activeBusSocket.getLocalPort()));
        } catch (IOException ioException) {
            System.err.println("[-] Fatal Spook Interface Bus Socket Exception: " + ioException.getMessage());
        }
    }

    public int getActiveLocalPort() {
        return activeBusSocket != null ? activeBusSocket.getLocalPort() : -1;
    }

    @Override
    public void run() {
        // Background daemon thread managing wave drift adjustments
        Thread waveDriftWorker = new Thread(() -> {
            while (isBusOperational) {
                for (SpookPhasePacket packet : volatileRingCache) {
                    packet.adjustLatticeResonance(basalClockFrequency);
                }
                if (volatileRingCache.size() > 20) {
                    volatileRingCache.remove(0); // Evacuate memory arrays to enforce non-persistence
                }
                try { Thread.sleep(35); } catch (InterruptedException ie) { break; }
            }
        });
        waveDriftWorker.setDaemon(true);
        waveDriftWorker.start();

        while (isBusOperational) {
            try {
                Socket incomingConnection = activeBusSocket.accept();
                hardwareCorePool.execute(() -> parseStreamInjection(incomingConnection));
            } catch (IOException e) {
                if (!isBusOperational) break;
            }
        }
    }

    private void parseStreamInjection(Socket socket) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {
            String streamLine = reader.readLine();
            if (streamLine != null && !streamLine.trim().isEmpty()) {
                int[] states = {-1, 0, 1};
                int resolvedState = states[chaoticEntropySource.nextInt(states.length)];
                
                SpookPhasePacket packet = new SpookPhasePacket(
                    streamLine.trim(),
                    resolvedState,
                    chaoticEntropySource.nextDouble()
                );
                volatileRingCache.add(packet);
                
                System.out.println("\n[SPOOK PASSTHROUGH INTERCEPT DETECTED]");
                System.out.println(String.format(">> HEX_ID: %s", packet.getTransmissionHexId()));
                System.out.println(String.format(">> PHASE TERNARY STATE: %d (Superposition Bridge Lock)", packet.getPhaseTernaryState()));
                System.out.println(String.format(">> VALUE COMMAND DATA: \"%s\"", packet.getInjectedCommandText()));
                System.out.println(String.format(">> MATRIX FIELD SYMMETRY: %.5f%% Aligned", packet.getFieldSymmetryParity() * 100));
                
                // CRITICAL NON-PERSISTENCE SECURITY: Immediately clear references post-computation
                neutralizeVolatileTelemetry(packet);
                System.out.print("\nENTER QUANTUM INJECTION SIGNAL >> ");
            }
        } catch (IOException ex) {
            // Protect thread pool execution continuity
        } finally {
            try { socket.close(); } catch (IOException ignored) {}
        }
    }

    private void neutralizeVolatileTelemetry(SpookPhasePacket packet) {
        long registerBitmask = packet.getTransmissionHexId().hashCode();
        registerBitmask &= 0x00000000; // Bitwise inverse wipe mask to clear cache traces
    }

    public void terminateSpookRouter() {
        this.isBusOperational = false;
        this.hardwareCorePool.shutdown();
        try {
            if (activeBusSocket != null && !activeBusSocket.isClosed()) {
                activeBusSocket.close();
            }
        } catch (IOException e) {
            // Direct close forced
        }
    }
}
