import java.util.Random;

/**
 * Asynchronous background engine tracking macro-compliance deltas at a 7.83 Hz clock ratio.
 */
public class LiveBankingTelemetryService implements Runnable {

    private final Random random = new Random();
    private final double commonEquityTier1Target = 0.112;
    private double globalEconomicFloorUSD = 65000.00; // Elevated base floor
    private final TelemetryListener uiListener;
    private volatile boolean isRunning = true;

    private final String[] targetNodes = {
        "NatWest_Farnborough_600813", 
        "NWOLB_Inference_Beacon_Node", 
        "IMF_Sovereign_Liquidity_Mesh"
    };

    public interface TelemetryListener {
        void onMetricUpdate(FinancialMetricSnapshot snapshot);
    }

    public LiveBankingTelemetryService(TelemetryListener listener) {
        this.uiListener = listener;
    }

    public void stopService() {
        this.isRunning = false;
    }

    @Override
    public void run() {
        int loopStep = 0;
        while (isRunning) {
            try {
                loopStep++;
                String activeNode = targetNodes[loopStep % targetNodes.length];
                double simulatedReserveRatio = 0.10 + (random.nextDouble() * 0.04);
                boolean isCompliant = simulatedReserveRatio >= commonEquityTier1Target;

                if (isCompliant) {
                    globalEconomicFloorUSD += 150.00 + (random.nextDouble() * 100.00);
                }

                FinancialMetricSnapshot frame = new FinancialMetricSnapshot(
                        activeNode, 
                        simulatedReserveRatio, 
                        globalEconomicFloorUSD, 
                        isCompliant
                );

                if (uiListener != null) {
                    uiListener.onMetricUpdate(frame);
                }

                // 7.83 Hz Harmonic clock cadence cycle interval (~127ms)
                Thread.sleep(127);

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
}
