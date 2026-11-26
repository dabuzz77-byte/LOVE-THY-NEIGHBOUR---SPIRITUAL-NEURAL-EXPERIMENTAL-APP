    // ==========================================
    // CORE ARITHMETIC CORE: SCHUMANN WAVEFORM GENERATOR
    // ==========================================
    static class SchumannCarrierWaveCore {
        private final double schumannBaseFrequency;
        private final double gatingThreshold;
        private final int internalResolution;
        private final double[] harmonicAmplitudes;
        private final int[] digitalBitStream;
        private double phaseEntropy = 0.0;

        public SchumannCarrierWaveCore(double schumannBaseFrequency, double gatingThreshold) {
            this.schumannBaseFrequency = schumannBaseFrequency;
            this.gatingThreshold = gatingThreshold;
            this.internalResolution = 64; // Mapping dimensions matching hardware node matrices
            this.harmonicAmplitudes = new double[internalResolution];
            this.digitalBitStream = new int[internalResolution];
        }

        public synchronized void computeResonanceHarmonics() {
            double cumulativeMagnitude = 0.0;
            long timestamp = System.currentTimeMillis();
            
            for (int i = 0; i < internalResolution; i++) {
                // Synthesize Schumann Resonances alongside dynamic earth cavity metrics
                double signalWaveValue = Math.sin(i * 0.25 + (timestamp * 0.001 * schumannBaseFrequency));
                double harmonicNoise = Math.cos(i * 0.72 + (timestamp * 0.0003));
                
                harmonicAmplitudes[i] = Math.pow(Math.abs(signalWaveValue + (0.15 * harmonicNoise)), 2.0);
                cumulativeMagnitude += harmonicAmplitudes[i];
            }
            
            double averageMeanAmplitude = 0.0;
            for (int i = 0; i < internalResolution; i++) {
                harmonicAmplitudes[i] /= (cumulativeMagnitude == 0.0 ? 1.0 : cumulativeMagnitude);
                averageMeanAmplitude += harmonicAmplitudes[i];
            }
            averageMeanAmplitude /= internalResolution;

            double localEntropyVector = 0.0;
            for (int i = 0; i < internalResolution; i++) {
                double spatialVariance = harmonicAmplitudes[i] - averageMeanAmplitude;
                
                // Rectification gating pass into clean processing integers
                digitalBitStream[i] = (spatialVariance > (gatingThreshold / internalResolution)) ? 1 : 0;
                
                if (harmonicAmplitudes[i] > 0.0) {
                    localEntropyVector -= harmonicAmplitudes[i] * (Math.log(harmonicAmplitudes[i]) / Math.log(2.0));
                }
            }
            this.phaseEntropy = localEntropyVector;
        }

        public double getBaseFrequency() { return schumannBaseFrequency; }
        public double[] getHarmonicAmplitudes() { return harmonicAmplitudes; }
        public double getPhaseEntropy() { return phaseEntropy; }

        public String getBitStreamSampleString() {
            StringBuilder sampleBuilder = new StringBuilder();
            for (int i = 0; i < Math.min(16, digitalBitStream.length); i++) {
                sampleBuilder.append(digitalBitStream[i]);
            }
            return sampleBuilder.toString();
        }
    }
