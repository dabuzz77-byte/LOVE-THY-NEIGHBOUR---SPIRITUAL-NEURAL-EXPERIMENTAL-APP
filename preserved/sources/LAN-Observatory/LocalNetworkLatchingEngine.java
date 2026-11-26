import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

/** Bounded LAN receiver with restartable sessions and observable failures. */
public final class LocalNetworkLatchingEngine implements AutoCloseable {
    public static final String MULTICAST_GROUP = "239.255.255.250";
    public static final int DISCOVERY_PORT = 19110;
    public static final int TCP_DATA_PORT = 19111;
    private static final int MAX_DEVICES = 512;
    private static final int MAX_LINE = 16_384;
    private final int discoveryPort;
    private final int tcpPort;
    private final long staleMillis;
    private final Map<String, RemoteDeviceNode> devices = new ConcurrentHashMap<>();
    private final Deque<String> events = new ArrayDeque<>();
    private final AtomicLong accepted = new AtomicLong();
    private final AtomicLong rejected = new AtomicLong();
    private volatile Session session;
    private volatile String status = "Stopped";
    private volatile long startedAt;

    public LocalNetworkLatchingEngine() { this(DISCOVERY_PORT, TCP_DATA_PORT, 30_000); }

    // Port zero and a configurable expiry enable isolated integration tests.
    LocalNetworkLatchingEngine(int discoveryPort, int tcpPort, long staleMillis) {
        if (staleMillis < 100) throw new IllegalArgumentException("Expiry must be at least 100 ms");
        this.discoveryPort = discoveryPort;
        this.tcpPort = tcpPort;
        this.staleMillis = staleMillis;
    }

    private static ThreadFactory threads(String prefix) {
        return task -> {
            Thread thread = new Thread(task, prefix);
            thread.setDaemon(true);
            return thread;
        };
    }

    private static final class Session {
        final MulticastSocket udp;
        final ServerSocket tcp;
        final ExecutorService listeners = Executors.newFixedThreadPool(2, threads("lan-listener"));
        final ThreadPoolExecutor clients = new ThreadPoolExecutor(4, 4, 0, TimeUnit.SECONDS,
                new ArrayBlockingQueue<>(32), threads("lan-client"), new ThreadPoolExecutor.AbortPolicy());
        final ScheduledExecutorService maintenance = Executors.newSingleThreadScheduledExecutor(threads("lan-expiry"));
        final Set<Socket> sockets = ConcurrentHashMap.newKeySet();
        volatile boolean active = true;
        Session(MulticastSocket udp, ServerSocket tcp) { this.udp = udp; this.tcp = tcp; }
        void shutdown() {
            active = false;
            udp.close();
            closeQuietly(tcp);
            sockets.forEach(LocalNetworkLatchingEngine::closeQuietly);
            sockets.clear();
            listeners.shutdownNow();
            clients.shutdownNow();
            maintenance.shutdownNow();
        }
    }

    public synchronized void startEngine() {
        if (session != null) return;
        MulticastSocket udp = null;
        ServerSocket tcp = null;
        try {
            tcp = new ServerSocket();
            tcp.setReuseAddress(true);
            tcp.bind(new InetSocketAddress(tcpPort), 32);
            udp = new MulticastSocket(null);
            udp.setReuseAddress(false);
            udp.bind(new InetSocketAddress(discoveryPort));
            int joined = 0;
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            if (interfaces != null) {
                for (NetworkInterface nic : Collections.list(interfaces)) {
                    try {
                        boolean ipv4 = Collections.list(nic.getInetAddresses()).stream().anyMatch(a -> a instanceof Inet4Address);
                        if (nic.isUp() && nic.supportsMulticast() && ipv4) {
                            udp.joinGroup(new InetSocketAddress(InetAddress.getByName(MULTICAST_GROUP), udp.getLocalPort()), nic);
                            joined++;
                        }
                    } catch (IOException ignored) { /* Direct UDP/TCP still works on this interface. */ }
                }
            }
            Session next = new Session(udp, tcp);
            devices.clear();
            accepted.set(0);
            rejected.set(0);
            startedAt = System.currentTimeMillis();
            session = next;
            status = joined > 0 ? "Listening" : "Listening - direct connections";
            log("Receiver started: UDP " + udp.getLocalPort() + " / TCP " + tcp.getLocalPort());
            if (joined == 0) log("Multicast unavailable. Send beacons or LAN1 frames directly to this computer.");
            next.listeners.execute(() -> receiveBeacons(next));
            next.listeners.execute(() -> acceptClients(next));
            next.maintenance.scheduleWithFixedDelay(() -> evict(next), 1, 1, TimeUnit.SECONDS);
        } catch (IOException | RuntimeException ex) {
            closeQuietly(udp);
            closeQuietly(tcp);
            if (session != null) session.shutdown();
            session = null;
            status = "Start failed";
            log("Could not start receiver: " + error(ex));
        }
    }

