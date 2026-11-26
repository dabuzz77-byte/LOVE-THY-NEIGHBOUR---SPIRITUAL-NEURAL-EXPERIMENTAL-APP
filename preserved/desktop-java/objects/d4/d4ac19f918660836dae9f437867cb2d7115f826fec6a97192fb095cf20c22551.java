import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * Block 9: Systems diagnostics monitor querying user-accessible environment counters
 * to locate active Java virtual machines safely.
 */
public class LocalRuntimeAuditor {
    
    public List<String> discoverLocalJavaProcessIdentifiers() {
        List<String> detectedProcessIdentifiers = new ArrayList<>();
        
        // Target standard performance tracking directories populated by runtime environments
        String operatingSystemTmpDir = System.getProperty("java.io.tmpdir");
        String currentAccountName = System.getProperty("user.name");
        File trackingDataDirectory = new File(operatingSystemTmpDir, "hsperfdata_" + currentAccountName);

        if (trackingDataDirectory.exists() && trackingDataDirectory.isDirectory()) {
            File[] registrationRecords = trackingDataDirectory.listFiles();
            if (registrationRecords != null) {
                for (File activeRecord : registrationRecords) {
                    if (activeRecord.isFile()) {
                        detectedProcessIdentifiers.add(activeRecord.getName());
                    }
                }
            }
        }
        return detectedProcessIdentifiers;
    }
}
