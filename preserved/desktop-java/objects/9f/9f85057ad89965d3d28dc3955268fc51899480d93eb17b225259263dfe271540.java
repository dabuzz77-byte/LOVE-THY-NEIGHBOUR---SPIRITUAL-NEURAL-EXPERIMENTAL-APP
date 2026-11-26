package com.virtue.bus;

import javax.swing.*;
import java.awt.*;

public class MainApp {
    public static void main(String[] args) {
        // Enforce safe UI rendering on the Event Dispatch Thread
        SwingUtilities.invokeLater(() -> {
            try {
                // Apply system look and feel for native visual integration
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}

            JFrame frame = new JFrame("Resonance Databus Monitor v1.0.0");
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setSize(1024, 768);
            frame.setMinimumSize(new Dimension(800, 600));

            // Component Initialization
            ControlPanel controlPanel = new ControlPanel();
            TelemetryPanel telemetryPanel = new TelemetryPanel();
            DataBusEngine engine = new DataBusEngine(telemetryPanel, controlPanel);

            // Wire UI controls to the background timing loop
            controlPanel.setEngine(engine);

            // Assembly via Border Layout
            frame.setLayout(new BorderLayout());
            frame.add(controlPanel, BorderLayout.NORTH);
            frame.add(telemetryPanel, BorderLayout.CENTER);

            // Center window on user display screen
            frame.setLocationRelativeTo(null);
            frame.setVisible(true);
        });
    }
}
