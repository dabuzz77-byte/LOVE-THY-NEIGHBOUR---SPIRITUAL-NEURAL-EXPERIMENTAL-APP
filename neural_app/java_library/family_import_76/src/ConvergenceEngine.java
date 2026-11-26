import neural.studio.*;
/**
 * Block 4: Mathematical analyzer calculating global convergence values,
 * systemic divergence thresholds, and manifold coherence indexes.
 */
public class ConvergenceEngine {
    private final ParallelManifoldRegistry targetRegistry;
    private final double baseTuningFrequency;

    public ConvergenceEngine(ParallelManifoldRegistry registry, double tuningFreq) {
        this.targetRegistry = registry;
        this.baseTuningFrequency = tuningFreq;
    }

    public double computeSystemicVariance() {
        double absoluteVarianceAccumulator = 0.0;
        int activeTracks = targetRegistry.getDimensionRangeLimit();

        for (int i = 0; i < activeTracks; i++) {
            ManifoldToken token = targetRegistry.readDimension(i);
            if (token != null) {
                // Compound variance formula integrating velocity deviations against baseline scalar values
                double localDeviation = Math.abs(token.getTrajectoryVelocity()) * (baseTuningFrequency / 7.83);
                absoluteVarianceAccumulator += localDeviation;
            }
        }
        return absoluteVarianceAccumulator / activeTracks;
    }

    public double calculateCoherencePercentage(double currentVariance) {
        // Converts mathematical divergence into a standard 0% to 100% stability scale
        double calculatedStability = 100.0 - (currentVariance * 2.5);
        return Math.max(0.0, Math.min(100.0, calculatedStability));
    }
}
