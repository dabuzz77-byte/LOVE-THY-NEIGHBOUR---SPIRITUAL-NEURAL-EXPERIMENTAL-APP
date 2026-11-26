import neural.studio.*;
import java.io.Serializable;
import java.util.Arrays;
import java.util.UUID;

/**
 * Immutable structural frame capturing streaming matrix data,
 * transaction metadata, and identity validation baselines.
 */
public final class FluxPayload implements Serializable {
    private static final long serialVersionUID = 7831010L;

    private final UUID transactionId;
    private final long processingTimestamp;
    private final boolean[][] binaryMatrix;
    private final boolean alignmentPassActive;

    public FluxPayload(boolean[][] sourceMatrix, boolean alignmentPassActive) {
        this.transactionId = UUID.randomUUID();
        this.processingTimestamp = System.nanoTime();
        this.alignmentPassActive = alignmentPassActive;
        // Strict defensive array copy to maintain data security boundaries
        this.binaryMatrix = Arrays.stream(sourceMatrix)
                                  .map(boolean[]::clone)
                                  .toArray(boolean[][]::new);
    }

    public UUID getTransactionId() { return transactionId; }
    public long getProcessingTimestamp() { return processingTimestamp; }
    public boolean[][] getBinaryMatrix() { return binaryMatrix; }
    public boolean isAlignmentPassActive() { return alignmentPassActive; }
}
