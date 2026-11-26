/**
 * Stateful data registry managing volatile system memory balances.
 */
public class RecallLedgerRegistry {
    private double alchemicalBalanceFloorGBP = 250000.00;
    private static final double CALIBRATED_SUSTENANCE_INCREMENT = 100.00;

    public synchronized double getAlchemicalBalanceFloorGBP() {
        return alchemicalBalanceFloorGBP;
    }

    public synchronized void applyCalibratedLift() {
        this.alchemicalBalanceFloorGBP += CALIBRATED_SUSTENANCE_INCREMENT;
    }
}
