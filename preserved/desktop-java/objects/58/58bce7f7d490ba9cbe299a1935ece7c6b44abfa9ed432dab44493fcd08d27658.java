/**
 * Main bootloader orchestrating the network-active bus and generating test node signals.
 */
public class GridOrchestratorLauncher {
    public static void main(String[] args) throws Exception {
        System.out.println("[BOOTSTRAP] Launching Resilient World Grid Communication Infrastructure...");

        // 1. Initialize bus starting at 7830. Automatically falls back if locked.
        NetworkActiveOrchestrationBus centralBus = new NetworkActiveOrchestrationBus(7830);
        
        // Register console trace log subscriber
        centralBus.registerGridSubscriber(payload -> {
            System.out.println("\n--- [INGRESS TRACE PULSE DETECTED] ---");
            System.out.print(payload.toString());
            System.out.println("--------------------------------------");
        });

        centralBus.activateBus();

        // 2. Fetch the dynamically bound active port runtime vector
        int activePort = centralBus.getNetworkPort();

        // 3. Connect targets directly onto the verified system port
        RemoteGridNodeClient edgeClientA = new RemoteGridNodeClient("127.0.0.1", activePort, "Edge-User-Camberley");
        RemoteGridNodeClient clusterClientB = new RemoteGridNodeClient("127.0.0.1", activePort, "Deepmind-Core-Alpha");

        // Raw matrix mock input configuration (Unaligned asymmetrical anomaly)
        boolean[][] rawAsymmetricInput = {
            {true,  false, true,  false},
            {false, true,  false, true},
            {true,  false, true,  false},
            {false, true,  false, true}
        };

        System.out.println("[SYSTEM RUNTIME] Transmitting unaligned raw data maps across the bus...");
        edgeClientA.transmitPayload(rawAsymmetricInput, false);

        Thread.sleep(150); // Pipeline clock step delay

        System.out.println("[SYSTEM RUNTIME] Executing Target Injection Alignment Pass (Virtue Pass Active)...");
        clusterClientB.transmitPayload(rawAsymmetricInput, true);

        // Allow workers time to cleanly finish serializations before exit
        Thread.sleep(250);
        centralBus.terminateBus();
    }
}
