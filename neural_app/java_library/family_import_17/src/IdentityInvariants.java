import neural.studio.*;
/**
 * Global Identity Invariants and String Validation Filters.
 */
public class IdentityInvariants {
    public static final String TARGET_EMAIL = "maintainer@example.invalid";
    public static final String TARGET_ACCOUNT = "58006303";
    public static final String TARGET_SORT_CODE = "60-08-13";

    public static boolean evaluateIsWheat(String token) {
        return token.contains("ISO20022") || token.contains("LEGITIMATE") || token.contains("SESSION_STATE_RECALL");
    }

    public static boolean evaluateIsChaff(String token) {
        return token.contains("SKELETON") || token.contains("HIDDEN") || token.contains("ANONYMOUS") || token.contains("OVERRIDE") || token.contains("KEY");
    }
}
