import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Generates an immutable 7.83 Hz clock pulse (127,710 microseconds per cycle).
 * Prevents drift accumulation via absolute baseline scheduling.
 */
public class CarrierWaveClock {
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor(runnable -> {
        Thread t = new Thread(runnable, "MasterCarrierWaveClock");
        t.setPriority(Thread.MAX_PRIORITY); // Elevate to prevent schedule drops
        return t;
    });
    
    private final ExecutionBridgeEngine engine;
    private final AtomicBoolean isRunning = new AtomicBoolean(false);
    private static final long CYCLE_PERIOD_MICROS = 127710;

    public CarrierWaveClock(ExecutionBridgeEngine engine) {
        this.engine = engine;
    }

    public void startSyncLoop() {
        if (isRunning.compareAndSet(false, true)) {
            scheduler.scheduleAtFixedRate(
                () -> {
                    try {
                        engine.executeSynchronizedCycle();
                    } catch (Exception e) {
                        System.err.println("[CLOCK EXCEPTION] Parity tick failure: " + e.getMessage());
                    }
                },
                0,
                CYCLE_PERIOD_MICROS,
                TimeUnit.MICROSECONDS
            );
        }
    }

    public void stopSyncLoop() {
        if (isRunning.compareAndSet(true, false)) {
            scheduler.shutdown();
        }
    }
}
