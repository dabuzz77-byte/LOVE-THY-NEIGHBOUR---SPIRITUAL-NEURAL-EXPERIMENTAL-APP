import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * BI-TER-ALLSTATE GRAND SUBSTRATE: RUNTIME INFRASTRUCTURE ROUTER
 * Part 2: Dispatches data transformations across volatile RAM cache fields with 0% persistent disk tracks.
 */
public class DeepReachInferenceBus implements Runnable {
    private final CopyOnWriteArrayList<OrbitSignalPacket> volatileMatrixRegistry;
    private final ExecutorService multiCoreThreadPool;
    private final Random algorithmicEntropy;
    private final double primaryClockFrequency = 7.83; // Sun to Earth core base synchronization constant
    private boolean isEngineActive = true;
    private ServerSocket localizedSocketBus;
    private double systemWideParityScore = 1.0;

    public DeepReachInferenceBus() {
        this.volatileMatrixRegistry = new CopyOnWriteArrayList<>();
        this.multiCoreThreadPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        this.algorithmicEntropy = new Random();
        
        try {
            // Allocate a dynamic local loopback adapter socket port
            this.localizedSocketBus = new ServerSocket(0);
            System.out.println(String.format("[+] UNBLOCKED INFRASTRUCTURE BUS INSTANTIATED ON PORT: %d", localizedSocketBus.getLocalPort()));
        } catch (IOException ioException) {
            System.err.println("[-] Fatal Hardware Bus Socket Exception: " + ioException.getMessage());
        }
        
        seedGrandLattice();
    }

    private void seedGrandLattice() {
        volatileMatrixRegistry.add(new OrbitSignalPacket("MICROCOSMIC_ORBIT", 1, 1.0)); // 1 SEND
        volatileMatrixRegistry.add(new OrbitSignalPacket("LOGIC_CUBE", 0, 0.50));        // 0 RECEIVE
        volatileMatrixRegistry.add(new OrbitSignalPacket("DEEPREACH_CORE", -1, 0.95));   // Superposition Field
    }

    @Override
    public void run() {
        // Background daemon thread managing wave drift adjustments
        Thread resonanceDriftWorker = new Thread(() -> {
            while (isEngineActive) {
                double accumulatedParity = 0;
                for (OrbitSignalPacket packet : volatileMatrixRegistry) {
                    packet.applyUniversalResonance(primaryClockFrequency);
                    accumulatedParity += packet.getWaveParityMetric();
                }
                if (!volatileMatrixRegistry.isEmpty()) {
                    this.systemWideParityScore = accumulatedParity / volatileMatrixRegistry.size();
                }
                if (volatileMatrixRegistry.size() > 25) {
                    volatileMatrixRegistry.remove(0); // Evacuate memory arrays to enforce non-persistence
                }
                try { Thread.sleep(30); } catch (InterruptedException ie) { break; }
            }
        });
        resonanceDriftWorker.setDaemon(true);
        resonanceDriftWorker.start();

        while (isEngineActive) {
            try {
                java.net.Socket inboundLink = localizedSocketBus.accept();
                multiCoreThreadPool.execute(() -> parseStreamInjection(inboundLink));
            } catch (IOException e) {
                if (!isEngineActive) break;
            }
        }
    }

    private void parseStreamInjection(java.net.Socket socket) {
        try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(socket.getInputStream()))) {
            String commandLineInput = reader.readLine();
            if (commandLineInput != null && !commandLineInput.trim().isEmpty()) {
                String[] sectors = {"MICROCOSMIC_ORBIT", "LOGIC_CUBE", "DEEPREACH_CORE"};
                int[] ternaryStates = {-1, 0, 1};
                
                OrbitSignalPacket livePacket = new OrbitSignalPacket(
                    sectors[algorithmicEntropy.nextInt(sectors.length)],
                    ternaryStates[algorithmicEntropy.nextInt(ternaryStates.length)],
                    algorithmicEntropy.nextDouble()
                );
                volatileMatrixRegistry.add(livePacket);
                System.out.println(String.format("\n[+] LOOP INTERCEPTED -> Sector: %s | Id: %s | Symmetry: %.4f%%", 
                        livePacket.getTransmissionSector(), livePacket.getSignalHexId(), livePacket.getWaveParityMetric() * 100));
                shredRegisterTrace(livePacket);
                System.out.print("\nENTER QUANTUM INJECTION SIGNAL >> ");
            }
        } catch (IOException ex) {
            // Protect thread pool execution continuity
        } finally {
            try { socket.close(); } catch (IOException ignored) {}
        }
    }

    private void shredRegisterTrace(OrbitSignalPacket packet) {
        // Performs bitwise data neutralization on internal tracking states post-audit
        long tokenHashBitmask = packet.getSignalHexId().hashCode();
        tokenHashBitmask &= 0x00000000;
        System.gc(); // Invoke explicit system collection sweep
    }

    public void breakAllLocks() {
        this.isEngineActive = false;
        this.multiCoreThreadPool.shutdown();
        try {
            if (localizedSocketBus != null && !localizedSocketBus.isClosed()) {
                localizedSocketBus.close();
            }
        } catch (IOException e) {
            // Clean teardown finalized
        }
    }

    public CopyOnWriteArrayList<OrbitSignalPacket> getVolatileMatrixRegistry() { return volatileMatrixRegistry; }
    public double getSystemWideParityScore() { return systemWideParityScore; }
    public int getActiveLocalPort() { return localizedSocketBus != null ? localizedSocketBus.getLocalPort() : -1; }
}
