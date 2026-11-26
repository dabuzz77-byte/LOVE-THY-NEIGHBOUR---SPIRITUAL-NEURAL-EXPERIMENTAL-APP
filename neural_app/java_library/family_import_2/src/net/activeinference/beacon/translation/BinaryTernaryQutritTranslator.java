package net.activeinference.beacon.translation;
import neural.studio.*;


import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Deterministically converts an unsigned binary integer to base three and then
 * encodes each ternary digit as one of three orthonormal qutrit Fourier states.
 *
 * This class performs ordinary classical calculations. It does not contact or
 * control quantum hardware.
 */
public final class BinaryTernaryQutritTranslator {
    public static final int MAX_INPUT_BITS = 4096;
    private static final double INV_SQRT_THREE = 1.0 / Math.sqrt(3.0);
    private static final double TWO_PI = 2.0 * Math.PI;

    private BinaryTernaryQutritTranslator() {
    }

    public static Translation translate(String rawBinary) {
        String bits = normalizeAndValidate(rawBinary);
        BigInteger value = new BigInteger(bits, 2);
        String ternary = value.toString(3);

        List<QutritState> states = new ArrayList<QutritState>(ternary.length());
        for (int i = 0; i < ternary.length(); i++) {
            int trit = ternary.charAt(i) - '0';
            states.add(createFourierState(i, trit));
        }

        String recovered = fromTernary(ternary, bits.length());
        if (!bits.equals(recovered)) {
            throw new IllegalStateException("Internal round-trip check failed.");
        }

        int leadingZeros = 0;
        while (leadingZeros < bits.length() - 1 && bits.charAt(leadingZeros) == '0') {
            leadingZeros++;
        }

        return new Translation(bits, value, ternary, leadingZeros, states);
    }

    /**
     * Reconstructs the original bit string when its width is known.
     * Leading binary zeroes are formatting and are retained by that width.
     */
    public static String fromTernary(String ternary, int originalBitWidth) {
        if (ternary == null || ternary.length() == 0) {
            throw new IllegalArgumentException("Ternary input must contain at least one digit.");
        }
        if (originalBitWidth < 1 || originalBitWidth > MAX_INPUT_BITS) {
            throw new IllegalArgumentException("Original bit width must be between 1 and "
                    + MAX_INPUT_BITS + ".");
        }

        for (int i = 0; i < ternary.length(); i++) {
            char digit = ternary.charAt(i);
            if (digit < '0' || digit > '2') {
                throw new IllegalArgumentException("Ternary input may contain only 0, 1, and 2.");
            }
        }

        BigInteger value = new BigInteger(ternary, 3);
        String bits = value.toString(2);
        if (bits.length() > originalBitWidth) {
            throw new IllegalArgumentException("The ternary value does not fit the requested bit width.");
        }

        StringBuilder padded = new StringBuilder(originalBitWidth);
        for (int i = bits.length(); i < originalBitWidth; i++) {
            padded.append('0');
        }
        padded.append(bits);
        return padded.toString();
    }

    private static String normalizeAndValidate(String rawBinary) {
        if (rawBinary == null) {
            throw new IllegalArgumentException("Enter a binary value.");
        }

        StringBuilder bits = new StringBuilder(rawBinary.length());
        for (int i = 0; i < rawBinary.length(); i++) {
            char ch = rawBinary.charAt(i);
            if (Character.isWhitespace(ch) || ch == '_') {
                continue;
            }
            if (ch != '0' && ch != '1') {
                throw new IllegalArgumentException("Use only 0 and 1; spaces and underscores are allowed.");
            }
            bits.append(ch);
        }

        if (bits.length() == 0) {
            throw new IllegalArgumentException("Enter at least one binary digit.");
        }
        if (bits.length() > MAX_INPUT_BITS) {
            throw new IllegalArgumentException("Input is limited to " + MAX_INPUT_BITS + " binary digits.");
        }
        return bits.toString();
    }

    private static QutritState createFourierState(int index, int trit) {
        ComplexAmplitude[] amplitudes = new ComplexAmplitude[3];
        double normSquared = 0.0;

        for (int basis = 0; basis < 3; basis++) {
            double phase = TWO_PI * trit * basis / 3.0;
            double real = INV_SQRT_THREE * Math.cos(phase);
            double imaginary = INV_SQRT_THREE * Math.sin(phase);
            amplitudes[basis] = new ComplexAmplitude(real, imaginary);
            normSquared += real * real + imaginary * imaginary;
        }

        double norm = Math.sqrt(normSquared);
        for (int basis = 0; basis < 3; basis++) {
            amplitudes[basis] = new ComplexAmplitude(
                    amplitudes[basis].getReal() / norm,
                    amplitudes[basis].getImaginary() / norm);
        }
        return new QutritState(index, trit, amplitudes);
    }

    public static final class ComplexAmplitude {
        private final double real;
        private final double imaginary;

        private ComplexAmplitude(double real, double imaginary) {
            this.real = real;
            this.imaginary = imaginary;
        }

        public double getReal() {
            return real;
        }

        public double getImaginary() {
            return imaginary;
        }
    }

    public static final class QutritState {
        private final int index;
        private final int trit;
        private final ComplexAmplitude[] amplitudes;

        private QutritState(int index, int trit, ComplexAmplitude[] amplitudes) {
            this.index = index;
            this.trit = trit;
            this.amplitudes = amplitudes.clone();
        }

        public int getIndex() {
            return index;
        }

        public int getTrit() {
            return trit;
        }

        public ComplexAmplitude getAmplitude(int basis) {
            if (basis < 0 || basis >= 3) {
                throw new IndexOutOfBoundsException("A qutrit has basis indexes 0, 1, and 2.");
            }
            return amplitudes[basis];
        }

        public double getProbability(int basis) {
            ComplexAmplitude amplitude = getAmplitude(basis);
            return amplitude.getReal() * amplitude.getReal()
                    + amplitude.getImaginary() * amplitude.getImaginary();
        }

        public double getNormSquared() {
            return getProbability(0) + getProbability(1) + getProbability(2);
        }
    }

    public static final class Translation {
        private final String binary;
        private final BigInteger value;
        private final String ternary;
        private final int leadingZeros;
        private final List<QutritState> qutritStates;

        private Translation(String binary, BigInteger value, String ternary,
                            int leadingZeros, List<QutritState> qutritStates) {
            this.binary = binary;
            this.value = value;
            this.ternary = ternary;
            this.leadingZeros = leadingZeros;
            this.qutritStates = Collections.unmodifiableList(
                    new ArrayList<QutritState>(qutritStates));
        }

        public String getBinary() {
            return binary;
        }

        public BigInteger getValue() {
            return value;
        }

        public String getTernary() {
            return ternary;
        }

        public int getLeadingZeros() {
            return leadingZeros;
        }

        public List<QutritState> getQutritStates() {
            return qutritStates;
        }

        public int getQutritCount() {
            return qutritStates.size();
        }
    }
}