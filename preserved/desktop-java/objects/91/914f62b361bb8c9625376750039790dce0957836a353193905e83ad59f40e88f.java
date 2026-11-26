import java.io.Serializable;
import java.util.Arrays;
import java.util.UUID;

/**
 * Immutable structural frame encapsulating binary flux grids, 
 * left/right chiral balance ratios, and time-stamped validation baselines.
 */
public final class ChiralFluxPayload implements Serializable {
    private static final long serialVersionUID = 783783L;

    private final UUID transactionId;
    private final long timestampNano;
    private final boolean[][] fluxMatrix;
    private final double leftChiralPolarization;
    private final double rightChiralPolarization;
    private final boolean paritySynchronized;

    public ChiralFluxPayload(boolean[][] sourceMatrix, double leftChiral, double rightChiral, boolean synced) {
        this.transactionId = UUID.randomUUID();
        this.timestampNano = System.nanoTime();
        this.leftChiralPolarization = leftChiral;
        this.rightChiralPolarization = rightChiral;
        this.paritySynchronized = synced;
        
        // Strict defensive matrix cloning to secure data boundaries across threads
        this.fluxMatrix = Arrays.stream(sourceMatrix)
                                .map(boolean[]::clone)
                                .toArray(boolean[][]::new);
    }

    public UUID getTransactionId() { return transactionId; }
    public long getTimestampNano() { return timestampNano; }
    public boolean[][] getFluxMatrix() { return fluxMatrix; }
    public double getLeftChiralPolarization() { return leftChiralPolarization; }
    public double getRightChiralPolarization() { return rightChiralPolarization; }
    public boolean isParitySynchronized() { return paritySynchronized; }
}
