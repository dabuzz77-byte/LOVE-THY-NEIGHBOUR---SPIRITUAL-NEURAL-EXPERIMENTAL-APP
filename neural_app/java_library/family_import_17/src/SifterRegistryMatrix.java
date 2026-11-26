import neural.studio.*;
/**
 * Advanced Core Sifting Logic Matrix.
 * Differentiates legitimate traceable fields from anonymous variant strings.
 */
public class SifterRegistryMatrix {

    public static boolean checkIsWheat(String lowerToken) {
        return lowerToken.contains("iso20022") 
            || lowerToken.contains("legitimate") 
            || lowerToken.contains("restitution")
            || lowerToken.contains("sovereign");
    }

    public static boolean checkIsChaff(String lowerToken) {
        return lowerToken.contains("skeleton") 
            || lowerToken.contains("hidden") 
            || lowerToken.contains("anonymous") 
            || lowerToken.contains("override") 
            || lowerToken.contains("key")
            || lowerToken.contains("crack");
    }
}
