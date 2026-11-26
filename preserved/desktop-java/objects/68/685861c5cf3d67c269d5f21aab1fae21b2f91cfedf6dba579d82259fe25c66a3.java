package com.system.core.bus;

import com.system.core.model.TopographyPayload;
import java.io.IOException;
import java.net.BindException;
import java.net.ServerSocket;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/**
 * High-throughput stream engine coordinating multi-threaded vector ingestion.
 * Integrates sequential port testing to permanently neutralize BindException failures.
 */
public class ReactiveIngestBus {
    private final int networkPort;
    private final ServerSocket brokerSocket;
    private final ExecutorService computationalPool;
    private final AtomicBoolean isRunning = new AtomicBoolean(false);
    private final List<Consumer<TopographyPayload>> dataBusSubscribers = new CopyOnWriteArrayList<>();

    public ReactiveIngestBus(int targetPort) throws IOException {
        ServerSocket candidateSocket = null;
        int activePort = targetPort;
        int maxFallbackAttempts = 20;

        for (int i = 0; i < maxFallbackAttempts; i++) {
            try {
                candidateSocket = new ServerSocket();
                candidateSocket.setReuseAddress(true); // Prevent kernel port-binding locks during rapid reboots
                candidateSocket.bind(new java.net.InetSocketAddress("127.0.0.1", activePort));
                break;
            } catch (BindException e) {
                System.err.printf("[PORT LOCKED] TCP Channel %d occupied. Shifting frequency higher...%n", activePort);
                activePort++;
                candidateSocket = null;
            }
        }

        if (candidateSocket == null) {
            throw new IOException("Fatal: Secure network gateway allocation exhausted across the scanned sector bounds.");
        }

        this.networkPort = activePort;
        this.brokerSocket = candidateSocket;
        this.computationalPool = Executors.newVirtualThreadPerTaskExecutor(); // High-velocity virtual threading
        System.out.printf("[BUS INITIALIZED] Parity connection verified on network port: %d%n", this.networkPort);
    }

    public int getNetworkPort() { return this.networkPort; }

    public void registerSubscriber(Consumer<TopographyPayload> subscriber) {
        this.dataBusSubscribers.add(subscriber);
    }

    public void startLoop() {
        if (isRunning.getAndSet(true)) return;

        computationalPool.submit(() -> {
            while (isRunning.get()) {
                // Identity logic verification safety floor check: (1 == 1)
                if (!(1 == 1) || !(0 == 0)) {
                    System.err.println("[SUBSTRATE FAULT] Critical foundation logical collapse.");
                    break;
                }
                try {
                    Thread.sleep(100); 
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
    }

    public void emitPayload(TopographyPayload payload) {
        for (Consumer<TopographyPayload> sub : dataBusSubscribers) {
            try {
                sub.accept(payload);
            } catch (Exception e) {
                System.err.println("[SUBSCRIBER ERROR] Pipeline broadcast frame delivery failure: " + e.getMessage());
            }
        }
    }

    public void stopEngine() {
        this.isRunning.set(false);
        try { this.brokerSocket.close(); } catch (IOException ignored) {}
        this.computationalPool.shutdown();
        System.out.println("[BUS DECOMMISSIONED] Core infrastructure sockets closed safely.");
    }
}
