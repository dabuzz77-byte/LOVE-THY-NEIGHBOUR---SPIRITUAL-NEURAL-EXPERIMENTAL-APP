import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Advanced Cryptographic Pattern and Opposite Factor Flux Transformer.
 * Handles bit-level inversion passes cleanly without external infrastructure dependencies.
 */
public class InversionRegistry {

    /**
     * Calculates a deterministic SHA-256 state fingerprint across text parameters.
     */
    public static String calculateStateHash(String sourceInput) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] encodedHash = digest.digest(sourceInput.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            
            for (byte b : encodedHash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            return hexString.toString().toUpperCase();
        } catch (Exception e) {
            return "HASH_FAULT_DETECTION_METRIC";
        }
    }

    /**
     * Computes the absolute opposite factor flux bitwise logical complement of a hash string.
     */
    public static String computeOppositeFactorFlux(String cryptographicHash) {
        try {
            byte[] rawBytes = cryptographicHash.getBytes(StandardCharsets.UTF_8);
            byte[] invertedResult = new byte[Math.min(rawBytes.length, 12)]; // Bound width safely
            
            for (int i = 0; i < invertedResult.length; i++) {
                invertedResult[i] = (byte) (~rawBytes[i] & 0xFF);
            }
            
            StringBuilder sb = new StringBuilder();
            for (byte b : invertedResult) {
                sb.append(String.format("%02X", b));
            }
            return sb.toString();
        } catch (Exception e) {
            return "FLUX_INVERSION_RESTRICTION_ERROR";
        }
    }
}
