import neural.studio.*;
import java.util.Arrays;

/** Deterministic signal normalization. The historical name does not imply quantum hardware. */
public final class QuantumTernaryBinaryCore {
    private final double threshold;
    private final double[] probabilities;
    private final int[] binary;
    private final int[] ternary;
    private double entropy;

    public QuantumTernaryBinaryCore(int qubitCount, double threshold) {
        if (qubitCount < 1 || qubitCount > 10 || !Double.isFinite(threshold) || threshold < 0 || threshold > 1)
            throw new IllegalArgumentException("Use 1-10 dimension bits and a threshold in [0, 1]");
        this.threshold = threshold;
        probabilities = new double[1 << qubitCount];
        binary = new int[probabilities.length];
        ternary = new int[probabilities.length];
        processQuantumState(new double[0]);
    }

    public synchronized void processQuantumState(double[] metrics) {
        if (metrics == null) throw new IllegalArgumentException("Metrics are required");
        double max = 0;
        for (int i = 0; i < probabilities.length; i++) {
            probabilities[i] = i < metrics.length && Double.isFinite(metrics[i]) ? Math.abs(metrics[i]) : 0;
            max = Math.max(max, probabilities[i]);
        }
        double sum = 0;
        if (max > 0) {
            for (int i = 0; i < probabilities.length; i++) {
                double scaled = probabilities[i] / max;
                probabilities[i] = scaled * scaled;
                sum += probabilities[i];
            }
        }
        if (sum == 0) Arrays.fill(probabilities, 1.0 / probabilities.length);
        else for (int i = 0; i < probabilities.length; i++) probabilities[i] /= sum;
        entropy = 0;
        double mean = 1.0 / probabilities.length;
        for (int i = 0; i < probabilities.length; i++) {
            double p = probabilities[i];
            ternary[i] = p > mean * (1 + threshold) ? 1 : p < mean * (1 - threshold) ? -1 : 0;
            binary[i] = ternary[i] == 1 ? 1 : 0;
            if (p > 0) entropy -= p * Math.log(p) / Math.log(2);
        }
    }

    public synchronized double[] getProbabilities() { return probabilities.clone(); }
    public synchronized int[] getBinaryStream() { return binary.clone(); }
    public synchronized int[] getTernaryStream() { return ternary.clone(); }
    public synchronized double getEntropy() { return entropy; }
}

