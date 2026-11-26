package net.manifold.telemetry;
import neural.studio.*;


import java.util.List;

public record NetworkSnapshot(long capturedAt, long sequence, List<Adapter> adapters,
        List<Connection> connections, List<Event> events, boolean tcpAvailable, String warning, String error) {
    public NetworkSnapshot {
        adapters = List.copyOf(adapters); connections = List.copyOf(connections); events = List.copyOf(events);
    }
    public record Adapter(String id, String name, long receivedBytes, long sentBytes,
            double receiveRate, double sendRate, boolean rateAvailable) {
        @Override public String toString() { return name; }
    }
    public record Connection(String local, String remote, String state, int pid, String process) {
        public String key() { return local + "|" + remote + "|" + pid; }
        public boolean established() { return state.equals("ESTABLISHED"); }
        public boolean listening() { return state.equals("LISTENING"); }
        public String remoteHost() {
            int split = remote.lastIndexOf(':');
            return split > 0 ? remote.substring(0, split).replace("[", "").replace("]", "") : remote;
        }
        public boolean loopback() {
            String host = remoteHost();
            return host.equals("::1") || host.startsWith("127.") || host.startsWith("::ffff:127.");
        }
    }
    public record Event(long time, String type, String description) {}
    public static NetworkSnapshot waiting() {
        return new NetworkSnapshot(0, 0, List.of(), List.of(), List.of(), false, "", "");
    }
    public long establishedCount() { return connections.stream().filter(Connection::established).count(); }
    public long processCount() { return connections.stream().filter(Connection::established).map(Connection::pid).distinct().count(); }
    public boolean stale() { return capturedAt > 0 && System.currentTimeMillis() - capturedAt > 10_000; }
}
