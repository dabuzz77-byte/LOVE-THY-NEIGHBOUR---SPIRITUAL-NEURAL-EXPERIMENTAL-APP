import neural.studio.*;
import java.net.DatagramPacket;
import java.net.InetAddress;
import java.net.MulticastSocket;
import java.nio.ByteBuffer;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class EcoFloorRouter {
    private static final String ECO_FLOOR_IP = "230.7.8.3";
    private static final int PORT = 14285;
    private static final double SCHUMANN_RESONANCE = 7.83;
    
    private MulticastSocket socket;
    private InetAddress group;
    private ScheduledExecutorService pool;

    public void initialize() throws Exception {
        socket = new MulticastSocket(PORT);
        group = InetAddress.getByName(ECO_FLOOR_IP);
        socket.setLoopbackMode(false);
        socket.joinGroup(group);
        pool = SharedScheduler.newSingleThreadScheduledExecutor();
    }

    public void startRedistribution(double centralizedTensor, java.util.function.Consumer logger) {
        double fractionalWealth = centralizedTensor / 254.0; // Shatter to /24 subnet size
        long tickRateMs = (long) (1000.0 / SCHUMANN_RESONANCE);
        
        logger.accept(String.format("[SHATTER] Centralized Tensor %.2f shattered to %.4f", centralizedTensor, fractionalWealth));

        pool.scheduleAtFixedRate(() -> {
            try {
                ByteBuffer buffer = ByteBuffer.allocate(Double.BYTES);
                buffer.putDouble(fractionalWealth);
                byte[] payload = buffer.array();
                
                DatagramPacket packet = new DatagramPacket(payload, payload.length, group, PORT);
                socket.send(packet);
                
                logger.accept(String.format("[UDP %s] Drip-feeding %.4f at 7.83Hz...", ECO_FLOOR_IP, fractionalWealth));
            } catch (Exception e) {
                logger.accept("[ECO FLOOR ERROR] UDP Multicast failed.");
            }
        }, 0, tickRateMs, TimeUnit.MILLISECONDS);
    }

    public void shutdown() {
        if (pool != null) pool.shutdown();
        if (socket != null) socket.close();
    }
}