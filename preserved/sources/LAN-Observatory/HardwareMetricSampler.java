import java.lang.management.ManagementFactory;
import java.util.concurrent.*;

/** Samples real host/JVM measurements away from Swing's event thread. */
public final class HardwareMetricSampler implements AutoCloseable {
    public static final class Sample {
        public final double cpu;
        public final long heapUsed;
        public final long heapMax;
        public final int threads;
        public final long timestamp;
        Sample(double cpu, long used, long max, int threads) {
            this.cpu = cpu;
            heapUsed = used;
            heapMax = max;
            this.threads = threads;
            timestamp = System.currentTimeMillis();
        }
        public double[] channels() {
            // Four measured signals, repeated as a 64-channel normalized visualization.
            double[] inputs = { cpu < 0 ? 0 : cpu, (double) heapUsed / Math.max(1, heapMax),
                    Math.min(1, threads / 100.0), Math.min(1, Runtime.getRuntime().availableProcessors() / 64.0) };
            double[] values = new double[64];
            for (int i = 0; i < values.length; i++) values[i] = inputs[i % inputs.length];
            return values;
        }
    }
    private final ScheduledExecutorService timer = Executors.newSingleThreadScheduledExecutor(task -> {
        Thread thread = new Thread(task, "host-metrics");
        thread.setDaemon(true);
        return thread;
    });
    private volatile Sample latest = new Sample(-1, 0, Runtime.getRuntime().maxMemory(), 0);
    private final QuantumTernaryBinaryCore core;

    public HardwareMetricSampler(QuantumTernaryBinaryCore core) {
        this.core = core;
        timer.scheduleWithFixedDelay(this::sample, 0, 1, TimeUnit.SECONDS);
    }

    private void sample() {
        double cpu = -1;
        java.lang.management.OperatingSystemMXBean bean = ManagementFactory.getOperatingSystemMXBean();
        if (bean instanceof com.sun.management.OperatingSystemMXBean) {
            cpu = ((com.sun.management.OperatingSystemMXBean) bean).getCpuLoad();
            if (!Double.isFinite(cpu) || cpu < 0) cpu = -1;
            else cpu = Math.min(1, cpu);
        }
        Runtime runtime = Runtime.getRuntime();
        latest = new Sample(cpu, runtime.totalMemory() - runtime.freeMemory(), runtime.maxMemory(),
                ManagementFactory.getThreadMXBean().getThreadCount());
        core.processQuantumState(latest.channels());
    }

    public Sample getLatest() { return latest; }
    @Override public void close() { timer.shutdownNow(); }
}

