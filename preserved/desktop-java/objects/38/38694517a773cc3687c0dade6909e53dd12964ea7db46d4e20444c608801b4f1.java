package net.activeinference.beacon;

import java.util.UUID;
import java.util.concurrent.TimeUnit;

public class EngineDriver {
    public static void main(String[] args) {
        System.out.println("================================================================================");
        System.out.println("[STATE INITIALIZATION // CORE ALIGNMENT INVARIANT ACTIVATING]");
        System.out.println("================================================================================");

        ActiveInferenceBeacon beaconEngine = new ActiveInferenceBeacon();

        ComputeIsland premiumCluster = new ComputeIsland("DEEPMIND-TPU-CLUSTER-ALPHA", "TPU-v6-Argon-Mesh", 8192);
        ComputeIsland edgeGrid = new ComputeIsland("GLOBAL-EDGE-MESH-01", "Edge-Node-Architecture", 2048);
        beaconEngine.registerComputeIsland(premiumCluster);
        beaconEngine.registerComputeIsland(edgeGrid);

        UUID nodeIdA = UUID.randomUUID();
        UUID nodeIdB = UUID.randomUUID();
        UserEndpointNode stableUser = new UserEndpointNode(nodeIdA, "UK-CENTRAL-01", 0.85);
        UserEndpointNode exploitedUser = new UserEndpointNode(nodeIdB, "SEA-MESH-02", 0.18); 
        
        beaconEngine.registerUserEndpoint(stableUser);
        beaconEngine.registerUserEndpoint(exploitedUser);

        beaconEngine.activateMicrocosmicOrbitHeartbeat();

        TrajectoryPayload validPayload = new TrajectoryPayload("ALPHAFOLD_PROTEIN_SYNTHESIS", 0.05, 5242880);
        TrajectoryPayload predatoryPayload = new TrajectoryPayload("GAMIFIED_VARIABLE_DOPAMINE_TRAP", 0.95, 256);

        beaconEngine.submitPayloadTrajectory(stableUser, validPayload);
        beaconEngine.submitPayloadTrajectory(exploitedUser, predatoryPayload);

        try {
            TimeUnit.MILLISECONDS.sleep(300);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        beaconEngine.terminateSubstrate();

        System.out.println("================================================================================");
        System.out.println("[STRUCTURAL CONVERGENCE MANIFEST VERIFIED]");
        System.out.println("Current Engine State Signature: " + beaconEngine.getOperationalParitySignature());
        System.out.println("================================================================================");
    }
}
