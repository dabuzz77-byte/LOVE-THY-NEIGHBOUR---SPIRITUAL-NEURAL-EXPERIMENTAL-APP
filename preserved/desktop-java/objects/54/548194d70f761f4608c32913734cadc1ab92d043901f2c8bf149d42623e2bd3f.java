import java.util.Random;

/**
 * CORE ARITHMETIC CORE: DATA DE-QUANTISATION
 */
public class QuantumTernaryBinaryCore {
    private final int qubitCount;
    private final int targetStateDimensions;
    private final double logicTernaryGatingThreshold;
    private final double[] probabilities;
    private final int[] ternaryVectorStream;
    private final int[] binaryVectorStream;
    private double executionEntropy = 0.0;

    public QuantumTernaryBinaryCore(int qubitCount, double logicTernaryGatingThreshold) {
        this.qubitCount = qubitCount;
        this.targetStateDimensions = 1 << qubitCount;
        this.logicTernaryGatingThreshold = logicTernaryGatingThreshold;
        this.probabilities = new double[targetStateDimensions];
        this.ternaryVectorStream = new int[targetStateDimensions];
        this.binaryVectorStream = new int[targetStateDimensions];
    }

    public synchronized void processQuantumState(double[] rawTelemetryMetrics) {
        double aggregateVectorMagnitude = 0.0;
        
        for (int i = 0; i < targetStateDimensions; i++) {
            double linearInputSeed = (i < rawTelemetryMetrics.length) ? rawTelemetryMetrics[i] : Math.sin(i * 0.45);
            probabilities[i] = Math.pow(Math.abs(Math.sin(linearInputSeed + (System.currentTimeMillis() * 0.0015))), 2);
            aggregateVectorMagnitude += probabilities[i];
        }
        
        double probabilisticMean = 0.0;
        for (int i = 0; i < targetStateDimensions; i++) {
            probabilities[i] /= (aggregateVectorMagnitude == 0.0 ? 1.0 : aggregateVectorMagnitude);
            probabilisticMean += probabilities[i];
        }
        probabilisticMean /= targetStateDimensions;

        double localEntropyCalculation = 0.0;
        for (int i = 0; i < targetStateDimensions; i++) {
            double statisticalVariance = probabilities[i] - probabilisticMean;
            
            if (statisticalVariance > logicTernaryGatingThreshold / targetStateDimensions) {
                ternaryVectorStream[i] = 1;
                binaryVectorStream[i] = 1;
            } else if (statisticalVariance < -logicTernaryGatingThreshold / targetStateDimensions) {
                ternaryVectorStream[i] = -1;
                binaryVectorStream[i] = 0;
            } else {
                ternaryVectorStream[i] = 0;
                binaryVectorStream[i] = 0;
            }
            
            if (probabilities[i] > 0.0) {
                localEntropyCalculation -= probabilities[i] * (Math.log(probabilities[i]) / Math.log(2.0));
            }
        }
        this.executionEntropy = localEntropyCalculation;
    }

    public double[] getProbabilities() { return probabilities; }
    public int[] getBinaryStream() { return binaryVectorStream; }
    public int[] getLastBinaryStream() { return binaryVectorStream; }
    public double getEntropy() { return executionEntropy; }

    public String getBinarySampleString() {
        StringBuilder outputSample = new StringBuilder();
        for (int i = 0; i < Math.min(12, binaryVectorStream.length); i++) {
            outputSample.append(binaryVectorStream[i]);
        }
        return outputSample.toString();
    }
}
