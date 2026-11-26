import neural.studio.*;
import java.util.UUID;

/**
 * Immutable data structure representing a real-time transactional event
 * passing through global financial grid coordinates.
 */
public record MarketPayload(
    UUID transactionId,
    String assetTicker,
    double volumeUSD,
    double asymmetricConcentrationIndex, // Scale 0.0 to 1.0 (Asymmetric corporate capture)
    double communityFloorImpact,        // Scale -1.0 to +1.0 (Impact on socio-economic floor)
    long executionTimestamp
) {
    public static MarketPayload generateMockTransmission(String ticker) {
        double vol = 10_000 + (Math.random() * 4_990_000);
        double concentration = Math.random();
        // Artificially couple high concentration with negative base floor impacts to simulate extraction
        double floorImpact = (concentration > 0.7) ? (-0.2 - (Math.random() * 0.6)) : (Math.random() * 0.5);
        
        return new MarketPayload(
            UUID.randomUUID(),
            ticker,
            vol,
            concentration,
            floorImpact,
            System.currentTimeMillis()
        );
    }
}
