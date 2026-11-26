import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Defines the structural data substrate and network coordinate maps 
 * spanning from Local Nodes up to Deepmind core clusters.
 */
public class NetworkTopology {
    public enum LayerType { LOCAL_USER_EDGE, REGIONAL_BACKBONE, DEEPMIND_CORE }

    public static record VectorCoordinate(int x, int y, int z) {}

    public static class TopologyNode {
        public final UUID nodeUid;
        public final String identityLabel;
        public final LayerType layer;
        public final VectorCoordinate coordinate;
        private double baselineFloorValue;
        private double processingVelocity;

        public TopologyNode(String label, LayerType layer, VectorCoordinate coord, double floor, double velocity) {
            this.nodeUid = UUID.randomUUID();
            this.identityLabel = label;
            this.layer = layer;
            this.coordinate = coord;
            this.baselineFloorValue = floor;
            this.processingVelocity = velocity;
        }

        public synchronized void mutateState(double floor, double velocity) {
            this.baselineFloorValue = floor;
            this.processingVelocity = velocity;
        }

        public synchronized double getBaselineFloorValue() { return baselineFloorValue; }
        public synchronized double getProcessingVelocity() { return processingVelocity; }
    }

    public static class RoutingVector {
        public final TopologyNode source;
        public final TopologyNode destination;
        public final double bandwidthCapacity;

        public RoutingVector(TopologyNode src, TopologyNode dest, double capacity) {
            this.source = src;
            this.destination = dest;
            this.bandwidthCapacity = capacity;
        }
    }

    private final ConcurrentHashMap<UUID, TopologyNode> nodes = new ConcurrentHashMap<>();
    private final List<RoutingVector> vectors = new ArrayList<>();

    public void addNode(TopologyNode node) {
        nodes.put(node.nodeUid, node);
    }

    public void linkNodes(TopologyNode src, TopologyNode dest, double capacity) {
        vectors.add(new RoutingVector(src, dest, capacity));
    }

    public List<TopologyNode> getNodes() { return new ArrayList<>(nodes.values()); }
    public List<RoutingVector> getVectors() { return new ArrayList<>(vectors); }
}