    private void receiveBeacons(Session current) {
        byte[] buffer = new byte[512];
        while (current.active) {
            try {
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                current.udp.receive(packet);
                if (packet.getLength() == buffer.length) throw new IllegalArgumentException("Beacon too long");
                String beacon = new String(packet.getData(), 0, packet.getLength(), StandardCharsets.UTF_8).trim();
                String[] parts = beacon.split(":", -1);
                if (parts.length != 3 || !parts[0].equals("GODMIND_BEACON")) throw new IllegalArgumentException("Invalid beacon");
                String platform = platform(parts[1]);
                String id = deviceId(parts[2]);
                synchronized (this) {
                    if (session != current || !current.active) return;
                    RemoteDeviceNode old = devices.get(id);
                    if (old == null && devices.size() >= MAX_DEVICES) throw new IllegalArgumentException("Device limit reached");
                    String ip = packet.getAddress().getHostAddress();
                    if (old != null && !old.ipAddress.equals(ip)) throw new IllegalArgumentException("Device ID already in use");
                    devices.put(id, old == null ? new RemoteDeviceNode(id, platform, ip)
                            : old.heartbeat(platform, ip, System.currentTimeMillis()));
                    if (old == null) log("Discovered " + platform + " device " + id);
                }
            } catch (SocketException ex) {
                if (current.active) fail(current, "Discovery stopped: " + error(ex));
                return;
            } catch (IOException | IllegalArgumentException ex) {
                reject(current, "Discovery: " + error(ex));
            }
        }
    }

    private void acceptClients(Session current) {
        while (current.active) {
            try {
                Socket socket = current.tcp.accept();
                socket.setSoTimeout(3_000);
                socket.setTcpNoDelay(true);
                current.sockets.add(socket);
                if (!current.active) {
                    current.sockets.remove(socket);
                    closeQuietly(socket);
                    return;
                }
                try {
                    current.clients.execute(() -> receiveFrame(current, socket));
                } catch (RejectedExecutionException ex) {
                    current.sockets.remove(socket);
                    closeQuietly(socket);
                    reject(current, "Receiver busy; connection closed");
                }
            } catch (IOException ex) {
                if (current.active) fail(current, "TCP listener stopped: " + error(ex));
                return;
            }
        }
    }

