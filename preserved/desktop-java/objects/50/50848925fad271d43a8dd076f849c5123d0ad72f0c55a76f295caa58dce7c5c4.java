import java.util.ArrayList;
import java.util.List;

/**
 * Background loop processor bound to the 7.83 Hz Schumann harmonic cadence clock.
 */
public class CadenceClockService implements Runnable {

    private final double targetFrequencyHz = 7.83;
    private final CultivationBusLauncher masterLauncher;
    private final List<TraditionModule> telemetryRegistry = new ArrayList<>();
    private volatile boolean isClockRunning = true;

    public CadenceClockService(CultivationBusLauncher launcher) {
        this.masterLauncher = launcher;
        // Ingesting comparative traditions into the safe learning matrix footprint
        telemetryRegistry.add(new TraditionModule("Gepchak_Yoga_Heat", "Tummo inner fire generation", "Eastern_Tibet", "Universal Compassion"));
        telemetryRegistry.add(new TraditionModule("Zen_Introspection", "Zazen silent cushion meditation", "Kyoto_Outpost", "Mind Nature Recognition"));
        telemetryRegistry.add(new TraditionModule("Vedic_Pranayama", "Nadi Shodhana alternate breath", "Varanasi_Core", "Internal Energy Taming"));
    }

    public void stopClock() {
        this.isClockRunning = false;
    }

    @Override
    public void run() {
        long executionSteps = 0;

        while (isClockRunning) {
            try {
                executionSteps++;
                if (telemetryRegistry.isEmpty()) continue;

                TraditionModule activeTradition = telemetryRegistry.get((int)(executionSteps % telemetryRegistry.size()));
                
                // Ter-Binary State Calculation Shift Logic [Bit 1, 0, -1]
                int stateSelector = (int)(executionSteps % 3);
                int stateBit = (stateSelector == 1) ? 1 : ((stateSelector == 2) ? 0 : -1);
                String statusString = (stateBit == 1) ? "SOVEREIGN_VIRTUE_PASS" : 
                                      ((stateBit == 0) ? "VACUUM_SUPPRESSED_GROUND" : "PREDATORY_NOISE_REJECT");

                // Execute a calibrated increment lift when the tradition matches core compassions
                if (stateBit == 1 && activeTradition.alignsWithCompassion()) {
                    masterLauncher.applyCalibratedAdjustment();
                }

                // Render compiled data rows out straight onto terminal console buffers
                TelemetrySnapshot progressFrame = new TelemetrySnapshot(
                        activeTradition.getTraditionName(),
                        stateBit,
                        statusString + " | Root Metric: " + activeTradition.getCoreEthicalMetric(),
                        masterLauncher.getAlchemicalBalanceFloorGBP()
                );
                
                progressFrame.emitConsoleLog();
                System.out.println();

                // Latency frame maps exactly to the 7.83 Hz harmonic clock phase (~127 milliseconds)
                Thread.sleep((long) (1000 / targetFrequencyHz));

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
}
