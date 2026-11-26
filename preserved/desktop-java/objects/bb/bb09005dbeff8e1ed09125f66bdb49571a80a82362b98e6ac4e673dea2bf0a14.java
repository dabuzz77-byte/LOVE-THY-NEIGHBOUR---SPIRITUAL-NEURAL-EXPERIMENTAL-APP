import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.Random;

/**
 * UNIFIED HARMONIC PROTOCOL: ISOLATED SOCKET LISTENER SERVER
 * Processes user command frames natively within independent local memory structures.
 */
public class LocalSilentRouter implements Runnable {
    private final CopyOnWriteArrayList<VolatileUnit> registry = new CopyOnWriteArrayList<>();
    private final ExecutorService threads = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
    private final Random entropySource = new Random();
    private final double basalSchumannClock = 7.83;
    private ServerSocket socket;
    private boolean active = true;
    private double overallParity = 1.0;

    public LocalSilentRouter() {
        try {
            this.socket = new ServerSocket(0);
            registry.add(new VolatileUnit("LOCAL_CHIPS", 1, 1.0));
            registry.add(new VolatileUnit("CLOUD_GATEWAY", 0, 0.95));
        } catch (IOException ignored) {}
    }

    @Override
    public void run() {
        Thread clockWorker = new Thread(() -> {
            while (active) {
                double total = 0;
                for (VolatileUnit u : registry) {
                    u.tick(basalSchumannClock);
                    total += u.getDrift();
                }
                if (!registry.isEmpty()) this.overallParity = total / registry.size();
                if (registry.size() > 20) registry.remove(0); 
                try { Thread.sleep(30); } catch (InterruptedException ie) { break; }
            }
        });
        clockWorker.setDaemon(true);
        clockWorker.start();

        while (active) {
            try {
                java.net.Socket s = socket.accept();
                threads.execute(() -> {
                    try (java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(s.getInputStream()))) {
                        r.readLine();
                        String[] sectors = {"LOCAL_CHIPS", "CLOUD_GATEWAY"};
                        registry.add(new VolatileUnit(sectors[entropySource.nextInt(2)], entropySource.nextInt(2), entropySource.nextDouble()));
                    } catch (IOException ignored) {} finally { try { s.close(); } catch (IOException ignored) {} }
                });
            } catch (IOException e) { if (!active) break; }
        }
    }

    public void terminateRouterSystem() {
        this.active = false;
        this.threads.shutdown();
        try { if (socket != null && !socket.isClosed()) socket.close(); } catch (IOException ignored) {}
    }

    public CopyOnWriteArrayList<VolatileUnit> getRegistry() { return registry; }
    public double getOverallParity() { return overallParity; }
    public int getActiveLocalPort() { return socket != null ? socket.getLocalPort() : -1; }
}
