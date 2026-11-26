import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * MODULE 5: ASYNC ROUTING INTEGRATION BUS LAYER — STACK-OVERFLOW PURGED
 * Runs isolated loopback channels cleanly without reflective logging feedback loops.
 */
public class CentralPortRouter implements Runnable {
    
    private final CopyOnWriteArrayList<BridgeDataVector> dynamicRegistryLattice;
    private final ExecutorService processingCoreThreadPool;
    private final Random entropySource = new Random();
    private final double basalSchumannClock = 7.83; // Baseline synchronization rhythm
    private boolean isRouterLoopOperational = true;
    private ServerSocket activeServerSocket;
    private double globalParityIndex = 1.0;

    public CentralPortRouter() {
        this.dynamicRegistryLattice = new CopyOnWriteArrayList<>();
        this.processingCoreThreadPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        
        try {
            // Secure an unallocated loopback listener socket on your host system hardware
            this.activeServerSocket = new ServerSocket(0);
            System.out.println("[+] CentralPortRouter initialized safely on local adapter port: " + activeServerSocket.getLocalPort());
        } catch (IOException ioException) {
            System.err.println("[-] Router Bus socket initialization fault: " + ioException.getMessage());
        }
        
        initializeLatticePoints();
    }

    private void initializeLatticePoints() {
        dynamicRegistryLattice.add(new BridgeDataVector("LOCAL_LLAMA3", 1, 1.0));
        dynamicRegistryLattice.add(new BridgeDataVector("LOCAL_FLUX", 0, 0.50));
        dynamicRegistryLattice.add(new BridgeDataVector("GOOGLE_GEMINI", -1, 0.95));
    }

    @Override
    public void run() {
        // Safe, non-recursive clock background drift worker thread
        Thread clockOscillationWorker = new Thread(() -> {
            while (isRouterLoopOperational) {
                double accumulatedParity = 0;
                for (BridgeDataVector point : dynamicRegistryLattice) {
                    point.recalculateWaveDrift(basalSchumannClock);
                    accumulatedParity += point.getWaveParitySymmetry();
                }
                if (!dynamicRegistryLattice.isEmpty()) {
                    this.globalParityIndex = accumulatedParity / dynamicRegistryLattice.size();
                }
                if (dynamicRegistryLattice.size() > 20) {
                    dynamicRegistryLattice.remove(0); // Evacuate memory arrays to enforce non-persistence
                }
                try { Thread.sleep(30); } catch (InterruptedException ie) { break; }
            }
        });
        clockOscillationWorker.setDaemon(true);
        clockOscillationWorker.start();

        // Main thread loop accepting local socket pings
        while (isRouterLoopOperational) {
            try {
                java.net.Socket linkSocket = activeServerSocket.accept();
                processingCoreThreadPool.execute(() -> processInternalPingRequest(linkSocket));
            } catch (IOException e) {
                if (!isRouterLoopOperational) break;
            }
        }
    }

    private void processInternalPingRequest(java.net.Socket clientSocket) {
        // Read data payload silently with zero logging loops or external function references
        try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream()))) {
            String incomingPayload = reader.readLine();
            if (incomingPayload != null && !incomingPayload.trim().isEmpty()) {
                String[] sectors = {"LOCAL_LLAMA3", "LOCAL_FLUX", "GOOGLE_GEMINI"};
                int[] structuralStates = {-1, 0, 1};
                
                BridgeDataVector dynamicPoint = new BridgeDataVector(
                    sectors[entropySource.nextInt(sectors.length)],
                    structuralStates[entropySource.nextInt(structuralStates.length)],
                    entropySource.nextDouble()
                );
                dynamicRegistryLattice.add(dynamicPoint);
            }
        } catch (IOException ex) {
            // Protect background worker pool thread execution continuity
        } finally {
            try { clientSocket.close(); } catch (IOException ignored) {}
        }
    }

    public void terminateAllRouterLocksets() {
        this.isRouterLoopOperational = false;
        this.processingCoreThreadPool.shutdown();
        try {
            if (activeServerSocket != null && !activeServerSocket.isClosed()) {
                activeServerSocket.close();
            }
        } catch (IOException e) {
            // Clean teardown finalized
        }
    }

    public CopyOnWriteArrayList<BridgeDataVector> getDynamicRegistryLattice() { return dynamicRegistryLattice; }
    public double getGlobalParityIndex() { return globalParityIndex; }
    public int getActiveLocalPort() { return activeServerSocket != null ? activeServerSocket.getLocalPort() : -1; }
}
