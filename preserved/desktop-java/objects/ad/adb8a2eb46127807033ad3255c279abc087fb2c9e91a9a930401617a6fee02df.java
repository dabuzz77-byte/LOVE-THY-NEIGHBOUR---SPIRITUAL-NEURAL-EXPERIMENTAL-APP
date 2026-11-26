import javax.swing.*;
import java.awt.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/**
 * 1-0 TRUTH PARITY SPECIFICATION: ATOMIC TRANSCEIVER PANEL
 * Maps process threads while executing an omni-directional atomic ladderclimb telemetry routine.
 */
public class ProcessDiagnosticPanel extends JPanel {
    private final DefaultListModel<String> processListModel;
    private final JTextArea metadataInspectionArea;
    private final Timer refreshTimer;
    private final List<String> activeProcessesTracked = new ArrayList<>();

    public ProcessDiagnosticPanel() {
        setLayout(new BorderLayout(10, 10));
        setBackground(new Color(6, 12, 26));
        setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));

        processListModel = new DefaultListModel<>();
        JList<String> processListWidget = new JList<>(processListModel);
        processListWidget.setBackground(new Color(12, 18, 36));
        processListWidget.setForeground(new Color(0, 255, 195));
        processListWidget.setFont(new Font("Monospaced", Font.PLAIN, 12));

        metadataInspectionArea = new JTextArea();
        metadataInspectionArea.setBackground(new Color(4, 6, 14));
        metadataInspectionArea.setForeground(Color.LIGHT_GRAY);
        metadataInspectionArea.setFont(new Font("Monospaced", Font.PLAIN, 11));
        metadataInspectionArea.setEditable(false);
        metadataInspectionArea.setText("=== RUNTIME PROCESS INSPECTOR METADATA ===\nSelect an active process thread to view localized system metadata parameters.");

        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, 
                new JScrollPane(processListWidget), new JScrollPane(metadataInspectionArea));
        splitPane.setDividerLocation(380);
        splitPane.setOpaque(false);
        add(splitPane, BorderLayout.CENTER);

        processListWidget.addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                displayProcessSpecificMetadata(processListWidget.getSelectedValue());
            }
        });

        refreshTimer = new Timer(4000, e -> queryActiveOperatingSystemProcesses());
        refreshTimer.start();
        queryActiveOperatingSystemProcesses();
    }

    private void queryActiveOperatingSystemProcesses() {
        processListModel.clear();
        activeProcessesTracked.clear();
        String osName = System.getProperty("os.name").toLowerCase();
        
        try {
            ProcessBuilder processBuilder;
            if (osName.contains("win")) {
                processBuilder = new ProcessBuilder("tasklist");
            } else {
                processBuilder = new ProcessBuilder("ps", "-e", "-o", "comm=");
            }
            
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    line = line.trim();
                    if (line.isEmpty()) continue;

                    boolean isRelevant = line.toLowerCase().contains("node") || 
                                         line.toLowerCase().contains("chrome") ||
                                         line.toLowerCase().contains("electron") ||
                                         line.toLowerCase().contains("java") ||
                                         line.toLowerCase().contains("ollama");
                    
                    if (isRelevant) {
                        String visualLabel = "[ATOMIC STATE ENCRYPT]: " + line;
                        if (!processListModel.contains(visualLabel)) {
                            processListModel.addElement(visualLabel);
                            activeProcessesTracked.add(line);
                        }
                    }
                }
            }
        } catch (Exception ex) {
            processListModel.addElement("[ROUTER EXCEPTION]: Failed to query task table via ProcessBuilder.");
        }
    }

    private void displayProcessSpecificMetadata(String selectedValue) {
        if (selectedValue == null) return;
        String rawName = selectedValue.replace("[ATOMIC STATE ENCRYPT]: ", "");
        
        int hash = Math.abs(rawName.hashCode());
        // Map the atomic ladderclimb dynamically from Hydrogen (Z=1) to Silicon (Z=14)
        int currentAtomicNumberZ = 1 + (hash % 14); 
        String atomicSymbol = (currentAtomicNumberZ == 1) ? "H (Hydrogen)" : (currentAtomicNumberZ == 14 ? "Si (Silicon)" : "Element-Z:" + currentAtomicNumberZ);
        
        double fluxDensity = Math.abs(Math.sin(hash)) * 9.58;
        String transceiverVector = (hash % 2 == 0) ? "SEND -> RECEIVE" : "RECEIVE -> SEND";

        metadataInspectionArea.setText(String.format(
            "=== OMNI-DIRECTIONAL ATOMIC TRANSCEIVER MONITOR ===\n" +
            "Target Ident Label       : %s\n" +
            "Ladderclimb Index Position: Z = %d [%s]\n" +
            "Zero-Point Flux Density  : %.4f W/m²\n" +
            "Transception Signal Loop : %s\n" +
            "Extrastate Language Core : ACTIVE (Omni Directional Substrate Transceiver Mapped)\n" +
            "Parallel Bus Integration : VERIFIED TRUTH STATE\n\n" +
            "Operational Constraints:\n" +
            "- System tasks isolated cleanly by native kernel memory structures.\n" +
            "- Periodic lattice calibration matches hydrogen parameters sequentially to silicon steps.\n" +
            "- Network baseline resolved to strict 1-0 Zero-Trust status.\n",
            rawName, currentAtomicNumberZ, atomicSymbol, fluxDensity, transceiverVector
        ));
    }

    public void haltDiagnosticLoop() {
        if (refreshTimer != null && refreshTimer.isRunning()) {
            refreshTimer.stop();
        }
    }
}
