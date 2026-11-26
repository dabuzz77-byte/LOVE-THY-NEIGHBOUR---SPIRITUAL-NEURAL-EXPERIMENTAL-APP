package com.virtue.ihn;
import neural.studio.*;


import javax.swing.*;
import java.awt.*;

public class MainIHNApp {
    public static void main(String[] args) {
        // Enforce safe UI execution on the native Event Dispatch Thread
        SwingUtilities.invokeLater(() -> {
            try {
                // Apply system look and feel for integrated visual execution
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}

            SectionFrame frame = new SectionFrame("INFERENCE HYPERPATHWAY NETWORK v2.0.0 [LAN BUS]");
            frame.setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
            frame.setSize(1100, 750);
            frame.setMinimumSize(new Dimension(900, 600));

            // Component Stratification
            ControlPanel controlPanel = new ControlPanel();
            NodeGridPanel nodeGridPanel = new NodeGridPanel();
            ConsoleLogPanel consoleLogPanel = new ConsoleLogPanel();
            
            LANScanEngine scanEngine = new LANScanEngine(nodeGridPanel, consoleLogPanel, controlPanel);
            controlPanel.setEngine(scanEngine);

            // Assembly via Structured Border Layout Matrix
            JPanel centerContainer = new JPanel(new BorderLayout(0, 10));
            centerContainer.setBackground(new Color(20, 20, 20));
            centerContainer.add(nodeGridPanel, BorderLayout.CENTER);
            centerContainer.add(consoleLogPanel, BorderLayout.SOUTH);

            frame.setLayout(new BorderLayout());
            frame.add(controlPanel, BorderLayout.NORTH);
            frame.add(centerContainer, BorderLayout.CENTER);

            // Center frame on host display workspace
            frame.setLocationRelativeTo(null);
            frame.setVisible(true);
        });
    }
}
