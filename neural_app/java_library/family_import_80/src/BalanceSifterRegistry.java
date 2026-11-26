import neural.studio.*;
/**
 * Core Sifting Logic Matrix.
 * Differentiates legitimate traceable fields from anonymous variant strings.
 */
public class BalanceSifterRegistry {

    /**
     * Inspects an incoming text payload against strict compliance rule invariants.
     */
    public static boolean checkIsWheat(String cleanInputToken) {
        return cleanInputToken.contains("ISO20022") 
            || cleanInputToken.contains("LEGITIMATE") 
            || cleanInputToken.contains("RESTITUTION");
    }

    /**
     * Inspects an incoming text payload to isolate high-variance or unauthorized override vectors.
     */
    public static boolean checkIsChaff(String cleanInputToken) {
        return cleanInputToken.contains("SKELETON") 
            || cleanInputToken.contains("HIDDEN") 
            || cleanInputToken.contains("ANONYMOUS") 
            || cleanInputToken.contains("OVERRIDE") 
            || cleanInputToken.contains("KEY");
    }
}
