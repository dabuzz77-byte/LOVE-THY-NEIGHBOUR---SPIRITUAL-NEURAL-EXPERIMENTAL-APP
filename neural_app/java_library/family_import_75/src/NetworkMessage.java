import neural.studio.*;
import java.io.Serializable;

/**
 * STRIPED NETWORK DATA PRIMITIVE
 * Serializes local platform telemetry across network nodes.
 */
public class NetworkMessage implements Serializable {
    private static final long serialVersionUID = 44109263851L;

    public String platformType; // "ANDROID" or "IOS"
    public String deviceId;
    public double[] stateProbabilities;
    public double entropy;
    public double salience;

    public NetworkMessage(String platformType, String deviceId, double[] stateProbabilities, double entropy, double salience) {
        this.platformType = platformType;
        this.deviceId = deviceId;
        this.stateProbabilities = stateProbabilities;
        this.entropy = entropy;
        this.salience = salience;
    }
}
