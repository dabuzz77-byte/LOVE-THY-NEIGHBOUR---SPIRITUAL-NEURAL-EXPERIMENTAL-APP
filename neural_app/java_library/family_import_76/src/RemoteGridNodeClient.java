import neural.studio.*;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.net.Socket;

/**
 * Simulates a distinct execution context running elsewhere on the network grid,
 * dispatching complex matrix telemetry sequences into the active orchestration bus.
 */
public class RemoteGridNodeClient {
    private final String targetHost;
    private final int targetPort;
    private final String nodeIdentifier;

    public RemoteGridNodeClient(String host, int port, String identifier) {
        this.targetHost = host;
        this.targetPort = port;
        this.nodeIdentifier = identifier;
    }

    public void transmitPayload(boolean[][] matrix, boolean triggerVirtuePass) {
        try (Socket socket = new Socket(targetHost, targetPort);
             ObjectOutputStream oos = new ObjectOutputStream(socket.getOutputStream())) {
            
            OmniGridPayload payload = new OmniGridPayload(nodeIdentifier, matrix, triggerVirtuePass);
            oos.writeObject(payload);
            oos.flush();
            
        } catch (IOException e) {
            System.err.printf("[CLIENT ERROR] Remote transit tracking failed from node '%s': %s%n", 
                    nodeIdentifier, e.getMessage());
        }
    }
}
