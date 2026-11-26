package com.system.core.model;

import java.io.Serializable;
import java.util.Arrays;
import java.util.UUID;

/**
 * Immutable data transfer object capturing variable multi-dimensional telemetry matrices,
 * unique tracking IDs, and logical identity baseline status flags.
 */
public final class TopographyPayload implements Serializable {
    private static final long serialVersionUID = 78320261L;

    private final UUID transactionId;
    private final String originIdentifier;
    private final boolean[][] dataStateGrid;
    private final double conflictCoefficient; // Scale: 0.0 to 1.0 (Structural friction metric)
    private final long processingTimestampNano;

    public TopographyPayload(String origin, boolean[][] sourceGrid, double conflictMetric) {
        this.transactionId = UUID.randomUUID();
        this.originIdentifier = origin;
        this.conflictCoefficient = conflictMetric;
        this.processingTimestampNano = System.nanoTime();
        
        // Strict defensive matrix copying to preserve cross-thread data boundaries
        this.dataStateGrid = Arrays.stream(sourceGrid)
                                   .map(boolean[]::clone)
                                   .toArray(boolean[][]::new);
    }

    public UUID getTransactionId() { return transactionId; }
    public String getOriginIdentifier() { return originIdentifier; }
    public boolean[][] getDataStateGrid() { return dataStateGrid; }
    public double getConflictCoefficient() { return conflictCoefficient; }
    public long getProcessingTimestampNano() { return processingTimestampNano; }
}
