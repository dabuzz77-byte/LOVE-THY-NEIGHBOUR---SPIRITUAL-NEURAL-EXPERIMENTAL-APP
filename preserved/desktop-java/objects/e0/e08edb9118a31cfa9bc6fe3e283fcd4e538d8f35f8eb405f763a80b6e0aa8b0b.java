import java.io.Serializable;

/**
 * MODULE 1: TRANSIENT ACCOUNT PARAMETER SPECIFICATION
 * Encapsulates the runtime identifiers safely within volatile memory caches.
 */
public class AuditAccountSpec implements Serializable {
    private static final long serialVersionUID = 783783999L;

    private final String maskedAccountLabel;
    private final long verificationTimestampMillis;
    private String explicitTargetString;

    public AuditAccountSpec(String targetIdentifier) {
        this.explicitTargetString = targetIdentifier != null ? targetIdentifier.trim() : "";
        this.verificationTimestampMillis = System.currentTimeMillis();
        
        // Enforce strict masking boundaries to protect structural values in logs
        if (this.explicitTargetString.length() > 6) {
            this.maskedAccountLabel = "AUDIT-ID-..." + this.explicitTargetString.substring(this.explicitTargetString.length() - 5);
        } else {
            this.maskedAccountLabel = "AUDIT-ID-DEFAULT";
        }
    }

    public synchronized void updateTargetString(String updatedTarget) {
        this.explicitTargetString = updatedTarget != null ? updatedTarget.trim() : "";
    }

    public synchronized String getExplicitTargetString() {
        return this.explicitTargetString;
    }

    public String getMaskedAccountLabel() {
        return this.maskedAccountLabel;
    }

    public long getVerificationTimestampMillis() {
        return this.verificationTimestampMillis;
    }
}
