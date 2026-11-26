package net.activeinference.beacon.backbone;
import neural.studio.*;


import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.ThreadMXBean;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/**
 * ================================================================================
 * SYSTEM RESOURCE BUS BACKBONE // ACTIVE INFRASTRUCTURE TELEMETRY DAEMON
 * ================================================================================
 * Production-ready server subsystem that aggregates all running local Java process metrics
 * and provisions them across live outbound TCP/IP socket connections asynchronously.
 */
public class SubstrateNetworkBus {
    private static final int DISCOVERY_BUS_PORT = 7850;
    
    private final ScheduledExecutorService auditWorkerClock;
    private final ExecutorService networkTransmissionPool;
    private final AtomicReference<BusTelemetryPacket> currentBusState;
    private boolean isServerRunning;

    public SubstrateNetworkBus() {
        this.auditWorkerClock = SharedScheduler.newSingleThreadScheduledExecutor();
        this.networkTransmissionPool = Executors.newCachedThreadPool();
        this.currentBusState = new AtomicReference<>(new BusTelemetryPacket("INIT", 1, 10, 256));
        this.isServerRunning = true;
    }

    /**
     * Loops low-level operating system process environments via the local JPS tool
     * to extract real-time process metadata without using simulated abstractions.
     */
    private void executeSubstrateDiscoveryAudit() {
        try {
            ThreadMXBean threadBean = ManagementFactory.getThreadMXBean();
            MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();

            int currentJvmThreads = threadBean.getThreadCount();
            long currentJvmHeapMb = memoryBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);

            // Access native runtime to sweep active JVM PIDs
            Process jpsProcess = Runtime.getRuntime().exec("jps");
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(jpsProcess.getInputStream(), StandardCharsets.UTF_8))) {
                
                int discoveredJavaInstances = 0;
                while (reader.readLine() != null) {
                    discoveredJavaInstances++;
                }

                // Compile metrics into an immutable state packet
                String isoTimestamp = ZonedDateTime.now().format(DateTimeFormatter.ISO_INSTANT);
                BusTelemetryPacket freshPacket = new BusTelemetryPacket(
                        isoTimestamp,
                        Math.max(1, discoveredJavaInstances),
                        currentJvmThreads,
                        currentJvmHeapMb
                );

                this.currentBusState.set(freshPacket);
            }
        } catch (Exception e) {
            System.err.println("[⚠️ BUS AUDIT FAULT] Discovery sequence interrupted: " + e.getMessage());
        }
    }

    /**
     * Initializes the background server socket, accepting inbound node registrations
     * and offloading data transmissions to the concurrent worker thread pool.
     */
    public void activateNetworkBusSubstrate() {
        // Schedule continuous background process sweeps every 1000 milliseconds
        this.auditWorkerClock.scheduleAtFixedRate(this::executeSubstrateDiscoveryAudit, 0, 1, TimeUnit.SECONDS);

        System.out.println("================================================================================");
        System.out.printf("[🛰️ NET BUS ACTIVE] Initializing backbone framework on socket port: %d%n", DISCOVERY_BUS_PORT);
        System.out.println("================================================================================");

        try (ServerSocket serverSocket = new ServerSocket(DISCOVERY_BUS_PORT)) {
            while (isServerRunning) {
                // Wait block until an endpoint node requests connection access
                Socket endpointSocket = serverSocket.accept();
                
                // Dispatch client processing to thread pool asynchronously to prevent structural blockages
                this.networkTransmissionPool.execute(() -> handleClientNodeStreaming(endpointSocket));
            }
        } catch (Exception e) {
            System.err.println("[❌ CRITICAL BUS MELTDOWN] Server socket closed unexpectedly: " + e.getMessage());
        }
    }

    /**
     * Handles streaming serialization payloads cleanly across the output stream channels.
     */
    private void handleClientNodeStreaming(Socket socket) {
        String remoteAddress = socket.getRemoteSocketAddress().toString();
        System.out.printf("[✅ CLIENT ATTACHED] Node connection ingress approved from: %s%n", remoteAddress);

        try (PrintWriter networkWriter = new PrintWriter(
                new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8), true)) {

            // Stream current unified metrics to the client endpoint node
            BusTelemetryPacket payloadFrame = this.currentBusState.get();
            networkWriter.println(payloadFrame.toString());
            
            System.out.printf("[🔄 BUS TX] Dispatched system frame block directly to %s: %s%n", remoteAddress, payloadFrame);

        } catch (Exception e) {
            System.err.println("[⚠️ CONNECTION DROPPED] Frame stream aborted for target: " + remoteAddress);
        } finally {
            try {
                socket.close();
            } catch (Exception ignored) {}
        }
    }

    /**
     * Master Daemon Bootstrap launch-frame.
     */
    public static void main(String[] args) {
        SubstrateNetworkBus networkBackbone = new SubstrateNetworkBus();
        
        // Register application layer shutdown hooks to guarantee clean OS state releases
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\n[🔒 CORE TERMINATION] Releasing network adapters and thread pools safely.");
            networkBackbone.isServerRunning = false;
            networkBackbone.auditWorkerClock.shutdown();
            networkBackbone.networkTransmissionPool.shutdown();
        }));

        networkBackbone.activateNetworkBusSubstrate();
    }
}
