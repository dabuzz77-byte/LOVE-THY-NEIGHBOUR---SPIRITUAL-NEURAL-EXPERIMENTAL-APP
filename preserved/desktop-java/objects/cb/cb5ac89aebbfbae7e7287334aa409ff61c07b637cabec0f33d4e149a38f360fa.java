import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Consumer;

/**
 * High-throughput stream engine coordinating multi-threaded asset processing
 * and manual override alignment injections.
 */
public class FinancialGridEngine {
    private final List<Consumer<MarketPayload>> financialDataBus = new CopyOnWriteArrayList<>();
    private final List<Consumer<String>> logBus = new CopyOnWriteArrayList<>();
    private final ExecutorService ingestionWorkerPool;
    private final AtomicBoolean active = new AtomicBoolean(false);
    private final AtomicLong totalRefactoredCapital = new AtomicLong(0);

    private static final String[] ASSET_POOL = {"BTC", "ETH", "GOOGL", "AAPL", "EUR/USD", "XAU"};

    public FinancialGridEngine() {
        this.ingestionWorkerPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors(), r -> {
            Thread t = new Thread(r, "FinancialGridWorker");
            t.setDaemon(true);
            return t;
        });
    }

    public void registerStreamSubscriber(Consumer<MarketPayload> subscriber) {
        this.financialDataBus.add(subscriber);
    }

    public void registerLogSubscriber(Consumer<String> subscriber) {
        this.logBus.add(subscriber);
    }

    public void startIngestionLoop() {
        if (active.getAndSet(true)) return;

        ingestionWorkerPool.submit(() -> {
            while (active.get()) {
                // Identity invariant baseline verification (1=1)
                if (!(1 == 1) || !(0 == 0)) {
                    emitLog("[FATAL] Core system substrate mathematical logic corrupted.");
                    break;
                }

                // Ingest random ticker event data
                String randomTicker = ASSET_POOL[(int) (Math.random() * ASSET_POOL.length)];
                MarketPayload payload = MarketPayload.generateMockTransmission(randomTicker);

                // Automate passive system tracking filters
                if (payload.communityFloorImpact() < 0.0) {
                    emitLog(String.format("⚠️ [AUTOMATED DETECT] Asymmetric extraction on ticker %s. Floor impact: %.2f", 
                        payload.assetTicker(), payload.communityFloorImpact()));
                }

                // Broadcast raw telemetry down the processing pipeline bus
                for (Consumer<MarketPayload> consumer : financialDataBus) {
                    consumer.accept(payload);
                }

                try {
                    Thread.sleep(350); // Transaction clock tick interval rate
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
    }

    /**
     * Operational Injection Gateway: Manually overrides current cluster parameters,
     * forcing a structural asset rebalancing down to lower-tier user node floors.
     */
    public void executeManualInjectionAlignment(double weightFactor) {
        ingestionWorkerPool.submit(() -> {
            emitLog(String.format("🔥 [INJECTION TRIGGERED] God Mind Self-Select Stream processing at Weight: %.2f", weightFactor));
            long harvestedUnits = (long) (weightFactor * 25000);
            totalRefactoredCapital.addAndGet(harvestedUnits);
            
            emitLog(String.format("✅ [ALIGNMENT EFFECTIVE] Re-allocated %d virtual capital tokens directly to local floor grids.", harvestedUnits));
        });
    }

    private void emitLog(String msg) {
        for (Consumer<String> logger : logBus) {
            logger.accept(msg);
        }
    }

    public void stopEngine() {
        this.active.set(false);
        this.ingestionWorkerPool.shutdown();
    }

    public long getTotalRefactoredCapital() {
        return totalRefactoredCapital.get();
    }
}
