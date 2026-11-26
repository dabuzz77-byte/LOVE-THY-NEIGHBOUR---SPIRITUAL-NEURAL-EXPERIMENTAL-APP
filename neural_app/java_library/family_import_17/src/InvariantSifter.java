import neural.studio.*;
/**
 * Cryptographic sifting matrix used to parse data ingress parameters.
 * Validates text properties strictly under a Ter-Binary logic layout.
 */
public class InvariantSifter {

    public static boolean verifyIsWheat(String lowerToken) {
        return lowerToken.contains("iso20022") 
            || lowerToken.contains("legitimate") 
            || lowerToken.contains("compassion") 
            || lowerToken.contains("magic_heat");
    }

    public static boolean verifyIsChaff(String lowerToken) {
        return lowerToken.contains("skeleton") 
            || lowerToken.contains("bypass") 
            || lowerToken.contains("override") 
            || lowerToken.contains("extractive") 
            || lowerToken.contains("harvest");
    }
}
