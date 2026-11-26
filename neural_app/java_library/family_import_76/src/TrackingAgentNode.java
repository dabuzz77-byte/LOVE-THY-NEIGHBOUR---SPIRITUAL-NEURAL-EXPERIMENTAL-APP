import neural.studio.*;
import java.util.Random;

/**
 * Block 8: Autonomous edge tracking component evaluating environmental vectors
 * and executing self-selecting convergence loops onto data structures.
 */
public class TrackingAgentNode {
    private final String structuralId;
    private double positionalX, positionalY;
    private double velocityX, velocityY;
    private FluxGridCell targetedGridCellReference = null;
    private final Random internalRandom = new Random();

    public TrackingAgentNode(String elementId, int spawnX, int spawnY) {
        this.structuralId = elementId;
        this.positionalX = spawnX;
        this.positionalY = spawnY;
        this.velocityX = (internalRandom.nextDouble() - 0.5) * 60.0;
        this.velocityY = (internalRandom.nextDouble() - 0.5) * 60.0;
    }

    public void updateDriftPattern(double timeDelta, int fieldWidth, int fieldHeight) {
        this.positionalX += velocityX * timeDelta;
        this.positionalY += velocityY * timeDelta;

        // Containment wall redirection mechanics
        if (positionalX < 300 || positionalX > fieldWidth - 50)  this.velocityX *= -1.0;
        if (positionalY < 50  || positionalY > fieldHeight - 150) this.velocityY *= -1.0;
    }

    public void linkToTargetCell(FluxGridCell targetCell) {
        this.targetedGridCellReference = targetCell;
    }

    public String getStructuralId() { return structuralId; }
    public int getPositionX() { return (int) positionalX; }
    public int getPositionY() { return (int) positionalY; }
    public FluxGridCell getTargetedGridCellReference() { return targetedGridCellReference; }
}
