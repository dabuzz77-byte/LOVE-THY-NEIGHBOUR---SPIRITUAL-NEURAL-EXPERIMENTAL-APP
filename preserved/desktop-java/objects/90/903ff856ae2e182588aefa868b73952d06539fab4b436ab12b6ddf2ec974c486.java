import java.io.ObjectInputStream;
import java.net.*;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * LOCAL NETWORK PERIMETER DISCOVERY & LATCHING SUITE
 * Uses a non-blocking Multicast socket to catch beacons and handles incoming TCP telemetry packets.
 */
public class LocalNetworkLatchingEngine {
    private static final String MULTICAST_GROUP = "239.255.255.250";
    private static final int DISCOVERY_PORT = 19110;
    private static final int TCP_DATA_PORT = 19111;

    private final Map<String, RemoteDeviceNode> latchedDevices = new ConcurrentHashMap<>();
    private final ExecutorService networkPool = Executors.newFixedThreadPool(8);
    
    private MulticastSocket multicastSocket;
    private ServerSocket tcpServerSocket;
    private boolean isRunning = false;

    public void startEngine() {
        this.isRunning = true;
        
        // 1. Fire up Multicast discovery socket listener
        networkPool.execute(this::listenForMulticastBeacons);
        
        // 2. Fire up structural TCP reception stream listener
        networkPool.execute(this::listenForInboundDataStreams);
        
        // 3. Fire up pruning daemon to drop stale perimeter channels
        networkPool.execute(this::evictDeadPerimeterNodes);
    }

    private void listenForMulticastBeacons() {
        try {
            InetAddress group = InetAddress.getByName(MULTICAST_GROUP);
            multicastSocket = new MulticastSocket(DISCOVERY_PORT);
            multicastSocket.joinGroup(group);

            byte[] buffer = new byte[256];
            while (isRunning) {
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                multicastSocket.receive(packet);

                String beaconStr = new String(packet.getData(), 0, packet.getLength()).trim();
                // Format token structure matching mobile beacons: "GODMIND_BEACON:[PLATFORM]:[DEVICE_ID]"
                if (beaconStr.startsWith("GODMIND_BEACON:")) {
                    String[] tokens = beaconStr.split(":");
                    if (tokens.length >= 3) {
                        String platform = tokens[1];
                        String id = tokens[2];
                        String ip = packet.getAddress().getHostAddress();

                        latchedDevices.computeIfAbsent(id, k -> new RemoteDeviceNode(id, platform, ip));
                    }
                }
            }
        } catch (Exception e) {
            // Context degradation handling for dropped device connections
        }
    }

    private void listenForInboundDataStreams() {
        try {
            tcpServerSocket = new ServerSocket(TCP_DATA_PORT);
            while (isRunning) {
                Socket connectedSocket = tcpServerSocket.accept();
                networkPool.execute(() -> processIncomingConnection(connectedSocket));
            }
        } catch (Exception e) {
            // Safe termination cascade
        }
    }

    private void processIncomingConnection(Socket socket) {
        try (ObjectInputStream ois = new ObjectInputStream(socket.getInputStream())) {
            NetworkMessage message = (NetworkMessage) ois.readObject();
            RemoteDeviceNode node = latchedDevices.get(message.deviceId);
            if (node != null) {
                node.updateTelemetry(message.stateProbabilities, message.entropy, message.salience);
            }
        } catch (Exception e) {
            // Drop corrupt frame sequence gracefully
        }
    }

    private void evictDeadPerimeterNodes() {
        while (isRunning) {
            try {
                Thread.sleep(5000);
                long current = System.currentTimeMillis();
                // Evict devices that haven't sent a telemetry window signal within 15 seconds
                latchedDevices.entrySet().removeIf(entry -> (current - entry.getValue().lastSeenTimestamp) > 15000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    public Map<String, RemoteDeviceNode> getLatchedDevices() {
        return latchedDevices;
    }

    public void stopEngine() {
        this.isRunning = false;
        if (multicastSocket != null) multicastSocket.close();
        if (tcpServerSocket != null) {
            try { tcpServerSocket.close(); } catch (Exception e) { /* ignored */ }
        }
        networkPool.shutdownNow();
    }
}
