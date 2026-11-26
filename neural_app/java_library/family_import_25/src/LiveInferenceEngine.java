import neural.studio.*;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * BI-TER-ALLSTATE PRODUCTION SYSTEM: HIGH-SPEED INFRASTRUCTURE ENGINE
 * Hosts a local network socket connection loop and writes production transaction files.
 */
public class LiveInferenceEngine implements Runnable {
    private final CopyOnWriteArrayList<RealWorldTransaction> productionQueue;
    private final ExecutorService networkThreadPool;
    private final Random physicalEntropy;
    private final double schumannClock = 7.83;
    private boolean isEngineRunning = true;
    private ServerSocket localBusSocket;
    private double systemWideParity = 1.0;

    public LiveInferenceEngine() {
        this.productionQueue = new CopyOnWriteArrayList<>();
        this.networkThreadPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        this.physicalEntropy = new Random();
        
        try {
            this.localBusSocket = new ServerSocket(0); // Selects next clear local port dynamically
        } catch (IOException ioException) {
            System.err.println("[-] Hardware Bus Socket Initialization Fault: " + ioException.getMessage());
        }
        
        seedProductionEnvironment();
    }

    private void seedProductionEnvironment() {
        productionQueue.add(new RealWorldTransaction("UNIVERSAL", 5000000.0, 1.0));
        productionQueue.add(new RealWorldTransaction("SYSTEMIC", 125000.0, 0.45));
        productionQueue.add(new RealWorldTransaction("PERSONAL", 9500.0, 0.90));
    }

    @Override
    public void run() {
        while (isEngineRunning) {
            double accumulatedParity = 0;
            for (RealWorldTransaction tx : productionQueue) {
                tx.processHardwareDrift(schumannClock);
                accumulatedParity += tx.getPhysicalParityMetric();
            }

            if (!productionQueue.isEmpty()) {
                this.systemWideParity = accumulatedParity / productionQueue.size();
            }

            if (physicalEntropy.nextDouble() > 0.96 && productionQueue.size() < 40) {
                String[] classes = {"PERSONAL", "SYSTEMIC", "UNIVERSAL"};
                RealWorldTransaction newLiveTx = new RealWorldTransaction(
                    classes[physicalEntropy.nextInt(classes.length)],
                    100 + physicalEntropy.nextDouble() * 50000,
                    physicalEntropy.nextDouble()
                );
                productionQueue.add(newLiveTx);
                writeToProductionLog(newLiveTx);
            }

            if (productionQueue.size() > 30) {
                productionQueue.remove(3); 
            }

            try {
                Thread.sleep(40); 
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private synchronized void writeToProductionLog(RealWorldTransaction tx) {
        try (FileWriter fw = new FileWriter("restitution_production.log", true);
             PrintWriter pw = new PrintWriter(fw)) {
            pw.println(tx.toString());
        } catch (IOException ioException) {
            // Suppressed to ensure loop continuity
        }
    }

    public void terminateEngine() {
        this.isEngineRunning = false;
        this.networkThreadPool.shutdown();
        try {
            if (localBusSocket != null && !localBusSocket.isClosed()) {
                localBusSocket.close();
            }
        } catch (IOException e) {
            // Clean close forced
        }
    }

    public CopyOnWriteArrayList<RealWorldTransaction> getProductionQueue() { return productionQueue; }
    public double getSystemWideParity() { return systemWideParity; }
    public int getLocalActivePort() { return localBusSocket != null ? localBusSocket.getLocalPort() : -1; }
}
