import neural.studio.*;
import java.awt.Color;
import java.util.UUID;

/**
 * BI-TER-ALLSTATE SYSTEM: MULTI-FILE CODE ENGINE
 * Part 1: Structures transactional capital metrics across the network.
 */
public class FinancialTransaction {
    private final String transactionId;
    private final String accountClass; // "PERSONAL_ASSET", "SYSTEMIC_DEBT", "UNIVERSAL_EQUITY"
    private final double locationGridX;
    private final double locationGridY;
    private final double fiatValueUSD;
    private final Color spectralAssetColor;
    private double virtueParityWeight;

    public FinancialTransaction(String accountClass, double x, double y, double fiatValue, double initialParity) {
        this.transactionId = "TX-" + UUID.randomUUID().toString().substring(0, 6).toUpperCase();
        this.accountClass = accountClass;
        this.locationGridX = x;
        this.locationGridY = y;
        this.fiatValueUSD = fiatValue;
        this.virtueParityWeight = initialParity;

        switch (accountClass) {
            case "PERSONAL_ASSET":
                this.spectralAssetColor = new Color(0, 255, 190, 220); // Mint Green
                break;
            case "SYSTEMIC_DEBT":
                this.spectralAssetColor = new Color(255, 70, 70, 220);   // Transmutation Crimson
                break;
            default:
                this.spectralAssetColor = new Color(0, 160, 255, 220);  // Sapphire Balance
                break;
        }
    }

    public void balanceAssetResonance(double systemClockFrequency) {
        double waveVariance = Math.sin(System.currentTimeMillis() * 0.001 * systemClockFrequency);
        this.virtueParityWeight += waveVariance * 0.015;
        if (this.virtueParityWeight > 1.0) this.virtueParityWeight = 1.0;
        if (this.virtueParityWeight < 0.0) this.virtueParityWeight = 0.0;
    }

    public String getTransactionId() { return transactionId; }
    public String getAccountClass() { return accountClass; }
    public double getX() { return locationGridX; }
    public double getY() { return locationGridY; }
    public double getValue() { return fiatValueUSD; }
    public Color getColor() { return spectralAssetColor; }
    public double getVirtueIndex() { return virtueParityWeight; }
}
