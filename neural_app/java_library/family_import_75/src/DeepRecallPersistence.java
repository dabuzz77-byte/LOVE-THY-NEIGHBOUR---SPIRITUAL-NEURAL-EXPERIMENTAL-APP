import neural.studio.*;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;

/**
 * PERSISTENCE CORE: VECTOR STRIPED STORAGE (NIO)
 */
public class DeepRecallPersistence {
    private final File targetDiskFile;
    private long totalCommittedVectors = 0;

    public DeepRecallPersistence(String physicalFilePath) {
        this.targetDiskFile = new File(physicalFilePath);
        if (targetDiskFile.exists()) {
            targetDiskFile.delete(); 
        }
    }

    public void asyncPersistVector(double[] dataVector, double computedSalienceValue) {
        new Thread(() -> {
            try (FileOutputStream streamOutput = new FileOutputStream(targetDiskFile, true);
                 FileChannel writeChannel = streamOutput.getChannel()) {
                
                int structuralAllocationSize = 8 + 4 + (dataVector.length * 8); 
                ByteBuffer transferBuffer = ByteBuffer.allocate(structuralAllocationSize);
                
                transferBuffer.putLong(System.currentTimeMillis());
                transferBuffer.putFloat((float) computedSalienceValue);
                for (double internalElement : dataVector) {
                    transferBuffer.putDouble(internalElement);
                }
                
                transferBuffer.flip();
                writeChannel.write(transferBuffer);
                incrementCommitCounter();
            } catch (IOException dropExecutionException) {
                // Graceful fallback execution path
            }
        }).start();
    }

    private synchronized void incrementCommitCounter() {
        totalCommittedVectors++;
    }

    public synchronized long getWriteCount() {
        return totalCommittedVectors;
    }
}
