import neural.studio.*;
/**
 * Domain entity mapping a spiritual tradition for comparative analysis.
 * Standalone package-free compilation unit.
 */
public class TraditionModule {
    private final String traditionName;
    private final String primaryPractice;
    private final String geographyNode;
    private final String coreEthicalMetric;

    public TraditionModule(String name, String practice, String geography, String metric) {
        this.traditionName = name;
        this.primaryPractice = practice;
        this.geographyNode = geography;
        this.coreEthicalMetric = metric;
    }

    public String getTraditionName() { return traditionName; }
    public String getPrimaryPractice() { return primaryPractice; }
    public String getGeographyNode() { return geographyNode; }
    public String getCoreEthicalMetric() { return coreEthicalMetric; }

    public boolean alignsWithCompassion() {
        return this.coreEthicalMetric != null && this.coreEthicalMetric.toLowerCase().contains("compassion");
    }
}
