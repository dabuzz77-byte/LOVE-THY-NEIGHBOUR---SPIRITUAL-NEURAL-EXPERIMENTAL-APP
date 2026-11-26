package net.manifold.crypto;
import neural.studio.*;


import net.manifold.core.InferenceQuantum;
import java.nio.ByteBuffer;
import java.security.SecureRandom;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Authenticated packet codec; validation does not claim to authenticate a network peer's identity. */
public final class CryptographicConvergenceGate {
    private final SecureRandom random = new SecureRandom();

    public byte[] encrypt(InferenceQuantum quantum, SecretKey key) throws Exception {
        byte[] iv = new byte[12];
        random.nextBytes(iv);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));
        byte[] encrypted = cipher.doFinal(quantum.serialize());
        return ByteBuffer.allocate(iv.length + encrypted.length).put(iv).put(encrypted).array();
    }

    public InferenceQuantum convergeStream(byte[] packet, SecretKey key) throws Exception {
        if (packet == null || packet.length < 89 || packet.length > 56 + 1024 + InferenceQuantum.MAX_TENSOR_LENGTH * 4 + 28)
            throw new SecurityException("Invalid encrypted packet size");
        ByteBuffer wrapper = ByteBuffer.wrap(packet);
        byte[] iv = new byte[12];
        wrapper.get(iv);
        byte[] encrypted = new byte[wrapper.remaining()];
        wrapper.get(encrypted);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));
        InferenceQuantum quantum = InferenceQuantum.deserialize(cipher.doFinal(encrypted));
        long now = System.currentTimeMillis();
        if (quantum.creationTimestamp() < now - 60_000 || quantum.creationTimestamp() > now + 60_000)
            throw new SecurityException("Packet timestamp outside the accepted window");
        return quantum;
    }
}
