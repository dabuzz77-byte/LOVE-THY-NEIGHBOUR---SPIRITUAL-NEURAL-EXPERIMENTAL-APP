import neural.studio.*;
import java.io.Serializable;
import java.util.UUID;

/**
 * Immutable domain entity representing a high-magnitude asset transaction 
 * entering the infrastructure gateway.
 */
public final class AssetTransaction implements Serializable {
    private static final long serialVersionUID = 7831009L;

    private final UUID transactionId;
    private final String sourceNodeIdentifier;
    private final double proposedYieldUSD;
    private final double asymmetricCaptureIndex; // Scale 0.0 to 1.0 (Capital concentration weight)
    private final double localizedFloorImpact;    // Scale -1.0 to +1.0 (Impact on human baseline)

    public AssetTransaction(String sourceNode, double yield, double captureIndex, double floorImpact) {
        this.transactionId = UUID.randomUUID();
        this.sourceNodeIdentifier = sourceNode;
        this.proposedYieldUSD = yield;
        this.asymmetricCaptureIndex = captureIndex;
        this.localizedFloorImpact = floorImpact;
    }

    public UUID getTransactionId() { return transactionId; }
    public String getSourceNodeIdentifier() { return sourceNodeIdentifier; }
    public double getProposedYieldUSD() { return proposedYieldUSD; }
    public double getAsymmetricCaptureIndex() { return asymmetricCaptureIndex; }
    public double getLocalizedFloorImpact() { return localizedFloorImpact; }
}
