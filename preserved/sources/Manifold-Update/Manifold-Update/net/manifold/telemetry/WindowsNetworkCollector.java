package net.manifold.telemetry;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;

/** One bounded, asynchronous OS snapshot. No elevated access or third-party dependencies. */
public final class WindowsNetworkCollector implements AutoCloseable {
    public record Counter(String id, String name, long received, long sent) {}
    public record Reading(List<Counter> counters, List<NetworkSnapshot.Connection> connections,
            boolean tcpAvailable, String warning) {}
    private final ExecutorService reader = Executors.newSingleThreadExecutor(task -> {
        Thread t = new Thread(task, "network-collector-output"); t.setDaemon(true); return t;
    });
    private volatile Process active;
    private volatile boolean closed;
    private final String command;

    public WindowsNetworkCollector() throws IOException {
        if (!System.getProperty("os.name").startsWith("Windows")) throw new IOException("Live collection requires Windows");
        try (InputStream input = getClass().getResourceAsStream("collect-network.ps1")) {
            if (input == null) throw new IOException("Missing collect-network.ps1 resource; run build.bat");
            command = Base64.getEncoder().encodeToString(new String(input.readAllBytes(), StandardCharsets.UTF_8)
                    .getBytes(StandardCharsets.UTF_16LE));
        }
    }

    public Reading collect() throws Exception {
        Process process;
        synchronized (this) {
            if (closed) throw new IOException("Collector closed");
            String root = System.getenv().getOrDefault("SystemRoot", "C:\\Windows");
            process = new ProcessBuilder(Path.of(root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe").toString(),
                    "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", command)
                    .redirectErrorStream(true).start();
            active = process;
        }
        Future<String> output = reader.submit(() -> {
            try (InputStream input = process.getInputStream()) {
                byte[] bytes = input.readNBytes(4 * 1024 * 1024 + 1);
                if (bytes.length > 4 * 1024 * 1024) throw new IOException("Collector output exceeded limit");
                return new String(bytes, StandardCharsets.UTF_8);
            }
        });
        try {
            if (!process.waitFor(12, TimeUnit.SECONDS)) throw new IOException("Windows network collection timed out; retrying");
            String text = output.get(2, TimeUnit.SECONDS);
            if (process.exitValue() != 0) throw new IOException("Windows collector exited with code " + process.exitValue());
            return parse(text);
        } finally {
            terminate(process);
            output.cancel(true);
            active = null;
        }
    }

    public static Reading parse(String text) throws IOException {
        List<Counter> counters = new ArrayList<>();
        List<NetworkSnapshot.Connection> connections = new ArrayList<>();
        List<String> warnings = new ArrayList<>();
        boolean complete = false, tcp = false;
        try {
            for (String line : text.split("\\R")) {
                String[] fields = line.split("\t", -1);
                switch (fields[0]) {
                    case "A" -> {
                        if (fields.length != 5) throw new IllegalArgumentException("Adapter framing");
                        long received = Long.parseLong(fields[3]), sent = Long.parseLong(fields[4]);
                        if (received < 0 || sent < 0) throw new IllegalArgumentException("Negative counters");
                        counters.add(new Counter(decode(fields[1]), decode(fields[2]), received, sent));
                    }
                    case "C" -> {
                        if (fields.length != 6 || connections.size() >= 10000) throw new IllegalArgumentException("Connection framing");
                        connections.add(new NetworkSnapshot.Connection(fields[1], fields[2], fields[3],
                                Integer.parseInt(fields[4]), decode(fields[5])));
                    }
                    case "W" -> warnings.add(decode(fields[1]));
                    case "T" -> tcp = fields.length == 2 && fields[1].equals("OK");
                    case "END" -> complete = true;
                    default -> { /* PowerShell diagnostics never become data. */ }
                }
            }
        } catch (RuntimeException failure) { throw new IOException("Malformed collector output", failure); }
        if (!complete) throw new IOException("Incomplete Windows network snapshot");
        return new Reading(List.copyOf(counters), List.copyOf(connections), tcp, String.join("; ", warnings));
    }

    private static String decode(String value) { return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8); }
    private static void terminate(Process process) {
        process.descendants().forEach(child -> { if (child.isAlive()) child.destroyForcibly(); });
        if (process.isAlive()) process.destroyForcibly();
    }
    @Override public synchronized void close() {
        closed = true;
        Process process = active;
        if (process != null) terminate(process);
        reader.shutdownNow();
    }
}
