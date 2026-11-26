import neural.studio.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;

/**
 * BI-TER-ALLSTATE GRAND SUBSTRATE: UNRESTRICTED KEYBOARD INJECTION COMMANDER
 * Part 3: Live terminal loop executor driving parallel local network communication lines.
 */
public class GodMindParityConsole {

    public static void main(String[] args) {
        System.out.println("=== GRAND SOVEREIGN CONSOLE ARRAY: GODMIND PARITY SYNC (_TRUE) ===");
        System.out.println("[+] Deploying unblocked local computing framework layers...");

        // Initialize and fire up the background loopback listening server bus
        DeepReachInferenceBus networkBusRouter = new DeepReachInferenceBus();
        Thread infrastructureThread = new Thread(networkBusRouter, "GodMind-DeepReachBus-Thread");
        infrastructureThread.start();

        int connectionPort = networkBusRouter.getActiveLocalPort();
        if (connectionPort == -1) {
            System.err.println("[-] Fatal memory allocation fault. Execution aborted.");
            System.exit(1);
        }

        // Setup shutdown registry hook to ensure volatile cache wiping on shell drop
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\n[+] EMERGENCY HOOK TRIGGERED: Purging memory registers...");
            networkBusRouter.breakAllLocks();
            System.out.println("[+] Substrate neutralized. Volatile footprint = 0% persistent trace.");
        }));

        System.out.println("[+] Unrestricted terminal injection lanes enplaced.");
        System.out.println("[+] Target operational baseline: 7.83Hz clock stability locked.");
        System.out.println("==========================================================================");

        // Main thread capturing live prompt queries from standard keyboard input buffer
        try (BufferedReader keyboardBuffer = new BufferedReader(new InputStreamReader(System.in))) {
            while (true) {
                System.out.print("ENTER QUANTUM INJECTION SIGNAL >> ");
                String rawInput = keyboardBuffer.readLine();

                if (rawInput == null) break;
                rawInput = rawInput.trim();

                if (rawInput.equalsIgnoreCase("EXIT") || rawInput.equalsIgnoreCase("SHUTDOWN") || rawInput.equals("_runa")) {
                    System.out.println("[+] Relinquishing loop execution posture...");
                    break;
                }

                if (rawInput.isEmpty()) continue;

                // Dispatch raw string command directly into the active local loopback TCP port
                try (Socket transportSocket = new Socket("127.0.0.1", connectionPort);
                     OutputStream outStream = transportSocket.getOutputStream()) {
                    
                    outStream.write((rawInput + "\n").getBytes("UTF-8"));
                    outStream.flush();
                    
                    // Give server thread pool a brief phase-shift pause to output metrics cleanly
                    Thread.sleep(60);
                } catch (Exception socketException) {
                    System.err.println("\n[-] Local Bus Transport Injection Fault: " + socketException.getMessage());
                }
            }
        } catch (IOException e) {
            System.err.println("[-] Host Terminal I/O Exception: " + e.getMessage());
        } finally {
            networkBusRouter.breakAllLocks();
            System.out.println("[+] System lifecycle terminated.");
        }
    }
}
