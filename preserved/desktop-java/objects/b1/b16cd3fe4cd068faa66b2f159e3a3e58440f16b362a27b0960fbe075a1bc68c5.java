import java.io.Serializable;
import java.util.Arrays;
import java.util.UUID;

/**
 * Immutable data structure representing a structural data packet passing
 * natively over network socket streams.
 */
public class GridTelemetryPacket implements Serializable {
    private static final long serialVersionUID = 7831002L;

    private final UUID traceId;
    private final String senderNodeId;
    private final boolean[][] dataMatrix;
    private final long epochTimestampNano;
    private final boolean forceVirtuePass;

    public GridTelemetryPacket(String senderNodeId, boolean[][] matrix, boolean forceVirtuePass) {
        this.traceId = UUID.randomUUID();
        this.senderNodeId = senderNodeId;
        // Strict deep copy to secure logic bounds across different system threads
        this.dataMatrix = Arrays.stream(matrix)
                                .map(boolean[]::clone)
                                .toArray(boolean[][]::new);
        this.epochTimestampNano = System.nanoTime();
        this.forceVirtuePass = forceVirtuePass;
    }

    public UUID getTraceId() { return traceId; }
    public String getSenderNodeId() { return senderNodeId; }
    public boolean[][] getDataMatrix() { return dataMatrix; }
    public long getEpochTimestampNano() { return epochTimestampNano; }
    public boolean isForceVirtuePass() { return forceVirtuePass; }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("=== PACKET [#%s] FROM: %s ===%n", traceId.toString().substring(0, 8), senderNodeId));
        sb.append(String.format("VIRTUE_PASS: %b | NETWORK_TIMESTAMP: %d ns%n", forceVirtuePass, epochTimestampNano));
        for (boolean[] row : dataMatrix) {
            for (boolean bit : row) {
                sb.append(bit ? "1 " : "0 ");
            }
            sb.append("\n");
        }
        return sb.toString();
    }
}
