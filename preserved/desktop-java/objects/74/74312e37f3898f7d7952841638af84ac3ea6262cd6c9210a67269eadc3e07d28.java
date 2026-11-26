import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * BI-TER-ALLSTATE SYSTEM: MULTI-FILE CODE ENGINE
 * Part 2: Manages the volatile memory bus and balances global network alignment index.
 */
public class InferenceClearingHouse {
    private final List<FinancialTransaction> ledgerCache;
    private final Random marketEntropySource;
    private final double referenceFrequency = 7.83; 
    private double networkRestitutionIndex = 1.0;

    public InferenceClearingHouse() {
        this.ledgerCache = new ArrayList<>();
        this.marketEntropySource = new Random();
        seedPrimaryClearingNodes();
    }

    private void seedPrimaryClearingNodes() {
        ledgerCache.add(new FinancialTransaction("UNIVERSAL_EQUITY", 640, 350, 1000000.0, 1.0));
        ledgerCache.add(new FinancialTransaction("SYSTEMIC_DEBT", 380, 220, 450000.0, 0.33));
        ledgerCache.add(new FinancialTransaction("PERSONAL_ASSET", 820, 500, 85000.0, 0.85));
    }

    public synchronized void processLedgerPipeline() {
        double combinedVirtueScore = 0;

        for (FinancialTransaction tx : ledgerCache) {
            tx.balanceAssetResonance(referenceFrequency);
            combinedVirtueScore += tx.getVirtueIndex();
        }

        if (!ledgerCache.isEmpty()) {
            this.networkRestitutionIndex = combinedVirtueScore / ledgerCache.size();
        }

        if (marketEntropySource.nextDouble() > 0.94 && ledgerCache.size() < 35) {
            String[] classes = {"PERSONAL_ASSET", "SYSTEMIC_DEBT", "UNIVERSAL_EQUITY"};
            String chosenClass = classes[marketEntropySource.nextInt(classes.length)];
            ledgerCache.add(new FinancialTransaction(
                chosenClass,
                80 + marketEntropySource.nextInt(1000),
                60 + marketEntropySource.nextInt(500),
                500 + marketEntropySource.nextDouble() * 250000,
                marketEntropySource.nextDouble()
            ));
        }

        if (ledgerCache.size() > 28) {
            ledgerCache.remove(3); 
        }
    }

    public synchronized List<FinancialTransaction> getLedgerCache() {
        return new ArrayList<>(ledgerCache);
    }

    public double getNetworkRestitutionIndex() {
        return networkRestitutionIndex;
    }
}
