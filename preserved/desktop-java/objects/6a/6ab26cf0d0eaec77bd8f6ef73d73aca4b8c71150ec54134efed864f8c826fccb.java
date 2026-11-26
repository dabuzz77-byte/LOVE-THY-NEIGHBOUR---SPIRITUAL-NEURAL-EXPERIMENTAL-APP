import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList; // Corrected high-performance concurrent import

/**
 * Thread-safe, non-blocking telemetry distribution registry.
 * Eliminates garbage collector strain via structural reference streaming.
 */
public class CoreEventBus {
    
    public interface TelemetrySubscriber {
        void handleSystemFrame(long cycle, double[][] q, int[][] t, byte[][] b, Map<String, Double> perfMetrics);
    }

    private final List<TelemetrySubscriber> subscribers = new CopyOnWriteArrayList<>();

    public void subscribe(TelemetrySubscriber subscriber) {
        subscribers.add(subscriber);
    }

    public void broadcast(long cycle, double[][] q, int[][] t, byte[][] b, Map<String, Double> metrics) {
        for (TelemetrySubscriber sub : subscribers) {
            sub.handleSystemFrame(cycle, q, t, b, metrics);
        }
    }
}
