import neural.studio.*;
import java.io.Serializable;

/** Legacy Java wire format. New mobile clients should use the documented LAN1 text protocol. */
public class NetworkMessage implements Serializable {
    private static final long serialVersionUID = 44109263851L;
    public String platformType;
    public String deviceId;
    public double[] stateProbabilities;
    public double entropy;
    public double salience;

    public NetworkMessage(String platformType, String deviceId, double[] probabilities, double entropy, double salience) {
        this.platformType = platformType;
        this.deviceId = deviceId;
        stateProbabilities = probabilities == null ? null : probabilities.clone();
        this.entropy = entropy;
        this.salience = salience;
    }
}

