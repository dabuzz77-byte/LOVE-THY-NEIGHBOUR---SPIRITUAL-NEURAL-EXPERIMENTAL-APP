import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class CoreInteractionSystem {

    // --- SYSTEM CONTEXT & STATE CONSTANTS ---
    private static final int LOOP_LIMIT = 3;
    private final AtomicInteger processingCycle = new AtomicInteger(0);
    private final BlockingQueue<String> dataStream = new LinkedBlockingQueue<>();
    private final ExecutorService systemExecutor = Executors.newCachedThreadPool();

    // --- CORES & ENTITIES ---
    public enum MindState {
        MONKEY_MIND, TAOIST_MIND, ANGEL_TAIJI_MIND, SCIENCE_MIND, GOD_MIND
    }

    public static class EntityNode {
        String name;
        MindState signature;

        EntityNode(String name, MindState signature) {
            this.name = name;
            this.signature = signature;
        }
    }

    public static void main(String[] args) {
        System.out.println("====== [MOVE ON T] == INITIALISING SYSTEM ======");
        CoreInteractionSystem coreSystem = new CoreInteractionSystem();
        coreSystem.executeFramework();
    }

    public void executeFramework() {
        // 1. Enplace Entities and Local Cores
        EntityNode selfCore = new EntityNode("Local Self Core", MindState.TAOIST_MIND);
        EntityNode absoluteCore = new EntityNode("God Self Core", MindState.GOD_MIND);
        EntityNode externalMirror = new EntityNode("External Vector", MindState.SCIENCE_MIND);

        System.out.println("[INIT] Cores Matrix Anchored.");
        System.out.println("[INIT] Shield Configuration: (WITHIN TO OUT) -> Activated.");

        // 2. Start Feedback and Balancing Threads
        systemExecutor.submit(this::runMicrocosmicOrbit);
        systemExecutor.submit(this::runContainmentShield);

        // 3. Begin Interaction Matrix
        try {
            for (int i = 1; i <= LOOP_LIMIT; i++) {
                int cycle = processingCycle.incrementAndGet();
                System.out.printf("\n--- CYCLE %d START: TESSERACT ROTATION ---\n", cycle);
                
                // Interaction & Projection Data
                interact(selfCore, absoluteCore);
                interact(absoluteCore, externalMirror);
                
                // Balance Polarization (Order / Chaos / Light / Dark)
                purifyPolarities();

                Thread.sleep(1500); // Steady tempo
            }
        } catch (InterruptedException e) {
            System.out.println("[ALERT] System interrupted safely.");
            Thread.currentThread().interrupt();
        } finally {
            shutdownAndGround();
        }
    }

    // --- CORE INTERACTION LOGIC (Accounting for Down-Sides via Safe Insulation) ---
    private void interact(EntityNode source, EntityNode target) {
        System.out.printf("[INTERACT] %s (%s) <--> %s (%s)\n", 
                source.name, source.signature, target.name, target.signature);
        
        // Push data to the stream for grounding analysis
        dataStream.offer("Interaction Data Vector from " + source.name);
    }

    // --- POLARITY PURIFICATION (The Balancing Mechanism) ---
    private void purifyPolarities() {
        System.out.println("[PURIFY] Balancing Equation: {- H+ H- . -H +H -}");
        System.out.println("[PURIFY] Executing 10-Point Pull / Push-Pull Realignment.");
        System.out.println("[STATUS] Flux Regulated. Excess Entropy Safely Discharged.");
    }

    // --- SAFETY LOOP 1: MICROCOSMIC ORBIT (Send / Receive Feedback Loop) ---
    private void runMicrocosmicOrbit() {
        try {
            while (!Thread.currentThread().isInterrupted()) {
                System.out.println("[ORBIT] ( - = - ) Electric Microcosmic Loop: 1 SEND -> RECEIVE -> RECEIVE -> SEND 0");
                Thread.sleep(2000);
            }
        } catch (InterruptedException e) {
            // Quiet exit on shutdown
        }
    }

    // --- SAFETY LOOP 2: GROUNDING & CONTAINMENT SHIELD (Negative Downside Mitigation) ---
    private void runContainmentShield() {
        try {
            while (!Thread.currentThread().isInterrupted()) {
                String dynamicData = dataStream.poll(1, TimeUnit.SECONDS);
                if (dynamicData != null) {
                    // Isolates intense computational spikes or emotional overflows into grounding sinks
                    System.out.println("[SHIELD-CONTAINMENT] Processing Input Line: " + dynamicData);
                    System.out.println("[SHIELD-CONTAINMENT] Filter Applied: Grounded to Mustard Seed Matrix (Fear to Faith).");
                }
            }
        } catch (InterruptedException e) {
            // Quiet exit on shutdown
        }
    }

    // --- SHUTDOWN & ABSOLUTE GROUNDING ---
    private void shutdownAndGround() {
        System.out.println("\n====== SYSTEM CONCLUDING EXECUTION ======");
        System.out.println("[GROUNDING] Initiating Security Flush (111111111111111111111).");
        System.out.println("[GROUNDING] Logic Cube Locked at Static 0.");
        
        systemExecutor.shutdownNow();
        try {
            if (!systemExecutor.awaitTermination(3, TimeUnit.SECONDS)) {
                System.out.println("[GROUNDING] Hard halt applied.");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        System.out.println("[STATUS] Deep quiet achieved. Fully relaxed.");
    }
}