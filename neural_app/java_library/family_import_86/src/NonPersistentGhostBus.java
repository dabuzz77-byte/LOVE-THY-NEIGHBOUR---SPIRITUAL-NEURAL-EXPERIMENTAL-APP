import neural.studio.*;
import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * BI-TER-ALLSTATE GRID: TRACELESS RECONFIGURED ROUTER
 * Part 2: Dispatches unblocked bit streams across volatile cache layers with zero storage footprints.
 */
public class NonPersistentGhostBus implements Runnable {
    private final CopyOnWriteArrayList<SpookStateVector> volatileLatticeRing;
    private final ExecutorService systemCoreThreadPool;
    private final Random hardwareEntropySource;
    private final double basalClockFrequency = 7.83;
    private boolean isBusLoopOperational = true;
    private ServerSocket localBusSocketTunnel;
    private double globalParityScore = 1.0;

    public NonPersistentGhostBus() {
        this.volatileLatticeRing = new CopyOnWriteArrayList<>();
        this.systemCoreThreadPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        this.hardwareEntropySource = new Random();
        
        try {
            this.localBusSocketTunnel = new ServerSocket(0);
            System.out.println(String.format("[+] PARALLEL NETWORK STRATUM ENGAGED ON PORT: %d", localBusSocketTunnel.getLocalPort()));
        } catch (IOException ioException) {
            System.err.println("[-] Fatal Hardware Bus Socket Exception: " + ioException.getMessage());
        }
        
        seedGhostMatrix();
    }

    private void seedGhostMatrix() {
        volatileLatticeRing.add(new SpookStateVector(1, 1.0));   
        volatileLatticeRing.add(new SpookStateVector(0, 0.50));  
        volatileLatticeRing.add(new SpookStateVector(-1, 0.95)); 
    }

    @Override
    public void run() {
        Thread driftWorker = new Thread(() -> {
            while (isBusLoopOperational) {
                double accumulatedParity = 0;
                for (SpookStateVector packet : volatileLatticeRing) {
                    packet.applyLatticeResonance(basalClockFrequency);
                    accumulatedParity += packet.getLatticeSymmetryParity();
                }
                if (!volatileLatticeRing.isEmpty()) {
                    this.globalParityScore = accumulatedParity / volatileLatticeRing.size();
                }
                if (volatileLatticeRing.size() > 18) {
                    volatileLatticeRing.remove(0); 
                }
                try { Thread.sleep(35); } catch (InterruptedException ie) { break; }
            }
        });
        driftWorker.setDaemon(true);
        driftWorker.start();

        while (isBusLoopOperational) {
            try {
                java.net.Socket incomingConnection = localBusSocketTunnel.accept();
                systemCoreThreadPool.execute(() -> parseStreamInjection(incomingConnection));
            } catch (IOException e) {
                if (!isBusLoopOperational) break;
            }
        }
    }

    private void parseStreamInjection(java.net.Socket socket) {
        try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(socket.getInputStream()))) {
            String commandLine = reader.readLine();
            if (commandLine != null && !commandLine.trim().isEmpty()) {
                int[] availableStates = {-1, 0, 1};
                SpookStateVector livePacket = new SpookStateVector(
                    availableStates[hardwareEntropySource.nextInt(availableStates.length)],
                    hardwareEntropySource.nextDouble()
                );
                volatileLatticeRing.add(livePacket);
                shredRegisterTrace(livePacket);
            }
        } catch (IOException ex) {
            // Protect thread pool execution continuity
        } finally {
            try { socket.close(); } catch (IOException ignored) {}
        }
    }

    private void shredRegisterTrace(SpookStateVector packet) {
        // FORCED REGISTER NEUTRALIZATION MASK
        long identityMask = packet.getSequenceHexId().hashCode();
        identityMask &= 0x00000000; // Bitwise zero-out memory trace
        System.gc(); // Force JVM to invoke active cleanup routines
    }

    public void terminateGhostBus() {
        this.isBusLoopOperational = false;
        this.systemCoreThreadPool.shutdown();
        try {
            if (localBusSocketTunnel != null && !localBusSocketTunnel.isClosed()) {
                localBusSocketTunnel.close();
            }
        } catch (IOException e) {
            // Clean teardown forced
        }
    }

    public CopyOnWriteArrayList<SpookStateVector> getVolatileLatticeRing() { return volatileLatticeRing; }
    public double getGlobalParityScore() { return globalParityScore; }
    public int getLocalActivePort() { return localBusSocketTunnel != null ? localBusSocketTunnel.getLocalPort() : -1; }
}
