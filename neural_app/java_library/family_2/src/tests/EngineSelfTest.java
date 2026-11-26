import neural.studio.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.BooleanSupplier;
import javax.swing.*;

/** Dependency-free regression and loopback integration tests. Run test.bat. */
public final class EngineSelfTest {
    private static int checks;
    public static void main(String[] args) throws Exception {
        coreAndSnapshots();
        protocolsAndLifecycle();
        expiry();
        bindFailure();
        uiFiltering();
        System.out.println("PASS: " + checks + " checks (core, TCP/UDP, legacy filter, restart, expiry, CSV, UI)");
    }

    private static void coreAndSnapshots() {
        QuantumTernaryBinaryCore core = new QuantumTernaryBinaryCore(6, .4);
        check(Math.abs(core.getEntropy() - 6) < 1e-9, "Uniform state entropy");
        core.processQuantumState(new double[] {Double.MAX_VALUE, Double.MAX_VALUE, Double.NaN, Double.POSITIVE_INFINITY});
        double[] result = core.getProbabilities();
        check(result[0] == .5 && result[1] == .5 && result[2] == 0, "Finite overflow-safe normalization");
        check(Math.abs(Arrays.stream(result).sum() - 1) < 1e-10, "Normalized sum");
        result[0] = 99;
        check(core.getProbabilities()[0] == .5, "Core defensive copy");
        check(core.getTernaryStream()[0] == 1 && core.getTernaryStream()[2] == -1, "Ternary states");
        boolean invalid = false;
        try { new QuantumTernaryBinaryCore(31, .4); } catch (IllegalArgumentException expected) { invalid = true; }
        check(invalid, "Dimension validation");
        double[] probabilities = {.5, .5};
        RemoteDeviceNode before = new RemoteDeviceNode("device", "ANDROID", "127.0.0.1");
        RemoteDeviceNode after = before.updateTelemetry(probabilities, 1, .6, System.currentTimeMillis());
        probabilities[0] = 100;
        check(before.messageCount == 0 && after.messageCount == 1, "Immutable node update");
        check(after.getProbabilities()[0] == .5, "Immutable probability snapshot");
        check(TelemetryExport.cell("-phone").equals("\"'-phone\""), "CSV formula protection");
        check(TelemetryExport.toCsv(List.of(before)).contains("Discovered\",,,0,"), "Missing telemetry stays blank in CSV");
    }

    private static void protocolsAndLifecycle() throws Exception {
        try (LocalNetworkLatchingEngine engine = new LocalNetworkLatchingEngine(0, 0, 30_000)) {
            engine.startEngine();
            check(engine.isRunning(), "Receiver starts");
            int port = engine.getTcpPort();
            engine.startEngine();
            check(engine.getTcpPort() == port, "Start is idempotent");
            check(send(port, "LAN1|ANDROID|pixel|1.0|0.75|0.5,0.5\n").equals("OK"), "Text frame acknowledgement");
            check(send(port, "LAN1|IOS|iphone|0|0|\n").equals("OK"), "iOS and empty distribution accepted");
            check(engine.getLatchedDevices().size() == 2, "Text protocol self-registers");
            long firstSeen = engine.getLatchedDevices().get("pixel").lastSeenTimestamp;
            Thread.sleep(20);
            beacon(engine.getDiscoveryPort(), "GODMIND_BEACON:ANDROID:pixel");
            await(() -> engine.getLatchedDevices().get("pixel").lastSeenTimestamp > firstSeen, "Beacon refreshes existing device");
            check(engine.getLatchedDevices().get("pixel").messageCount == 1, "Beacon preserves telemetry");
            beacon(engine.getDiscoveryPort(), "GODMIND_BEACON:ANDROID:legacy");
            await(() -> engine.getLatchedDevices().containsKey("legacy"), "UDP discovery");
            serialized(port, new NetworkMessage("ANDROID", "legacy", new double[] {.25, .75}, .81, .6));
            await(() -> engine.getLatchedDevices().get("legacy").messageCount == 1, "Legacy telemetry");
            serialized(port, new Date());
            await(() -> engine.getRejectedCount() >= 1, "Unexpected serialized class rejected");
            long rejected = engine.getRejectedCount();
            serialized(port, new NetworkMessage("ANDROID", "legacy", new double[257], 1, .5));
            await(() -> engine.getRejectedCount() > rejected, "Oversized legacy array rejected");
            long frames = engine.getAcceptedCount();
            check(send(port, "LAN1|ANDROID|pixel|NaN|0.5|1\n").isEmpty(), "Nonfinite entropy rejected");
            check(send(port, "LAN1|IOS|iphone|1|0.5|0.1,0.1\n").isEmpty(), "Invalid distribution rejected");
            check(send(port, "LAN1|BAD|other|1|0.5|1\n").isEmpty(), "Unknown platform rejected");
            check(send(port, "LAN1|IOS|bad id|1|0.5|1\n").isEmpty(), "Invalid ID rejected");
            check(engine.getAcceptedCount() == frames, "Malformed frames do not mutate telemetry");
            Map<String, RemoteDeviceNode> snapshot = engine.getLatchedDevices();
            boolean immutable = false;
            try { snapshot.clear(); } catch (UnsupportedOperationException expected) { immutable = true; }
            check(immutable, "Device map is read-only");
            ExecutorService senders = Executors.newFixedThreadPool(8);
            try {
                List<Future<String>> replies = new ArrayList<>();
                for (int i = 0; i < 16; i++) {
                    final int id = i;
                    replies.add(senders.submit(() -> send(port, "LAN1|IOS|parallel-" + id + "|1|0.5|0.5,0.5\n")));
                }
                for (Future<String> reply : replies) check(reply.get(5, TimeUnit.SECONDS).equals("OK"), "Concurrent client accepted");
            } finally { senders.shutdownNow(); }
            Socket idle = new Socket(InetAddress.getLoopbackAddress(), port);
            idle.setSoTimeout(2000);
            Thread.sleep(50);
            engine.stopEngine();
            check(!engine.isRunning() && engine.getLatchedDevices().isEmpty(), "Stop clears live state");
            check(idle.getInputStream().read() == -1, "Stop closes stalled clients");
            idle.close();
            engine.startEngine();
            check(engine.isRunning() && engine.getAcceptedCount() == 0, "Restart creates a fresh session");
            check(send(engine.getTcpPort(), "LAN1|IOS|after-restart|1|0.5|1\n").equals("OK"), "Traffic after restart");
        }
    }

