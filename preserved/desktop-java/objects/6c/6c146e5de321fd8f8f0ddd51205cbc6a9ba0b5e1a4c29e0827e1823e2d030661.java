import java.io.Serializable;
import java.util.UUID;

/**
 * 1-0 TRUTH PARITY SPECIFICATION: EPHEMERAL DATA VECTOR STRUCT
 * Captures transient transaction tokens securely using structural binary status limits.
 */
public class VolatileUnit implements Serializable {
    private static final long serialVersionUID = 88111L;
    
    private final String txId;
    private final String label; // "LOCAL_CHIPS", "CLOUD_GATEWAY"
    private final int bit;      // 0 = Ground State, 1 = Active Processing Lane
    private final long nano;
    private double drift;

    public VolatileUnit(String label, int bit, double drift) {
        this.txId = "TX-" + UUID.randomUUID().toString().substring(0, 6).toUpperCase();
        this.label = label;
        this.bit = (bit == 1) ? 1 : 0;
        this.nano = System.nanoTime();
        this.drift = Math.min(1.0, Math.max(0.0, drift));
    }

    public void tick(double clockBaseline) {
        // High-precision oscillation simulation using built-in system clock markers
        double waveInterval = Math.sin(System.nanoTime() * 1e-9 * clockBaseline);
        this.drift += waveInterval * 0.005;
        if (this.drift > 1.0) this.drift = 1.0;
        if (this.drift < 0.0) this.drift = 0.0;
    }

    public String getTxId() { return txId; }
    public String getLabel() { return label; }
    public int getBit() { return bit; }
    public long getNano() { return nano; }
    public double getDrift() { return drift; }
}
