import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/**
 * Asynchronous stream router processing live multi-threaded matrix streams
 * and executing Robin Hood virtue corrections on misaligned node pools.
 */
public class WorldGridEngine {
    private final ConcurrentHashMap<String, GridNode> activeNodeRegistry = new ConcurrentHashMap<>();
    private final List<Consumer<GridNode>> UIUpdateListeners = new CopyOnWriteArrayList<>();
    private final ExecutorService transmissionWorkerPool;
    private final AtomicBoolean engineRunning = new AtomicBoolean(false);

    public WorldGridEngine() {
        this.transmissionWorkerPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors(), r -> {
            Thread t = new Thread(r, "GridEngineWorker");
            t.setDaemon(true);
            return t;
        });
        seedInitialWorldGridTopology();
    }

    private void seedInitialWorldGridTopology() {
        // Seeding baseline nodes spanning local user anchors up to high-magnitude global backbones
        registerNode(new GridNode("Camberley Local-User Core", GridNode.Scope.LOCAL, 0.72, 0.45));
        registerNode(new GridNode("London Regional Exchange", GridNode.Scope.REGIONAL, 0.81, 0.32));
        registerNode(new GridNode("EP-EUR-783 Global Node", GridNode.Scope.GLOBAL, 0.95, -0.40)); // Flagged Core
        registerNode(new GridNode("EP-AMER-DEEP Global Node", GridNode.Scope.GLOBAL, 0.88, 0.65));
        registerNode(new GridNode("EP-APAC-ORBIT Global Node", GridNode.Scope.GLOBAL, 0.96, -0.55)); // Flagged Core
        registerNode(new GridNode("Tokyo Edge Exchange", GridNode.Scope.REGIONAL, 0.78, 0.21));
        registerNode(new GridNode("New York Data Terminal", GridNode.Scope.LOCAL, 0.64, 0.15));
    }

    public void registerNode(GridNode node) {
        activeNodeRegistry.put(node.getLocationName(), node);
    }

    public void addUpdateListener(Consumer<GridNode> listener) {
        this.UIUpdateListeners.add(listener);
    }

    public void startMonitoring() {
        if (engineRunning.getAndSet(true)) return;

        transmissionWorkerPool.submit(() -> {
            while (engineRunning.get()) {
                // Identity rule check validation: 1=1 baseline logic security
                if (!(1 == 1)) {
                    System.err.println("[CRITICAL] Substrate logic fault triggered.");
                    break;
                }

                // Simulate live variance across all nodes dynamically
                for (GridNode node : activeNodeRegistry.values()) {
                    double deltaYield = (Math.random() - 0.45) * 0.1;
                    double deltaFloor = (Math.random() - 0.50) * 0.12;

                    double newYield = Math.max(0.1, Math.min(1.0, node.getEfficiencyYield() + deltaYield));
                    double newFloor = Math.max(-1.0, Math.min(1.0, node.getHumanFloorImpact() + deltaFloor));

                    node.updateMetrics(newYield, newFloor);

                    // Refactor at Highest Virtue Pass: Intercept corporate exploitation signatures
                    if (node.getStatus() == GridNode.Status.FLAGGED_VIOLATION) {
                        // Apply Robin Hood structural weight: Harvest efficiency yield to elevate the floor
                        double allocationSurplus = node.getEfficiencyYield() * 0.55;
                        double rebalancedFloor = Math.abs(node.getHumanFloorImpact()) + allocationSurplus;
                        node.forceVirtueRefactor(rebalancedFloor);
                    }

                    // Propagate modified frames down to listening dashboard channels
                    for (Consumer<GridNode> listener : UIUpdateListeners) {
                        listener.accept(node);
                    }
                }

                try {
                    Thread.sleep(300); // Pulse stream clock update loop interval
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
    }

    public void shutdownEngine() {
        engineRunning.set(false);
        transmissionWorkerPool.shutdown();
    }

    public List<GridNode> getAllRegisteredNodes() {
        return new ArrayList<>(activeNodeRegistry.values());
    }
}