    private static void expiry() throws Exception {
        try (LocalNetworkLatchingEngine engine = new LocalNetworkLatchingEngine(0, 0, 1200)) {
            engine.startEngine();
            beacon(engine.getDiscoveryPort(), "GODMIND_BEACON:IOS:heartbeat");
            await(() -> engine.getLatchedDevices().containsKey("heartbeat"), "Expiry test registration");
            for (int i = 0; i < 4; i++) {
                Thread.sleep(500);
                beacon(engine.getDiscoveryPort(), "GODMIND_BEACON:IOS:heartbeat");
            }
            check(engine.getLatchedDevices().containsKey("heartbeat"), "Heartbeats survive original expiry window");
            await(() -> engine.getLatchedDevices().isEmpty(), "Inactive devices expire");
        }
    }

    private static void bindFailure() throws Exception {
        try (ServerSocket occupied = new ServerSocket(0);
             LocalNetworkLatchingEngine engine = new LocalNetworkLatchingEngine(0, occupied.getLocalPort(), 30_000)) {
            engine.startEngine();
            check(!engine.isRunning() && engine.getStatus().equals("Start failed"), "TCP port conflict is visible");
            check(engine.getEvents().stream().anyMatch(s -> s.contains("Could not start")), "Failure reason in journal");
        }
        try (DatagramSocket occupied = new DatagramSocket(0);
             LocalNetworkLatchingEngine engine = new LocalNetworkLatchingEngine(occupied.getLocalPort(), 0, 30_000)) {
            engine.startEngine();
            check(!engine.isRunning(), "UDP failure rolls back TCP startup");
        }
    }

    private static void uiFiltering() throws Exception {
        try (LocalNetworkLatchingEngine engine = new LocalNetworkLatchingEngine(0, 0, 30_000)) {
            engine.startEngine();
            send(engine.getTcpPort(), "LAN1|ANDROID|pixel|1|0.5|1\n");
            send(engine.getTcpPort(), "LAN1|IOS|iphone|1|0.5|1\n");
            SwingUtilities.invokeAndWait(() -> {
                LANMatrixCanvas canvas = new LANMatrixCanvas(new QuantumTernaryBinaryCore(6, .4), engine);
                canvas.refresh(new HardwareMetricSampler.Sample(.4, 100, 1000, 15));
                JTable table = find(canvas, JTable.class);
                JTextField search = find(canvas, JTextField.class);
                JComboBox<?> platform = find(canvas, JComboBox.class);
                check(table.getRowCount() == 2, "UI renders device rows");
                search.setText("pix");
                check(table.getRowCount() == 1 && table.getValueAt(0, 0).equals("pixel"), "Search filters device IDs");
                search.setText("");
                platform.setSelectedItem("iOS");
                check(table.getRowCount() == 1 && table.getValueAt(0, 0).equals("iphone"), "Platform filter");
                table.setRowSelectionInterval(0, 0);
                canvas.refresh(new HardwareMetricSampler.Sample(.5, 100, 1000, 15));
                check(table.getSelectedRow() == 0, "Refresh retains selection");
                search.setText("[unmatched");
                check(table.getRowCount() == 0, "Search is literal, not regex");
            });
        }
    }

    static <T> T find(java.awt.Container parent, Class<T> type) {
        for (java.awt.Component child : parent.getComponents()) {
            if (type.isInstance(child)) return type.cast(child);
            if (child instanceof java.awt.Container) {
                T found = find((java.awt.Container) child, type);
                if (found != null) return found;
            }
        }
        return null;
    }

    static String send(int port, String text) throws IOException {
        try (Socket socket = new Socket(InetAddress.getLoopbackAddress(), port)) {
            socket.setSoTimeout(4000);
            socket.getOutputStream().write(text.getBytes(StandardCharsets.UTF_8));
            socket.getOutputStream().flush();
            String reply = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8)).readLine();
            return reply == null ? "" : reply;
        }
    }

    private static void serialized(int port, Object message) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(message);
            out.flush();
        }
        try (Socket socket = new Socket(InetAddress.getLoopbackAddress(), port)) {
            socket.getOutputStream().write(bytes.toByteArray());
            socket.getOutputStream().flush();
        }
    }

    private static void beacon(int port, String message) throws IOException {
        byte[] bytes = message.getBytes(StandardCharsets.UTF_8);
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.send(new DatagramPacket(bytes, bytes.length, InetAddress.getLoopbackAddress(), port));
        }
    }

    private static void await(BooleanSupplier ready, String label) throws Exception {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (!ready.getAsBoolean() && System.nanoTime() < deadline) Thread.sleep(15);
        check(ready.getAsBoolean(), label);
    }

    private static void check(boolean value, String label) {
        if (!value) throw new AssertionError(label);
        checks++;
    }
}