    private void receiveFrame(Session current, Socket socket) {
        try (Socket connection = socket;
             PushbackInputStream input = new PushbackInputStream(new LimitedInputStream(connection.getInputStream(), 32_768), 2)) {
            int first = input.read(), second = input.read();
            if (first < 0 || second < 0) throw new EOFException("Incomplete frame");
            input.unread(new byte[] {(byte) first, (byte) second});
            boolean legacy = first == 0xac && second == 0xed;
            NetworkMessage message;
            if (legacy) {
                try (ObjectInputStream objects = new ObjectInputStream(new LimitedInputStream(input, 32_768))) {
                    objects.setObjectInputFilter(info -> {
                        if (info.depth() > 5 || info.references() > 32 || info.streamBytes() > 32_768
                                || info.arrayLength() > 256) return ObjectInputFilter.Status.REJECTED;
                        Class<?> type = info.serialClass();
                        if (type == null) return ObjectInputFilter.Status.UNDECIDED;
                        return type == NetworkMessage.class || type == String.class || type == double[].class
                                ? ObjectInputFilter.Status.ALLOWED : ObjectInputFilter.Status.REJECTED;
                    });
                    Object value = objects.readObject();
                    if (!(value instanceof NetworkMessage)) throw new IOException("Expected NetworkMessage");
                    message = (NetworkMessage) value;
                    accept(current, message, connection.getInetAddress().getHostAddress(), true);
                }
            } else {
                message = parseText(readLine(input));
                accept(current, message, connection.getInetAddress().getHostAddress(), false);
                connection.getOutputStream().write("OK\n".getBytes(StandardCharsets.UTF_8));
                connection.getOutputStream().flush();
            }
        } catch (IOException | ClassNotFoundException | IllegalArgumentException ex) {
            reject(current, "Frame rejected: " + error(ex));
        } finally {
            current.sockets.remove(socket);
        }
    }

    private static final class LimitedInputStream extends FilterInputStream {
        private int remaining;
        private final long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(6);
        LimitedInputStream(InputStream input, int limit) { super(input); remaining = limit; }
        @Override public int read() throws IOException {
            if (System.nanoTime() > deadline) throw new SocketTimeoutException("Frame deadline exceeded");
            if (remaining <= 0) throw new IOException("Frame too large");
            int b = super.read();
            if (b >= 0) remaining--;
            return b;
        }
        @Override public int read(byte[] bytes, int offset, int length) throws IOException {
            if (System.nanoTime() > deadline) throw new SocketTimeoutException("Frame deadline exceeded");
            if (length == 0) return 0;
            if (remaining <= 0) throw new IOException("Frame too large");
            int count = in.read(bytes, offset, Math.min(length, remaining));
            if (count > 0) remaining -= count;
            return count;
        }
    }

