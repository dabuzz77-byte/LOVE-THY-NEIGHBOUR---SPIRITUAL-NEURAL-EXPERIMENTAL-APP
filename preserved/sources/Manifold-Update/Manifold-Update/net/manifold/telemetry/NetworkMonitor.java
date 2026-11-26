package net.manifold.telemetry;

import net.manifold.core.InferenceQuantum;
import net.manifold.engine.InferenceNetworkBroadcaster;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;

/** Keeps immutable UI snapshots and computes rates from counter differences and actual elapsed time. */
public final class NetworkMonitor implements AutoCloseable {
    private final WindowsNetworkCollector collector;
    private final InferenceNetworkBroadcaster engine;
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor(
            InferenceNetworkBroadcaster.daemonFactory("network-monitor"));
    private final List<Consumer<NetworkSnapshot>> listeners = new CopyOnWriteArrayList<>();
    private volatile NetworkSnapshot snapshot = NetworkSnapshot.waiting();
    private final Map<String, WindowsNetworkCollector.Counter> previous = new HashMap<>();
    private Map<String, NetworkSnapshot.Connection> previousConnections = new HashMap<>();
    private final Deque<NetworkSnapshot.Event> events = new ArrayDeque<>();
    private long previousNanos;
    private boolean tcpBaseline;
    private volatile boolean closed;

    public NetworkMonitor(InferenceNetworkBroadcaster engine) throws java.io.IOException {
        this.engine = engine;
        collector = new WindowsNetworkCollector();
    }
    public void start() { scheduler.scheduleWithFixedDelay(this::sample, 0, 2, TimeUnit.SECONDS); }
    public NetworkSnapshot snapshot() { return snapshot; }
    public void addListener(Consumer<NetworkSnapshot> listener) { listeners.add(listener); }

    private void sample() {
        try {
            WindowsNetworkCollector.Reading reading = collector.collect();
            if (closed) return;
            long now = System.currentTimeMillis(), nano = System.nanoTime();
            List<NetworkSnapshot.Adapter> adapters = calculateRates(reading.counters(), previous, nano - previousNanos,
                    previousNanos != 0);
            previous.clear();
            reading.counters().forEach(counter -> previous.put(counter.id(), counter));
            previousNanos = nano;
            Map<String, NetworkSnapshot.Connection> current = new LinkedHashMap<>();
            reading.connections().forEach(connection -> current.put(connection.key(), connection));
            if (reading.tcpAvailable()) {
                if (tcpBaseline) {
                    for (var connection : current.values()) {
                        var old = previousConnections.get(connection.key());
                        if (old == null) addEvent(now, "OPEN", connection.process() + "  " + connection.remote());
                        else if (!old.state().equals(connection.state()))
                            addEvent(now, "STATE", connection.process() + "  " + connection.remote() + "  " + connection.state());
                    }
                    for (var connection : previousConnections.values()) if (!current.containsKey(connection.key()))
                        addEvent(now, "CLOSED", connection.process() + "  " + connection.remote());
                } else addEvent(now, "READY", "First TCP snapshot: " + current.size() + " observed connections");
                previousConnections = current;
                tcpBaseline = true;
            } else tcpBaseline = false;
            snapshot = new NetworkSnapshot(now, snapshot.sequence() + 1, adapters, new ArrayList<>(current.values()),
                    new ArrayList<>(events), reading.tcpAvailable(), reading.warning(), "");
            // Condition a vector of observed measurements; no synthetic traffic or model inference is claimed.
            double receive = adapters.stream().mapToDouble(NetworkSnapshot.Adapter::receiveRate).max().orElse(0);
            double send = adapters.stream().mapToDouble(NetworkSnapshot.Adapter::sendRate).max().orElse(0);
            engine.submit(new InferenceQuantum(UUID.randomUUID(), "LOCAL_NETWORK_OBSERVATION", 0x101010,
                    new float[]{(float) Math.log1p(receive), (float) Math.log1p(send),
                            (float) Math.log1p(snapshot.establishedCount()), (float) Math.log1p(snapshot.processCount())},
                    0, 1.0, now));
        } catch (Exception failure) {
            if (closed) return;
            // Discard rate baselines so reconnects cannot produce a false throughput spike.
            previous.clear(); previousNanos = 0; tcpBaseline = false;
            NetworkSnapshot old = snapshot;
            snapshot = new NetworkSnapshot(old.capturedAt(), old.sequence(), old.adapters(), old.connections(), old.events(),
                    old.tcpAvailable(), old.warning(), failure.getMessage() == null ? failure.getClass().getSimpleName() : failure.getMessage());
        }
        for (var listener : listeners) try { listener.accept(snapshot); } catch (RuntimeException ignored) {}
    }

    public static List<NetworkSnapshot.Adapter> calculateRates(List<WindowsNetworkCollector.Counter> current,
            Map<String, WindowsNetworkCollector.Counter> previous, long elapsedNanos, boolean baseline) {
        List<NetworkSnapshot.Adapter> result = new ArrayList<>();
        for (var counter : current) {
            var old = previous.get(counter.id());
            boolean valid = baseline && old != null && elapsedNanos > 0 && counter.received() >= old.received()
                    && counter.sent() >= old.sent();
            double seconds = elapsedNanos / 1_000_000_000.0;
            result.add(new NetworkSnapshot.Adapter(counter.id(), counter.name(), counter.received(), counter.sent(),
                    valid ? (counter.received() - old.received()) / seconds : 0,
                    valid ? (counter.sent() - old.sent()) / seconds : 0, valid));
        }
        result.sort(Comparator.comparing(NetworkSnapshot.Adapter::name));
        return List.copyOf(result);
    }

    private void addEvent(long now, String type, String text) {
        events.addFirst(new NetworkSnapshot.Event(now, type, text));
        while (events.size() > 200) events.removeLast();
    }
    @Override public void close() { closed = true; scheduler.shutdownNow(); collector.close(); listeners.clear(); }
}
