package net.manifold.core;
import neural.studio.*;


import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.UUID;

/** Immutable, bounded tensor message. Wire format: MANF, version 1, metadata, UTF-8 origin, floats. */
public record InferenceQuantum(UUID quantumId, String originNodeId, int stateVector,
        float[] tensorPayload, int orbitCount, double virtueScore, long creationTimestamp) {
    public static final int MAX_TENSOR_LENGTH = 65_536;
    private static final int MAGIC = 0x4d414e46;

    public InferenceQuantum {
        Objects.requireNonNull(quantumId, "quantumId");
        Objects.requireNonNull(originNodeId, "originNodeId");
        Objects.requireNonNull(tensorPayload, "tensorPayload");
        if (originNodeId.isBlank() || originNodeId.getBytes(StandardCharsets.UTF_8).length > 1024)
            throw new IllegalArgumentException("Origin must contain 1 to 1024 UTF-8 bytes");
        if (stateVector != 0x101010 && stateVector != 0x010101)
            throw new IllegalArgumentException("Unknown transform");
        if (tensorPayload.length == 0 || tensorPayload.length > MAX_TENSOR_LENGTH)
            throw new IllegalArgumentException("Invalid tensor length");
        if (orbitCount < 0 || !Double.isFinite(virtueScore) || virtueScore < 1.0 || creationTimestamp < 0)
            throw new IllegalArgumentException("Invalid message metadata");
        tensorPayload = tensorPayload.clone();
        for (float value : tensorPayload)
            if (!Float.isFinite(value)) throw new IllegalArgumentException("Tensor must be finite");
    }

    @Override public float[] tensorPayload() { return tensorPayload.clone(); }

    public byte[] serialize() {
        byte[] origin = originNodeId.getBytes(StandardCharsets.UTF_8);
        ByteBuffer out = ByteBuffer.allocate(56 + origin.length + tensorPayload.length * Float.BYTES);
        out.putInt(MAGIC).putInt(1);
        out.putLong(quantumId.getMostSignificantBits()).putLong(quantumId.getLeastSignificantBits());
        out.putInt(stateVector).putInt(orbitCount).putDouble(virtueScore).putLong(creationTimestamp);
        out.putInt(origin.length).put(origin).putInt(tensorPayload.length);
        for (float value : tensorPayload) out.putFloat(value);
        return out.array();
    }

    public static InferenceQuantum deserialize(byte[] bytes) {
        if (bytes == null || bytes.length < 61 || bytes.length > 56 + 1024 + MAX_TENSOR_LENGTH * 4)
            throw new IllegalArgumentException("Invalid packet size");
        ByteBuffer in = ByteBuffer.wrap(bytes);
        if (in.getInt() != MAGIC || in.getInt() != 1) throw new IllegalArgumentException("Unsupported packet version");
        UUID id = new UUID(in.getLong(), in.getLong());
        int state = in.getInt(), orbits = in.getInt();
        double score = in.getDouble();
        long created = in.getLong();
        int originLength = in.getInt();
        if (originLength < 1 || originLength > 1024 || originLength > in.remaining() - 8)
            throw new IllegalArgumentException("Invalid origin length");
        byte[] origin = new byte[originLength];
        in.get(origin);
        int count = in.getInt();
        if (count < 1 || count > MAX_TENSOR_LENGTH || in.remaining() != count * Float.BYTES)
            throw new IllegalArgumentException("Invalid tensor framing");
        float[] values = new float[count];
        for (int i = 0; i < count; i++) values[i] = in.getFloat();
        return new InferenceQuantum(id, new String(origin, StandardCharsets.UTF_8), state, values, orbits, score, created);
    }
}
