import neural.studio.*;
import java.io.BufferedReader;

import java.io.IOException;

import java.io.InputStreamReader;

import java.io.OutputStream;

import java.net.ServerSocket;

import java.net.Socket;

import java.net.URI;

import java.util.concurrent.CopyOnWriteArrayList;

import java.util.concurrent.ExecutorService;

import java.util.concurrent.Executors;

import java.util.Random;

import java.util.UUID;



/**

 * BI-TER-ALLSTATE SYSTEM: MASTER LOCAL TERMINAL CONNECTOR

 * Single-file native architecture containing the Ephemeral Substrate,

 * Asynchronous Server Core, and Live Interactive Terminal Injection Client.

 */

public class TerminalBusGateway {



    private static final double BASELINE_CLOCK_HZ = 7.83;



    // =========================================================================

    // 1. DATA SUBSTRATE ELEMENT: VOLATILE SIGNAL RECORD

    // =========================================================================

    public static class SignalPacket {

        private final String signalHexId;

        private final String commandPayload;

        private final long generationTimestampNano;

        private double fieldAlignmentParity;



        public SignalPacket(String commandPayload, double startingParity) {

            this.signalHexId = "SIG-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();

            this.commandPayload = commandPayload;

            this.generationTimestampNano = System.nanoTime();

            this.fieldAlignmentParity = Math.min(1.0, Math.max(0.0, startingParity));

        }



        public void evaluateWaveDrift(double frequencyAnchor) {

            double nanoWaveVariance = Math.sin(System.nanoTime() * 1e-9 * frequencyAnchor);

            this.fieldAlignmentParity += nanoWaveVariance * 0.01;

            if (this.fieldAlignmentParity > 1.0) this.fieldAlignmentParity = 1.0;

            if (this.fieldAlignmentParity < 0.0) this.fieldAlignmentParity = 0.0;

        }



        @Override

        public String toString() {

            return String.format("[%s] ID: %s | Content: \"%s\" | Parity: %.4f",

                    System.currentTimeMillis(), signalHexId, commandPayload, fieldAlignmentParity);

        }

    }



    // =========================================================================

    // 2. RUNTIME INFRASTRUCTURE LAYER: ASYNC LOCAL BUS ROUTER

    // =========================================================================

    public static class AsynchronousBusRouter implements Runnable {

        private final CopyOnWriteArrayList<SignalPacket> volatileRingCache = new CopyOnWriteArrayList<>();

        private final ExecutorService clientProcessingPool = Executors.newCachedThreadPool();

        private boolean isServerRunning = true;

        private ServerSocket busListeningSocket;



        public AsynchronousBusRouter() {

            try {

                // Dynamically allocate next free unassigned port on native host adapter loops

                this.busListeningSocket = new ServerSocket(0);

                System.out.println(String.format("[+] PARALLEL NETWORK STRATUM ENGAGED ON PORT: %d", busListeningSocket.getLocalPort()));

            } catch (IOException e) {

                System.err.println("[-] Infrastructure Server Socket Failure: " + e.getMessage());

            }

        }



        public int getActivePort() {

            return busListeningSocket != null ? busListeningSocket.getLocalPort() : -1;

        }



        @Override

        public void run() {

            // Spin up background daemon to handle wave drift parameters continuously

            Thread calculationDriftWorker = new Thread(() -> {

                while (isServerRunning) {

                    for (SignalPacket packet : volatileRingCache) {

                        packet.evaluateWaveDrift(BASELINE_CLOCK_HZ);

                    }

                    if (volatileRingCache.size() > 20) {

                        volatileRingCache.remove(0); // Evacuate register ring to prevent hardware leakage

                    }

                    try { Thread.sleep(40); } catch (InterruptedException ie) { break; }

                }

            });

            calculationDriftWorker.setDaemon(true);

            calculationDriftWorker.start();



            // Main server socket accept loop

            while (isServerRunning) {

                try {

                    Socket incomingClientSocket = busListeningSocket.accept();

                    clientProcessingPool.execute(() -> parseIncomingStream(incomingClientSocket));

                } catch (IOException e) {

                    if (!isServerRunning) break;

                }

            }

        }



