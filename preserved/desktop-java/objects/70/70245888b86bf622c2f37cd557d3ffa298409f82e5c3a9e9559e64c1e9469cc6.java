import java.io.Serializable;
import java.util.UUID;

/**
 * UNIFIED HARMONIC PROTOCOL: EPHEMERAL DATA VECTOR STRUCT
 * Encapsulates runtime parameters securely inside temporary non-persistent heap memory.
 */
public class VolatileUnit implements Serializable {
    private static final long serialVersionUID = 88111L;
    
    private final String txId;
    private final String label; 
    private final int bit;      
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
