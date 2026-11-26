import java.net.InetAddress;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class SubnetDiscoveryEngine {
    
    // Modify this base IP to match your local network's subnet (e.g., 192.168.1)
    private static final String SUBNET_BASE = "192.168.1";
    private static final int TIMEOUT_MS = 1500;

    public static void main(String[] args) {
        System.out.println("INITIATING LAN DEVICE DISCOVERY ON: " + SUBNET_BASE + ".x");
        System.out.println("POOLING COMPUTE RESOURCES...\n");

        ExecutorService executor = Executors.newFixedThreadPool(50);

        for (int i = 1; i <= 254; i++) {
            final int nodeIndex = i;
            executor.submit(() -> checkNodeAvailability(nodeIndex));
        }

        executor.shutdown();
        try {
            executor.awaitTermination(2, TimeUnit.MINUTES);
            System.out.println("\nDISCOVERY LOOP END: 01.CRACK * *");
        } catch (InterruptedException e) {
            System.err.println("Discovery interrupted: " + e.getMessage());
        }
    }

    private static void checkNodeAvailability(int nodeIndex) {
        String targetIp = SUBNET_BASE + "." + nodeIndex;
        try {
            InetAddress address = InetAddress.getByName(targetIp);
            if (address.isReachable(TIMEOUT_MS)) {
                String hostName = address.getHostName();
                System.out.println("[ACTIVE NODE FOUND] IP: " + targetIp + " | Host: " + hostName);
            }
        } catch (Exception e) {
            // Node unresponsive; suppress output to keep datastream clean
        }
    }
}