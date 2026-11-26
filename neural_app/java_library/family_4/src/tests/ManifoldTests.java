import neural.studio.*;
import net.manifold.core.InferenceQuantum;
import net.manifold.crypto.CryptographicConvergenceGate;
import net.manifold.engine.InferenceNetworkBroadcaster;
import net.manifold.distributed.DistributedManifoldOrchestrator;
import net.manifold.telemetry.*;
import net.manifold.ui.NetworkDashboard;
import javax.crypto.spec.SecretKeySpec;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public final class ManifoldTests {
    private static int checks;
    private static void check(boolean condition, String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }
    private interface Throwing { void run() throws Exception; }
    private static void fails(Throwing code, String message) throws Exception {
        boolean failed = false;
        try { code.run(); } catch (Exception expected) { failed = true; }
        check(failed, message);
    }
    private static InferenceQuantum quantum(float[] values) {
        return new InferenceQuantum(UUID.randomUUID(), "local-α", 0x101010, values, 1, 1, System.currentTimeMillis());
    }
    private static String b64(String value) { return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8)); }

    public static void main(String[] args) throws Exception {
        float[] input = {1, 2, 3};
        InferenceQuantum q = quantum(input);
        input[0] = 42;
        check(q.tensorPayload()[0] == 1, "Constructor must copy input");
        float[] external = q.tensorPayload(); external[0] = 99;
        check(q.tensorPayload()[0] == 1, "Accessor must not expose mutable tensor");
        InferenceQuantum decoded = InferenceQuantum.deserialize(q.serialize());
        check(decoded.originNodeId().equals(q.originNodeId()) && decoded.quantumId().equals(q.quantumId())
                && Arrays.equals(decoded.tensorPayload(), q.tensorPayload()), "Wire round trip preserves identity and data");
        fails(() -> quantum(new float[]{Float.NaN}), "NaN rejected");
        fails(() -> quantum(new float[0]), "Empty payload rejected");
        fails(() -> quantum(new float[InferenceQuantum.MAX_TENSOR_LENGTH + 1]), "Oversized payload rejected");
        byte[] bad = q.serialize(); ByteBuffer.wrap(bad).putInt(48, Integer.MAX_VALUE);
        fails(() -> InferenceQuantum.deserialize(bad), "Untrusted length checked before allocation");
        fails(() -> InferenceQuantum.deserialize(Arrays.copyOf(q.serialize(), q.serialize().length - 1)), "Truncation rejected");
        fails(() -> InferenceQuantum.deserialize(Arrays.copyOf(q.serialize(), q.serialize().length + 1)), "Trailing bytes rejected");

        var gate = new CryptographicConvergenceGate();
        var key = new SecretKeySpec(new byte[16], "AES");
        byte[] encrypted = gate.encrypt(q, key);
        check(gate.convergeStream(encrypted, key).originNodeId().equals(q.originNodeId()), "Authenticated round trip");
        encrypted[encrypted.length - 1] ^= 1;
        fails(() -> gate.convergeStream(encrypted, key), "Tampering rejected");
        fails(() -> gate.convergeStream(new byte[10], key), "Short encrypted packet rejected");
        var stale = new InferenceQuantum(UUID.randomUUID(), "local", 0x101010, new float[]{1}, 0, 1, 0);
        fails(() -> gate.convergeStream(gate.encrypt(stale, key), key), "Expired packet rejected");

        InferenceNetworkBroadcaster engine = new InferenceNetworkBroadcaster();
        try {
            ExecutorService callers = Executors.newFixedThreadPool(8);
            try {
                List<Future<CompletableFuture<InferenceQuantum>>> calls = new ArrayList<>();
                for (int i = 0; i < 100; i++) calls.add(callers.submit(() -> engine.submit(q)));
                CompletableFuture<InferenceQuantum> first = calls.get(0).get();
                for (var call : calls) check(call.get() == first, "Concurrent duplicate submissions share one result");
                check(Math.abs(first.get(3, TimeUnit.SECONDS).tensorPayload()[0] - Math.tanh(1)) < 1e-6, "Transform result is correct");
                check(engine.getProcessedCount() == 1, "Duplicate message computes once");
                check(q.tensorPayload()[0] == 1, "Engine does not mutate source");
                new DistributedManifoldOrchestrator(engine).routeParallelQuantum(quantum(new float[1025])).get(3, TimeUnit.SECONDS);
                check(engine.getProcessedCount() == 2, "Large payload runs locally without a remote dependency");
                for (int i = 0; i < 2200; i++) engine.submit(quantum(new float[]{i})).get(3, TimeUnit.SECONDS);
                check(engine.getActiveStreamCount() <= 2048, "Retention is bounded under sustained work");
            } finally { callers.shutdownNow(); }
        } finally { engine.close(); }
        fails(() -> engine.submit(q).get(), "Submissions after close fail");

        String frame = "A\t" + b64("eth") + "\t" + b64("Ethernet α") + "\t5000\t1000\n"
                + "C\t[::1]:45000\t[::1]:443\tESTABLISHED\t123\t" + b64("test-app") + "\nT\tOK\nEND\n";
        var reading = WindowsNetworkCollector.parse(frame);
        check(reading.tcpAvailable() && reading.counters().get(0).name().equals("Ethernet α"), "Collector UTF-8 and framing");
        check(reading.connections().get(0).loopback() && reading.connections().get(0).remoteHost().equals("::1"), "IPv6 endpoint handling");
        fails(() -> WindowsNetworkCollector.parse(frame.replace("END", "")), "Partial snapshot rejected");
        fails(() -> WindowsNetworkCollector.parse("A\tbad\nEND"), "Malformed frame rejected");
        var previous = Map.of("eth", new WindowsNetworkCollector.Counter("eth", "Ethernet", 1000, 500));
        var rates = NetworkMonitor.calculateRates(reading.counters(), previous, 2_000_000_000L, true).get(0);
        check(rates.receiveRate() == 2000 && rates.sendRate() == 250 && rates.rateAvailable(), "Rates use actual elapsed seconds");
        check(!NetworkMonitor.calculateRates(reading.counters(), Map.of(), 2_000_000_000L, true).get(0).rateAvailable(), "New interface gets baseline");
        check(!NetworkMonitor.calculateRates(reading.counters(), previous, 0, true).get(0).rateAvailable(), "Zero interval unavailable");
        var reset = List.of(new WindowsNetworkCollector.Counter("eth", "Ethernet", 1, 1));
        check(!NetworkMonitor.calculateRates(reset, previous, 2_000_000_000L, true).get(0).rateAvailable(), "Counter reset never creates negative rate");
        String csv = NetworkDashboard.csv(List.of(new NetworkSnapshot.Connection("127.0.0.1:1", "127.0.0.1:2", "ESTABLISHED", 1, "=test,\"app\"")), 0);
        check(csv.contains("\"'=test,\"\"app\"\"\""), "CSV quotes fields and neutralizes spreadsheet formulas");
        System.out.println("PASS: " + checks + " regression checks");
    }
}
