import neural.studio.*;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.net.Socket;

/**
 * Production Client Adapter converting internal configurations into 
 * physical serialized network outputs.
 */
public class ProductionGridClient {
    private final String networkHost;
    private final int networkPort;
    private final String systemNodeLabel;

    public ProductionGridClient(String host, int port, String nodeLabel) {
        this.networkHost = host;
        this.networkPort = port;
        this.systemNodeLabel = nodeLabel;
    }

    /**
     * Serialises and writes the telemetry matrix down the active network connection socket.
     */
    public void transmitMetrics(boolean[][] matrix, boolean activateVirtuePassOverride) {
        try (Socket tcpSocket = new Socket(networkHost, networkPort);
             ObjectOutputStream oos = new ObjectOutputStream(tcpSocket.getOutputStream())) {
            
            GridTelemetryPacket compiledPacket = new GridTelemetryPacket(systemNodeLabel, matrix, activateVirtuePassOverride);
            oos.writeObject(compiledPacket);
            oos.flush();
            
        } catch (IOException e) {
            System.err.printf("[CLIENT NETWORK FAULT] Delivery failed from node '%s': %s%n", 
                    systemNodeLabel, e.getMessage());
        }
    }
}
