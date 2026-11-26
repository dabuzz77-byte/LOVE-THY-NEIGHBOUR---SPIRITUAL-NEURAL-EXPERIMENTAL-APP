import java.io.Serializable;

/**
 * MODULE 1: CRYPTOGRAPHIC HANDSHAKE TELEMETRY FRAME
 * Safely wraps authorization strings within volatile variables for transmission checks.
 */
public class SecureCredentialSpec implements Serializable {
    private static final long serialVersionUID = 883784222L;

    private final String maskedDiagnosticLabel;
    private final long timestampAcquisitionMillis;
    private String explicitTokenString;

    public SecureCredentialSpec(String initialToken) {
        this.explicitTokenString = initialToken != null ? initialToken.trim() : "";
        this.timestampAcquisitionMillis = System.currentTimeMillis();
        
        if (this.explicitTokenString.length() > 8) {
            this.maskedDiagnosticLabel = "CORP-AUTH-..." + this.explicitTokenString.substring(this.explicitTokenString.length() - 6);
        } else {
            this.maskedDiagnosticLabel = "CORP-AUTH-EMPTY";
        }
    }

    public synchronized void updateTokenValue(String freshlyInjectedToken) {
        this.explicitTokenString = freshlyInjectedToken != null ? freshlyInjectedToken.trim() : "";
    }

    public synchronized String getExplicitTokenString() {
        return this.explicitTokenString;
    }

    public String getMaskedDiagnosticLabel() {
        return this.maskedDiagnosticLabel;
    }

    public long getTimestampAcquisitionMillis() {
        return this.timestampAcquisitionMillis;
    }
}
