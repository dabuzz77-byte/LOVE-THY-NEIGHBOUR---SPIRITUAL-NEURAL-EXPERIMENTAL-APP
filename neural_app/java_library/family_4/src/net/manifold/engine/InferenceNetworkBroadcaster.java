package net.manifold.engine;
import neural.studio.*;


import net.manifold.core.InferenceQuantum;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

/** Bounded local tensor processor. Network observation is handled separately by NetworkMonitor. */
public final class InferenceNetworkBroadcaster implements AutoCloseable {
    private static final int MAX_RETAINED = 2048;
    private static final long RETENTION_NANOS = TimeUnit.SECONDS.toNanos(30);
    private record Entry(CompletableFuture<InferenceQuantum> result, long admittedAt) {}
    private final Map<UUID, Entry> messages = new LinkedHashMap<>();
    private final ThreadPoolExecutor workers;
    private final ScheduledExecutorService maintenance;
    private final LongAdder processed = new LongAdder(), rejected = new LongAdder();
    private boolean closed;

    public InferenceNetworkBroadcaster() {
        int count = Math.max(1, Math.min(4, Runtime.getRuntime().availableProcessors() - 1));
        workers = new ThreadPoolExecutor(count, count, 0, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(256), daemonFactory("manifold-compute"), new ThreadPoolExecutor.AbortPolicy());
        maintenance = SharedScheduler.newSingleThreadScheduledExecutor(daemonFactory("manifold-retention"));
        maintenance.scheduleWithFixedDelay(this::expire, 1, 1, TimeUnit.SECONDS);
    }

    public static ThreadFactory daemonFactory(String name) {
        return task -> { Thread t = new Thread(task, name); t.setDaemon(true); return t; };
    }

    public synchronized CompletableFuture<InferenceQuantum> submit(InferenceQuantum message) {
        Objects.requireNonNull(message, "message");
        if (closed) return CompletableFuture.failedFuture(new IllegalStateException("Engine is closed"));
        Entry existing = messages.get(message.quantumId());
        if (existing != null) return existing.result();
        expire();
        if (messages.size() >= MAX_RETAINED) {
            Iterator<Entry> entries = messages.values().iterator();
            while (entries.hasNext()) {
                if (entries.next().result().isDone()) { entries.remove(); break; }
            }
        }
        if (messages.size() >= MAX_RETAINED) return reject("Retention capacity reached");
        CompletableFuture<InferenceQuantum> result = new CompletableFuture<>();
        messages.put(message.quantumId(), new Entry(result, System.nanoTime()));
        try {
            workers.execute(() -> {
                try {
                    float[] data = message.tensorPayload();
                    for (int i = 0; i < data.length; i++) data[i] = (float) (message.stateVector() == 0x101010
                            ? Math.tanh(data[i]) : Math.atan(data[i]));
                    InferenceQuantum transformed = new InferenceQuantum(message.quantumId(), message.originNodeId(),
                            message.stateVector(), data, message.orbitCount(), message.virtueScore(), message.creationTimestamp());
                    processed.increment();
                    result.complete(transformed);
                } catch (RuntimeException failure) { result.completeExceptionally(failure); }
            });
        } catch (RejectedExecutionException failure) {
            messages.remove(message.quantumId());
            rejected.increment();
            result.completeExceptionally(failure);
        }
        return result;
    }

    private CompletableFuture<InferenceQuantum> reject(String message) {
        rejected.increment();
        return CompletableFuture.failedFuture(new RejectedExecutionException(message));
    }

    public void broadcastQuantum(InferenceQuantum quantum) { submit(quantum); }
    private synchronized void expire() {
        long now = System.nanoTime();
        messages.values().removeIf(entry -> entry.result().isDone() && now - entry.admittedAt() > RETENTION_NANOS);
    }
    public synchronized int getActiveStreamCount() { return messages.size(); }
    public long getProcessedCount() { return processed.sum(); }
    public long getRejectedCount() { return rejected.sum(); }
    public int getQueueDepth() { return workers.getQueue().size(); }

    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        maintenance.shutdownNow();
        workers.shutdownNow();
        messages.values().forEach(entry -> entry.result().completeExceptionally(new CancellationException("Engine closed")));
        messages.clear();
    }
}
