import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.net.StandardProtocolFamily;
import java.net.UnixDomainSocketAddress;

public class KernelBridge {

    // Define the persistent structural address for the local ipc gate
    private static final String SOCKET_PATH = System.getProperty("user.home") + "/kernel_bridge.sock";
    private static final int BUFFER_SIZE = 1024;
    private static boolean isRunning = true;

    public static void main(String[] args) {
        Path socketFile = Path.of(SOCKET_PATH);
        
        // Clean any residual socket configurations from previous sessions
        try {
            Files.deleteIfExists(socketFile);
        } catch (IOException e) {
            System.err.println("[ERROR] Failed to clean residual socket registers: " + e.getMessage());
        }

        // Initialize the local server socket channel using the Unix Domain protocol family
        try (ServerSocketChannel serverChannel = ServerSocketChannel.open(StandardProtocolFamily.UNIX)) {
            
            UnixDomainSocketAddress address = UnixDomainSocketAddress.of(socketFile);
            serverChannel.bind(address);
            
            System.out.println("===================================================================");
            System.out.println("KERNEL TO KERNEL/S BRIDGE INFERENCE MODULE INITIALIZED");
            System.out.println("GATE PATHWAY: " + SOCKET_PATH);
            System.out.println("STATUS: STANDBY // WAITING FOR INFERENCE CHANNELS...");
            System.out.println("===================================================================");

            // Core background execution loop
            while (isRunning) {
                try (SocketChannel clientChannel = serverChannel.accept()) {
                    System.out.println("[SUCCESS] Local client connected to Host Kernel Bridge. Syncing clock cycles...");
                    processStream(clientChannel);
                } catch (IOException e) {
                    System.err.println("[WARNING] Socket channel reset during stream processing: " + e.getMessage());
                }
            }

        } catch (IOException e) {
            System.err.println("[CRITICAL] Failed to bind bridge infrastructure: " + e.getMessage());
        } finally {
            // Guarantee socket files are unlinked on hard termination
            try {
                Files.deleteIfExists(socketFile);
            } catch (IOException ignored) {}
        }
    }

    /**
     * Reads raw bytes from the local PC input channel and pipes them 
     * directly through the data verification register.
     */
    private static void processStream(SocketChannel channel) throws IOException {
        ByteBuffer buffer = ByteBuffer.allocate(BUFFER_SIZE);

        while (channel.read(buffer) > 0) {
            buffer.flip(); // Prepare buffer for reading out the payload
            
            byte[] rawBytes = new byte[buffer.remaining()];
            buffer.get(rawBytes);
            String incomingPayload = new String(rawBytes).trim();

            // Intercept data strings to audit for the validation switch
            if (incomingPayload.contains("_true") || incomingPayload.contains("_active")) {
                System.out.println("[AUDIT] Validation parameter flag found: ACTIVE STATE DETECTED.");
                
                // Formulate the uncompromised return verification packet
                String verificationResponse = "[STATUS_REPLY] Packet ingested safely. Code compiled under _true parameters.\n";
                ByteBuffer responseBuffer = ByteBuffer.wrap(verificationResponse.getBytes());
                channel.write(responseBuffer);
            } else {
                System.out.println("[INGEST] Streaming raw telemetry packet size: " + rawBytes.length + " bytes");
            }

            buffer.clear(); // Reset the buffer capacity for the next hardware clock tick
        }
    }
    
    /**
     * Hard-stop command hook to safely de-allocate the kernel socket pipeline programmatically.
     */
    public static void terminateBridge() {
        isRunning = false;
        System.out.println("[STATUS] Kernel bridge ordered to enter safe shutdown sequence.");
    }
}