    static String readLine(InputStream input) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        for (int i = 0; i <= MAX_LINE; i++) {
            int value = input.read();
            if (value == '\n') return bytes.toString(StandardCharsets.UTF_8).trim();
            if (value < 0) throw new EOFException("A frame must end with a newline");
            if (i == MAX_LINE) throw new IOException("Frame too large");
            bytes.write(value);
        }
        throw new IOException("Frame too large");
    }

    static NetworkMessage parseText(String text) {
        String[] fields = text.split("\\|", -1);
        if (fields.length != 6 || !fields[0].equals("LAN1"))
            throw new IllegalArgumentException("Expected LAN1|platform|id|entropy|salience|probabilities");
        String[] values = fields[5].isEmpty() ? new String[0] : fields[5].split(",", -1);
        if (values.length > 256) throw new IllegalArgumentException("Maximum 256 probabilities");
        double[] probabilities = new double[values.length];
        for (int i = 0; i < values.length; i++) probabilities[i] = Double.parseDouble(values[i]);
        return new NetworkMessage(fields[1], fields[2], probabilities,
                Double.parseDouble(fields[3]), Double.parseDouble(fields[4]));
    }

    private synchronized void accept(Session current, NetworkMessage message, String ip, boolean legacy) {
        if (session != current || !current.active) return;
        String id = deviceId(message.deviceId);
        String platform = platform(message.platformType);
        if (!Double.isFinite(message.entropy) || message.entropy < 0 || message.entropy > 64)
            throw new IllegalArgumentException("Entropy must be finite and in [0, 64]");
        if (!Double.isFinite(message.salience) || message.salience < 0 || message.salience > 1)
            throw new IllegalArgumentException("Salience must be finite and in [0, 1]");
        double[] probabilities = message.stateProbabilities;
        if (probabilities == null || probabilities.length > 256) throw new IllegalArgumentException("Invalid probability array");
        double sum = 0;
        for (double p : probabilities) {
            if (!Double.isFinite(p) || p < 0 || p > 1) throw new IllegalArgumentException("Probability outside [0, 1]");
            sum += p;
        }
        if (probabilities.length > 0 && Math.abs(sum - 1) > 0.01)
            throw new IllegalArgumentException("Probabilities must sum to 1 (tolerance 0.01)");
        RemoteDeviceNode old = devices.get(id);
        if (old == null && legacy) throw new IllegalArgumentException("Legacy clients must send a beacon first");
        if (old != null && !old.ipAddress.equals(ip)) throw new IllegalArgumentException("Device ID belongs to another address");
        if (old == null && devices.size() >= MAX_DEVICES) throw new IllegalArgumentException("Device limit reached");
        long now = System.currentTimeMillis();
        RemoteDeviceNode base = old == null ? new RemoteDeviceNode(id, platform, ip) : old.heartbeat(platform, ip, now);
        devices.put(id, base.updateTelemetry(probabilities, message.entropy, message.salience, now));
        accepted.incrementAndGet();
        if (old == null) log("Connected " + platform + " device " + id);
    }

    private static String deviceId(String value) {
        if (value == null || !value.matches("[A-Za-z0-9._-]{1,64}"))
            throw new IllegalArgumentException("Use 1-64 letters, digits, dots, underscores or hyphens for the device ID");
        return value;
    }

    private static String platform(String value) {
        if (value == null) throw new IllegalArgumentException("Platform is required");
        String normalized = value.toUpperCase(Locale.ROOT);
        if (!normalized.equals("ANDROID") && !normalized.equals("IOS"))
            throw new IllegalArgumentException("Platform must be ANDROID or IOS");
        return normalized;
    }

    private synchronized void evict(Session current) {
        if (session != current || !current.active) return;
        long now = System.currentTimeMillis();
        devices.entrySet().removeIf(entry -> {
            if (now - entry.getValue().lastSeenTimestamp <= staleMillis) return false;
            log("Expired device " + entry.getKey());
            return true;
        });
    }

    private synchronized void fail(Session current, String reason) {
        if (session != current) return;
        current.shutdown();
        session = null;
        devices.clear();
        status = "Receiver error";
        log(reason);
    }

    private synchronized void reject(Session current, String reason) {
        if (session != current || !current.active) return;
        long count = rejected.incrementAndGet();
        // Keep noisy clients from monopolizing the log.
        if (count <= 5 || count % 100 == 0) log(reason + " (rejected: " + count + ")");
    }

    private synchronized void log(String event) {
        String clean = event.replaceAll("[\\p{Cntrl}]", " ");
        events.addFirst(LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")) + "  " + clean);
        while (events.size() > 100) events.removeLast();
    }

    private static String error(Exception ex) {
        return ex.getMessage() == null ? ex.getClass().getSimpleName() : ex.getMessage();
    }

    private static void closeQuietly(Closeable resource) {
        if (resource != null) try { resource.close(); } catch (IOException ignored) { }
    }

    public synchronized void stopEngine() {
        Session old = session;
        session = null;
        if (old != null) {
            old.shutdown();
            devices.clear();
            log("Receiver stopped");
        }
        status = "Stopped";
    }

    public boolean isRunning() { return session != null; }
    public String getStatus() { return status; }
    public long getAcceptedCount() { return accepted.get(); }
    public long getRejectedCount() { return rejected.get(); }
    public long getUptimeSeconds() { return isRunning() ? (System.currentTimeMillis() - startedAt) / 1000 : 0; }
    public synchronized Map<String, RemoteDeviceNode> getLatchedDevices() {
        return Collections.unmodifiableMap(new TreeMap<>(devices));
    }
    public synchronized List<String> getEvents() { return List.copyOf(events); }
    public synchronized int getDiscoveryPort() { return session == null ? discoveryPort : session.udp.getLocalPort(); }
    public synchronized int getTcpPort() { return session == null ? tcpPort : session.tcp.getLocalPort(); }
    @Override public void close() { stopEngine(); }
}

