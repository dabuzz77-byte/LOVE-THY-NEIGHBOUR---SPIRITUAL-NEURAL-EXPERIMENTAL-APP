import neural.studio.*;
import java.io.Serializable;
import java.util.UUID;

/**
 * Concrete immutable transaction payload routing across physical grid endpoints.
 * Captures raw transaction volumes alongside systemic extraction variables.
 */
public final class GridTransactionPayload implements Serializable {
    private static final long serialVersionUID = 7831002L;

    private final UUID transactionId;
    private final String sourceEndpointId;
    private final double transactionalVolumeUSD;
    private final double asymmetricExtractionIndex; // Scale: 0.0 to 1.0 (Asymmetric corporate capture)
    private final double localSocioEconomicFloor;     // Scale: -1.0 to 1.0 (Socio-economic impact)
    private final long entryTimestampNano;

    public GridTransactionPayload(String endpoint, double volume, double extraction, double floor) {
        this.transactionId = UUID.randomUUID();
        this.sourceEndpointId = endpoint;
        this.transactionalVolumeUSD = volume;
        this.asymmetricExtractionIndex = extraction;
        this.localSocioEconomicFloor = floor;
        this.entryTimestampNano = System.nanoTime();
    }

    public UUID getTransactionId() { return transactionId; }
    public String getSourceEndpointId() { return sourceEndpointId; }
    public double getTransactionalVolumeUSD() { return transactionalVolumeUSD; }
    public double getAsymmetricExtractionIndex() { return asymmetricExtractionIndex; }
    public double getLocalSocioEconomicFloor() { return localSocioEconomicFloor; }
    public long getEntryTimestampNano() { return entryTimestampNano; }
}
