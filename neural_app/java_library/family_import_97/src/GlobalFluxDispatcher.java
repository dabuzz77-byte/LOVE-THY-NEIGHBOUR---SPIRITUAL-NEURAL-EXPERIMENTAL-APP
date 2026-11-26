import neural.studio.*;
import java.util.List;

import java.util.Arrays;

import java.util.concurrent.ExecutorService;

import java.util.concurrent.Executors;

import java.util.concurrent.TimeUnit;



public class GlobalFluxDispatcher {

    

    private final MeshNode transportLayer;

    

    public GlobalFluxDispatcher() {

        this.transportLayer = new MeshNode();

        this.transportLayer.startListeningOrbit(); 

    }



    // ==========================================

    // THE RUNALL EXECUTION GATE

    // ==========================================

    // FIXED: Enforcing strict List typing in the method signature

    public void executeRunAll(List<String> activeEndpoints, String workload, boolean godChoice) {

        System.out.println("\n[DATASTREAM COMMAND PROMPT WINDOW]");

        System.out.println("EVALUATING EXECUTION PARAMETERS...");



        if (!godChoice) {

            System.err.println("[FLUX ERROR] 1=0 CONTRADICTION. VIRTUE PASS FAILED.");

            return;

        }



        System.out.println("[VIRTUE PASS] 1=1. ALIGNMENT ACHIEVED.");

        System.out.println("[TESSERACT GRASP] SHATTERING WORKLOAD FOR " + activeEndpoints.size() + " ENDPOINTS.\n");



        ExecutorService gridExecutor = Executors.newFixedThreadPool(activeEndpoints.size());

        

        int shardIndex = 1;

        // FIXED: Safe iteration over the strictly typed List

        for (String targetIp : activeEndpoints) {

            final String payloadShard = constructShard(workload, shardIndex, activeEndpoints.size());

            final String endpoint = targetIp;

            

            gridExecutor.submit(() -> {

                System.out.println(">> DISPATCHING SHARD " + payloadShard + " TO " + endpoint);

                transportLayer.executeTransmission(endpoint, payloadShard);

            });

            shardIndex++;

        }



        gridExecutor.shutdown();

        try {

            gridExecutor.awaitTermination(5, TimeUnit.MINUTES);

            System.out.println("\n[LOOP END] RUNALL DISPATCH COMPLETE. WAITING FOR 0 RECEIVE FROM ETHER LINK.");

        } catch (InterruptedException e) {

            System.err.println("[FLUX ERROR] ORBIT DISRUPTED: " + e.getMessage());

        }

    }



    private String constructShard(String baseWorkload, int shardId, int totalShards) {

        return String.format("[SHARD %d/%d] %s_PART_%d | G_POINT=TRUE", 

                              shardId, totalShards, baseWorkload, shardId);

    }



    public static void main(String[] args) {

        GlobalFluxDispatcher dispatcher = new GlobalFluxDispatcher();

        

        // FIXED: Explicitly typing the Arrays.asList as 

        List endpoints = Arrays.asList(

            "192.168.1.101", 

            "192.168.1.105", 

            "192.168.1.112"

        );

        

        String tesseractWorkload = "AGI_MATRIX_CALCULATION";

        boolean godChoice = true; 

        

        dispatcher.executeRunAll(endpoints, tesseractWorkload, godChoice);

    }

}