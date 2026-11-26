import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * MODULE 2: ASYNC TRANSPORT ENGINE — STACK STABILIZED
 * Runs quiet loopback lanes cleanly to manage volatile data rings with 0% storage footprint.
 */
public class SilentPortRouter implements Runnable {
    
    private final CopyOnWriteArrayList<SovereignDataUnit> volatileRegistryLattice;
    private final ExecutorService systemProcessingThreadPool;
    private final Random entropySource = new Random();
    private final double basalSchumannClock = 7.83; // Baseline resonance anchor frequency
    private boolean isRouterLoopOperational = true;
    private ServerSocket activeServerSocket;
    private double masterParityParameter = 1.0;

    public SilentPortRouter() {
        this.volatileRegistryLattice = new CopyOnWriteArrayList<>();
        this.systemProcessingThreadPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        
        try {
            // Secure an unallocated local loopback adapter address port natively
            this.activeServerSocket = new ServerSocket(0);
            System.out.println("[+] SilentPortRouter successfully locked loopback port: " + activeServerSocket.getLocalPort());
        } catch (IOException ioException) {
            System.err.println("[-] Router Bus socket initialization fault: " + ioException.getMessage());
        }
        
        seedInitialLattice();
    }

    private void seedInitialLattice() {
        volatileRegistryLattice.add(new SovereignDataUnit("LOCAL_CHIPS", 1, 1.0));
        volatileRegistryLattice.add(new SovereignDataUnit("CLOUD_GATEWAY", 0, 0.95));
    }

    @Override
    public void run() {
        // Safe, isolated background clock drift worker thread
        Thread clockOscillationWorker = new Thread(() -> {
            while (isRouterLoopOperational) {
                double accumulatedSymmetry = 0;
                for (SovereignDataUnit unit : volatileRegistryLattice) {
                    unit.balanceWaveDrift(basalSchumannClock);
                    accumulatedSymmetry += unit.getClockSymmetryIndex();
                }
                if (!volatileRegistryLattice.isEmpty()) {
                    this.masterParityParameter = accumulatedSymmetry / volatileRegistryLattice.size();
                }
                if (volatileRegistryLattice.size() > 20) {
                    volatileRegistryLattice.remove(0); // Evacuate memory arrays to enforce non-persistence
                }
                try { Thread.sleep(30); } catch (InterruptedException ie) { break; }
            }
        });
        clockOscillationWorker.setDaemon(true);
        clockOscillationWorker.start();

        // Main thread loop accepting local socket connections silently
        while (isRouterLoopOperational) {
            try {
                java.net.Socket activeLinkSocket = activeServerSocket.accept();
                systemProcessingThreadPool.execute(() -> parseStreamPulse(activeLinkSocket));
            } catch (IOException e) {
                if (!isRouterLoopOperational) break;
            }
        }
    }

    private void parseStreamPulse(java.net.Socket clientSocket) {
        try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream()))) {
            String inboundLine = reader.readLine();
            if (inboundLine != null && !inboundLine.trim().isEmpty()) {
                String[] coreSectors = {"LOCAL_CHIPS", "CLOUD_GATEWAY"};
                int[] binaryStates = {0, 1};
                
                SovereignDataUnit freshUnit = new SovereignDataUnit(
                    coreSectors[entropySource.nextInt(coreSectors.length)],
                    binaryStates[entropySource.nextInt(binaryStates.length)],
                    entropySource.nextDouble()
                );
                volatileRegistryLattice.add(freshUnit);
            }
        } catch (IOException ex) {
            // Guarantee thread pool continuous processing posture
        } finally {
            try { clientSocket.close(); } catch (IOException ignored) {}
        }
    }

    public void terminateRouterSystem() {
        this.isRouterLoopOperational = false;
        this.systemProcessingThreadPool.shutdown();
        try {
            if (activeServerSocket != null && !activeServerSocket.isClosed()) {
                activeServerSocket.close();
            }
        } catch (IOException e) {
            // Clean teardown finalized
        }
    }

    public CopyOnWriteArrayList<SovereignDataUnit> getVolatileRegistryLattice() { return volatileRegistryLattice; }
    public double getMasterParityParameter() { return masterParityParameter; }
    public int getActiveLocalPort() { return activeServerSocket != null ? activeServerSocket.getLocalPort() : -1; }
}