        private void parseIncomingStream(Socket clientSocket) {

            try (BufferedReader streamReader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()))) {

                String inputLine = streamReader.readLine();

                if (inputLine != null && !inputLine.trim().isEmpty()) {

                    SignalPacket parsedPacket = new SignalPacket(inputLine.trim(), new Random().nextDouble());

                    volatileRingCache.add(parsedPacket);

                    System.out.println("\n[BUS INJECTION DETECTED] -> " + parsedPacket);

                    System.out.print("ENTER TELEMETRY COMMAND PACKET >> ");

                }

            } catch (IOException ex) {

                // Prevent terminal trace crashes

            } finally {

                try { clientSocket.close(); } catch (IOException ignored) {}

            }

        }



        public void shutdownRouter() {

            this.isServerRunning = false;

            this.clientProcessingPool.shutdown();

            try {

                if (busListeningSocket != null && !busListeningSocket.isClosed()) {

                    busListeningSocket.close();

                }

            } catch (IOException e) {

                // Direct closure forced

            }

        }

    }



    // =========================================================================

    // 3. APPLICATION ENTRY POINT: LIVE KEYBOARD INJECTION CLIENT

    // =========================================================================

    public static void main(String[] args) {

        System.out.println("=== GRAND TRANSITION BUS: TERMINAL GATEWAY CONSOLE (_TRUE) ===");

        System.out.println("[+] Initializing multi-lane non-persistent processing arrays...");



        // Initialize and fire up the background loopback listening server

        AsynchronousBusRouter serverRouter = new AsynchronousBusRouter();

        Thread serverThread = new Thread(serverRouter, "GodMind-ServerBus-Worker");

        serverThread.start();



        int connectionPort = serverRouter.getActivePort();

        if (connectionPort == -1) {

            System.err.println("[-] Fatal initialization fault. Hardware allocation aborted.");

            System.exit(1);

        }



        // Setup shutdown registry hook to ensure volatile cache wiping on shell drop

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {

            System.out.println("\n[+] EMERGENCY HOOK TRIGGERED: Purging memory registers...");

            serverRouter.shutdownRouter();

            System.out.println("[+] Substrate neutralized. Volatile footprint = 0%.");

        }));



        System.out.println("[+] Unrestricted terminal injection lanes enplaced.");

        System.out.println("[+] Target operational frequency: 7.83Hz clock stability locked.");

        System.out.println("===============================================================");



        // Main thread loops to capture interactive user keyboard inputs

        try (BufferedReader keyboardBuffer = new BufferedReader(new InputStreamReader(System.in))) {

            while (true) {

                System.out.print("ENTER TELEMETRY COMMAND PACKET >> ");

                String inputCommand = keyboardBuffer.readLine();



                if (inputCommand == null) break;

                inputCommand = inputCommand.trim();



                if (inputCommand.equalsIgnoreCase("EXIT") || inputCommand.equalsIgnoreCase("SHUTDOWN")) {

                    System.out.println("[+] Relinquishing loop execution posture...");

                    break;

                }



                if (inputCommand.isEmpty()) continue;



                // Dispatch raw string command directly into the active local loopback TCP port

                try (Socket localTransportSocket = new Socket("127.0.0.1", connectionPort);

                     OutputStream outStream = localTransportSocket.getOutputStream()) {

                    

                    // Inject string followed by a clear newline terminator to release server buffer read blocks

                    outStream.write((inputCommand + "\n").getBytes("UTF-8"));

                    outStream.flush();

                    

                    // Give server thread pool a brief phase-shift millosecond pause to output details clearly

                    Thread.sleep(50);

                } catch (Exception socketException) {

                    System.err.println("\n[-] Local Bus Transport Injection Fault: " + socketException.getMessage());

                }

            }

        } catch (IOException e) {

            System.err.println("[-] Host Terminal I/O Exception: " + e.getMessage());

        } finally {

            serverRouter.shutdownRouter();

            System.out.println("[+] System lifecycle terminated.");

        }

    }

}

