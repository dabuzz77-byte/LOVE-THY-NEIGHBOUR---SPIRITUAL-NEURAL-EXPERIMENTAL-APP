import neural.studio.*;
import java.net.http.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;

/** Bounded HTTP dispatcher with truthful results, cancellation, and immutable telemetry. */
public final class GridEngine implements AutoCloseable {
    public static final int MAX_ENDPOINTS = 24;
    public enum State {
        READY, QUEUED, SENDING, SUCCESS, HTTP_ERROR, FAILED, TIMED_OUT, CANCELLED;
        public boolean terminal() { return ordinal() >= SUCCESS.ordinal(); }
        public String label() { return name().replace('_', ' '); }
    }
    public record Result(Endpoint endpoint, State state, int code, double latencyMs, long time,
                         long batch, int requestBytes, String detail) {}
    public record Event(long time, String endpoint, State state, String detail) {}
    public record Sample(long time, double latencyMs, boolean success) {}
    public record Snapshot(long revision, long batch, boolean active, List<Result> nodes, List<Event> events,
                           List<Sample> history, long completed, long succeeded, long cancelled, long payloadBytes) {
        public Snapshot { nodes = List.copyOf(nodes); events = List.copyOf(events); history = List.copyOf(history); }
        public long sending() { return nodes.stream().filter(r -> r.state() == State.SENDING).count(); }
        public long queued() { return nodes.stream().filter(r -> r.state() == State.QUEUED).count(); }
        public double averageMs() { return history.stream().mapToDouble(Sample::latencyMs).average().orElse(0); }
    }
    private final Object lock = new Object();
    private final ThreadPoolExecutor workers = new ThreadPoolExecutor(4, 8, 30, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(MAX_ENDPOINTS), daemonFactory("resonance-request"), new ThreadPoolExecutor.AbortPolicy());
    private final ScheduledExecutorService deadlines = SharedScheduler.newSingleThreadScheduledExecutor(daemonFactory("resonance-deadlines"));
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(4))
            .followRedirects(HttpClient.Redirect.NEVER).version(HttpClient.Version.HTTP_2).build();
    private final Map<UUID, Result> nodes = new LinkedHashMap<>();
    private final Map<UUID, FutureTask<Void>> tasks = new HashMap<>();
    private final Map<UUID, Long> starts = new HashMap<>();
    private final Deque<Event> events = new ArrayDeque<>();
    private final Deque<Sample> history = new ArrayDeque<>();
    private final List<Consumer<Snapshot>> listeners = new CopyOnWriteArrayList<>();
    private long revision, batch, completed, succeeded, cancelled, payloadBytes;
    private boolean active, closed;
    public static ThreadFactory daemonFactory(String name) {
        return runnable -> { Thread thread = new Thread(runnable, name); thread.setDaemon(true); return thread; };
    }

    public void addListener(Consumer<Snapshot> listener) { listeners.add(Objects.requireNonNull(listener)); }
    public void configure(List<Endpoint> endpoints) {
        Snapshot changed;
        synchronized (lock) {
            ensureIdle();
            if (endpoints.size() > MAX_ENDPOINTS) throw new IllegalArgumentException("At most 24 endpoints can be configured.");
            Set<UUID> ids = new HashSet<>(); Set<String> urls = new HashSet<>();
            for (Endpoint endpoint : endpoints) {
                if (!ids.add(endpoint.id()) || !urls.add(endpoint.uri().normalize().toString()))
                    throw new IllegalArgumentException("Duplicate endpoints are not allowed.");
            }
            nodes.clear();
            for (Endpoint endpoint : endpoints) nodes.put(endpoint.id(), new Result(endpoint, State.READY, 0, 0, 0, batch, 0, "Ready to send"));
            changed = changed();
        }
        publish(changed);
    }

    public long dispatch(DispatchPayload payload, Duration timeout, int concurrency) {
        byte[] body = payload.bytes();
        if (timeout.compareTo(Duration.ofSeconds(1)) < 0 || timeout.compareTo(Duration.ofSeconds(60)) > 0)
            throw new IllegalArgumentException("Timeout must be between 1 and 60 seconds.");
        if (concurrency < 1 || concurrency > 8) throw new IllegalArgumentException("Concurrency must be 1–8.");
        Snapshot changed;
        long currentBatch;
        synchronized (lock) {
            ensureIdle();
            if (nodes.isEmpty()) throw new IllegalStateException("Add an endpoint or start the local test first.");
            workers.purge(); workers.setCorePoolSize(concurrency);
            active = true; currentBatch = ++batch; tasks.clear(); starts.clear();
            nodes.replaceAll((id, old) -> new Result(old.endpoint(), State.QUEUED, 0, 0, 0, currentBatch, body.length, "Waiting for a request slot"));
            addEvent("ENGINE", State.QUEUED, "Batch " + currentBatch + ": " + nodes.size() + " requests queued");
            for (Result result : nodes.values()) {
                Endpoint endpoint = result.endpoint();
                FutureTask<Void> task = new FutureTask<>(() -> { send(endpoint, currentBatch, body, timeout); return null; });
                tasks.put(endpoint.id(), task); workers.execute(task);
            }
            changed = changed();
        }
        publish(changed);
        return currentBatch;
    }

    private void send(Endpoint endpoint, long currentBatch, byte[] body, Duration timeout) {
        Snapshot changed;
        FutureTask<Void> requestTask;
        synchronized (lock) {
            Result existing = nodes.get(endpoint.id());
            if (closed || existing == null || existing.batch() != currentBatch || existing.state() != State.QUEUED) return;
            starts.put(endpoint.id(), System.nanoTime());
            requestTask = tasks.get(endpoint.id());
            nodes.put(endpoint.id(), new Result(endpoint, State.SENDING, 0, 0, System.currentTimeMillis(), currentBatch, body.length, "Awaiting HTTP response"));
            addEvent(endpoint.name(), State.SENDING, "POST request started");
            changed = changed();
        }
        publish(changed);
        ScheduledFuture<?> deadline = deadlines.schedule(() -> {
            finish(endpoint, currentBatch, State.TIMED_OUT, 0, "Request exceeded the " + timeout.toSeconds() + " second deadline");
            requestTask.cancel(true);
        }, timeout.toMillis(), TimeUnit.MILLISECONDS);
        try {
            HttpRequest request = HttpRequest.newBuilder(endpoint.uri()).timeout(timeout)
                    .header("Content-Type", "application/json; charset=utf-8")
                    .header("Accept", "application/json")
                    .header("User-Agent", "PlanetaryResonance/2.0")
                    .POST(HttpRequest.BodyPublishers.ofByteArray(body)).build();
            // Discard response bodies so remote responses cannot grow application memory.
            HttpResponse<Void> response = client.send(request, HttpResponse.BodyHandlers.discarding());
            int code = response.statusCode();
            State state = code >= 200 && code < 300 ? State.SUCCESS : State.HTTP_ERROR;
            finish(endpoint, currentBatch, state, code, "HTTP " + code + (state == State.SUCCESS ? " · response received" : " · endpoint did not accept the request"));
        } catch (HttpTimeoutException failure) {
            finish(endpoint, currentBatch, State.TIMED_OUT, 0, "No complete response within " + timeout.toSeconds() + " seconds");
        } catch (InterruptedException failure) {
            Thread.currentThread().interrupt(); finish(endpoint, currentBatch, State.CANCELLED, 0, "Request cancelled");
        } catch (Exception failure) {
            Throwable cause = failure;
            while (cause.getCause() != null && cause.getCause() != cause) cause = cause.getCause();
            String detail = cause.getClass().getSimpleName();
            if (cause.getMessage() != null && !cause.getMessage().isBlank()) detail += ": " + cause.getMessage();
            finish(endpoint, currentBatch, State.FAILED, 0, detail.substring(0, Math.min(240, detail.length())));
        } finally { deadline.cancel(false); }
    }

    private void finish(Endpoint endpoint, long currentBatch, State state, int code, String detail) {
        Snapshot changed;
        synchronized (lock) {
            Result old = nodes.get(endpoint.id());
            if (old == null || old.batch() != currentBatch || old.state().terminal()) return;
            double ms = starts.containsKey(endpoint.id()) ? (System.nanoTime() - starts.get(endpoint.id())) / 1_000_000.0 : 0;
            long now = System.currentTimeMillis();
            nodes.put(endpoint.id(), new Result(endpoint, state, code, ms, now, currentBatch, old.requestBytes(), detail));
            if (state == State.CANCELLED) cancelled++;
            else {
                completed++; if (state == State.SUCCESS) succeeded++;
                if (code > 0) payloadBytes += old.requestBytes();
                history.addLast(new Sample(now, ms, state == State.SUCCESS));
                while (history.size() > 120) history.removeFirst();
            }
            addEvent(endpoint.name(), state, detail);
            active = nodes.values().stream().anyMatch(r -> !r.state().terminal());
            if (!active) lock.notifyAll();
            changed = changed();
        }
        publish(changed);
    }

    public void cancel() {
        Snapshot changed;
        synchronized (lock) {
            if (!active) return;
            for (var entry : nodes.entrySet()) {
                Result old = entry.getValue();
                if (old.state().terminal()) continue;
                long now = System.currentTimeMillis();
                double ms = starts.containsKey(entry.getKey()) ? (System.nanoTime() - starts.get(entry.getKey())) / 1_000_000.0 : 0;
                entry.setValue(new Result(old.endpoint(), State.CANCELLED, 0, ms, now, old.batch(), old.requestBytes(), "Cancelled by operator; delivery may already have occurred"));
                cancelled++; addEvent(old.endpoint().name(), State.CANCELLED, "Cancelled by operator; remote work cannot be undone");
            }
            tasks.values().forEach(task -> task.cancel(true));
            workers.purge(); active = false; lock.notifyAll(); changed = changed();
        }
        publish(changed);
    }

    public Snapshot snapshot() { synchronized (lock) { return snapshotLocked(); } }
    private Snapshot changed() { revision++; return snapshotLocked(); }
    private Snapshot snapshotLocked() {
        return new Snapshot(revision, batch, active, new ArrayList<>(nodes.values()), new ArrayList<>(events),
                new ArrayList<>(history), completed, succeeded, cancelled, payloadBytes);
    }
    private void addEvent(String endpoint, State state, String detail) {
        events.addFirst(new Event(System.currentTimeMillis(), endpoint, state, detail));
        while (events.size() > 300) events.removeLast();
    }
    private void publish(Snapshot snapshot) { for (var listener : listeners) try { listener.accept(snapshot); } catch (RuntimeException ignored) {} }
    private void ensureIdle() { if (closed) throw new IllegalStateException("Engine is closed."); if (active) throw new IllegalStateException("Cancel or wait for the active batch first."); }
    public void clearHistory() {
        Snapshot changed;
        synchronized (lock) { ensureIdle(); history.clear(); events.clear(); completed = succeeded = cancelled = payloadBytes = 0; changed = changed(); }
        publish(changed);
    }
    public boolean awaitIdle(Duration timeout) throws InterruptedException {
        long deadline = System.nanoTime() + timeout.toNanos();
        synchronized (lock) {
            while (active) {
                long remaining = deadline - System.nanoTime();
                if (remaining <= 0) return false;
                TimeUnit.NANOSECONDS.timedWait(lock, remaining);
            }
            return true;
        }
    }
    @Override public void close() {
        synchronized (lock) { if (closed) return; closed = true; }
        cancel(); workers.shutdownNow(); deadlines.shutdownNow(); listeners.clear();
    }
}
