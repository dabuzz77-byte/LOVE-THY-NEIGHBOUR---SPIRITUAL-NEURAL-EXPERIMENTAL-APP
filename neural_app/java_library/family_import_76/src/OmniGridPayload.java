import neural.studio.*;
import java.io.Serializable;
import java.util.Arrays;
import java.util.UUID;

/**
 * Serializable data payload passing through the active network grid bus.
 * Captures structural binary matrix topologies and alignment signals.
 */
public class OmniGridPayload implements Serializable {
    private static final long serialVersionUID = 783L; // Substrate resonance identifier

    private final UUID footprintId;
    private final String transmissionSource;
    private final boolean[][] matrixTopology;
    private final long nanoTimestamp;
    private final boolean virtuePassSignal;

    public OmniGridPayload(String source, boolean[][] matrix, boolean virtuePass) {
        this.footprintId = UUID.randomUUID();
        this.transmissionSource = source;
        // Strict defensive copy to ensure cross-process logic immutability
        this.matrixTopology = Arrays.stream(matrix)
                                    .map(boolean[]::clone)
                                    .toArray(boolean[][]::new);
        this.nanoTimestamp = System.nanoTime();
        this.virtuePassSignal = virtuePass;
    }

    public UUID getFootprintId() { return footprintId; }
    public String getTransmissionSource() { return transmissionSource; }
    public boolean[][] getMatrixTopology() { return matrixTopology; }
    public long getNanoTimestamp() { return nanoTimestamp; }
    public boolean isVirtuePassSignal() { return virtuePassSignal; }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("=== GRID PAYLOAD [#%s] FROM: %s ===\n", 
                footprintId.toString().substring(0, 8), transmissionSource));
        sb.append(String.format("VIRTUEPASS ACTIVE: %s | TIMESTAMP: %d ns\n", virtuePassSignal, nanoTimestamp));
        for (boolean[] row : matrixTopology) {
            for (boolean cell : row) {
                sb.append(cell ? "1 " : "0 ");
            }
            sb.append("\n");
        }
        return sb.toString();
    }
}
