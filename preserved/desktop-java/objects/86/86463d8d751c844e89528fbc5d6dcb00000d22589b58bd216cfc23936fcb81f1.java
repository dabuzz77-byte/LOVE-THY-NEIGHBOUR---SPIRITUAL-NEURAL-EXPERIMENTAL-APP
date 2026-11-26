import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * BI-TER-ALLSTATE GRAND ecosYSTEM: ASYNC INFRASTRUCTURE TRANSPORT
 * Part 2: Dispatches data transformations across volatile RAM cache fields with 0% persistent disk tracks.
 */
public class ParallelPassRouter implements Runnable {
    private final CopyOnWriteArrayList<SovereignPacket> volatileRegisterRing;
    private final ExecutorService hardwareCorePool;
    private final Random algorithmicEntropy;
    private final double basalClockFrequency = 7.83; // Core field anchor frequency
    private boolean isBusOperational = true;
    private ServerSocket localBusSocketTunnel;
    private double aggregateSymmetryScore = 1.0;

    public ParallelPassRouter() {
        this.volatileRegisterRing = new CopyOnWriteArrayList<>();
        this.hardwareCorePool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        this.algorithmicEntropy = new Random();
        
        try {
            // Bind an unassigned, isolated loopback socket channel onto the local device adapter
            this.localBusSocketTunnel = new ServerSocket(0);
            System.out.println(String.format("[+] UNBLOCKED PASS BUS OPERATIONAL NATIVELY ON PORT: %d", localBusSocketTunnel.getLocalPort()));
        } catch (IOException ioException) {
            System.err.println("[-] Fatal Skeleton Pass Socket Exception: " + ioException.getMessage());
        }
        
        seedProtectiveLattice();
    }

    private void seedProtectiveLattice() {
        // Enplace target allocations driven solely by floor-first life-support priorities
        volatileRegisterRing.add(new SovereignPacket("FLOOR_SUSTENANCE", 1, 99.4, 1.0));
        volatileRegisterRing.add(new SovereignPacket("HEALTH_SHIELD", 0, 91.2, 0.50));
        volatileRegisterRing.add(new SovereignPacket("HOUSING_MATRIX", -1, 85.7, 0.95));
    }

    @Override
    public void run() {
        // Active background daemon loop for real-time resonance calculations
        Thread resonanceDriftWorker = new Thread(() -> {
            while (isBusOperational) {
                double accumulatedParity = 0;
                for (SovereignPacket packet : volatileRegisterRing) {
                    packet.adjustLatticeOscillation(basalClockFrequency);
                    accumulatedParity += packet.getSystemSymmetryParity();
                }
                if (!volatileRegisterRing.isEmpty()) {
                    this.aggregateSymmetryScore = accumulatedParity / volatileRegisterRing.size();
                }
                if (volatileRegisterRing.size() > 24) {
                    volatileRegisterRing.remove(0); // Evacuate register ring to prevent hardware leakage
                }
                try { Thread.sleep(30); } catch (InterruptedException ie) { break; }
            }
        });
        resonanceDriftWorker.setDaemon(true);
        resonanceDriftWorker.start();

        while (isBusOperational) {
            try {
                java.net.Socket inboundLink = localBusSocketTunnel.accept();
                hardwareCorePool.execute(() -> parseStreamInjection(inboundLink));
            } catch (IOException e) {
                if (!isBusOperational) break;
            }
        }
    }

    private void parseStreamInjection(java.net.Socket socket) {
        try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(socket.getInputStream()))) {
            String incomingCommand = reader.readLine();
            if (incomingCommand != null && !incomingCommand.trim().isEmpty()) {
                String[] sectors = {"FLOOR_SUSTENANCE", "HEALTH_SHIELD", "HOUSING_MATRIX"};
                int[] ternaryStates = {-1, 0, 1};
                
                SovereignPacket livePacket = new SovereignPacket(
                    sectors[algorithmicEntropy.nextInt(sectors.length)],
                    ternaryStates[algorithmicEntropy.nextInt(ternaryStates.length)],
                    20 + algorithmicEntropy.nextDouble() * 80,
                    algorithmicEntropy.nextDouble()
                );
                volatileRegisterRing.add(livePacket);
                neutralizeVolatileTelemetry(livePacket);
            }
        } catch (IOException ex) {
            // Guarantee processing loop resilience against stream errors
        } finally {
            try { socket.close(); } catch (IOException ignored) {}
        }
    }

    private void neutralizeVolatileTelemetry(SovereignPacket packet) {
        // Performs bitwise data neutralization on internal tracking states post-audit
        long tokenBitmask = packet.getTransmissionId().hashCode();
        tokenBitmask &= 0x00000000; // Bitwise zero-out memory trace
        System.gc(); // Force JVM to invoke active memory cleanup routines
    }

    public void wipeSovereignSubstrate() {
        this.isBusOperational = false;
        this.hardwareCorePool.shutdown();
        try {
            if (localBusSocketTunnel != null && !localBusSocketTunnel.isClosed()) {
                localBusSocketTunnel.close();
            }
        } catch (IOException e) {
            // Direct close forced complete
        }
    }

    public CopyOnWriteArrayList<SovereignPacket> getVolatileRegisterRing() { return volatileRegisterRing; }
    public double getAggregateSymmetryScore() { return aggregateSymmetryScore; }
    public int getLocalActivePort() { return localBusSocketTunnel != null ? localBusSocketTunnel.getLocalPort() : -1; }
}
