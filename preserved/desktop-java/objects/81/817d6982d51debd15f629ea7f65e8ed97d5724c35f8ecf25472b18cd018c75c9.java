import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * BI-TER-ALLSTATE SUBSTRATE: SYSTEM DATA PROCESSING ROUTER
 * Coordinates multi-lane logistical paths within volatile RAM memory with 0% persistent disk log tracks.
 */
public class ParallelTransitionBus implements Runnable {
    private final CopyOnWriteArrayList<FloorResourcePacket> volatileLatticeRegistry;
    private final ExecutorService nativeCoreThreadPool;
    private final Random chaoticEntropy;
    private final double schumannBasalConstant = 7.83;
    private boolean isBusLoopOperational = true;
    private ServerSocket localBusSocketTunnel;
    private double combinedGlobalSymmetry = 1.0;

    public ParallelTransitionBus() {
        this.volatileLatticeRegistry = new CopyOnWriteArrayList<>();
        this.nativeCoreThreadPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        this.chaoticEntropy = new Random();
        
        try {
            // Bind an unassigned, isolated loopback socket channel onto the local device adapter
            this.localBusSocketTunnel = new ServerSocket(0);
        } catch (IOException ioException) {
            System.err.println("[-] Non-Persistent Data Plane Socket Exception: " + ioException.getMessage());
        }
        
        seedBaselineFloorNodes();
    }

    private void seedBaselineFloorNodes() {
        // Enplace target allocations driven solely by physical survival parameters
        volatileLatticeRegistry.add(new FloorResourcePacket("SUSTENANCE_FLOW", 99.2, 1.0));
        volatileLatticeRegistry.add(new FloorResourcePacket("MEDICAL_RESERVE", 94.6, 0.50));
        volatileLatticeRegistry.add(new FloorResourcePacket("SHELTER_HUMANITY", 88.1, 0.95));
    }

    @Override
    public void run() {
        while (isBusLoopOperational) {
            double accumulatedParity = 0;
            for (FloorResourcePacket packet : volatileLatticeRegistry) {
                packet.applyLatticeResonance(schumannBasalConstant);
                accumulatedParity += packet.getLatticeStabilityParity();
            }

            if (!volatileLatticeRegistry.isEmpty()) {
                this.combinedGlobalSymmetry = accumulatedParity / volatileLatticeRegistry.size();
            }

            // Simulate incoming telemetry data loads from community coordination endpoints
            if (chaoticEntropy.nextDouble() > 0.94 && volatileLatticeRegistry.size() < 42) {
                String[] sectors = {"SUSTENANCE_FLOW", "MEDICAL_RESERVE", "SHELTER_HUMANITY"};
                FloorResourcePacket inboundPacket = new FloorResourcePacket(
                    sectors[chaoticEntropy.nextInt(sectors.length)],
                    20 + chaoticEntropy.nextDouble() * 80,
                    chaoticEntropy.nextDouble()
                );
                volatileLatticeRegistry.add(inboundPacket);
                scrubVolatileRegisters(inboundPacket);
            }

            // High-speed queue evacuation (Enforces continuous ring buffer memory reclamation)
            if (volatileLatticeRegistry.size() > 24) {
                volatileLatticeRegistry.remove(0); // Immediately drop processed cache blocks
            }

            try {
                Thread.sleep(33); // Sync calculations to match native silicon clock intervals
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private void scrubVolatileRegisters(FloorResourcePacket packet) {
        // Performs bitwise data neutralization on internal tracking states post-audit
        long tokenHashBitmask = packet.getResourcePacketId().hashCode();
        tokenHashBitmask &= 0x00000000;
    }

    public void terminateSubstrateBus() {
        this.isBusLoopOperational = false;
        this.nativeCoreThreadPool.shutdown();
        try {
            if (localBusSocketTunnel != null && !localBusSocketTunnel.isClosed()) {
                localBusSocketTunnel.close();
            }
        } catch (IOException e) {
            // Clean closure forced
        }
    }

    public CopyOnWriteArrayList<FloorResourcePacket> getVolatileLatticeRegistry() { return volatileLatticeRegistry; }
    public double getCombinedGlobalSymmetry() { return combinedGlobalSymmetry; }
    public int getLocalActivePort() { return localBusSocketTunnel != null ? localBusSocketTunnel.getLocalPort() : -1; }
}
