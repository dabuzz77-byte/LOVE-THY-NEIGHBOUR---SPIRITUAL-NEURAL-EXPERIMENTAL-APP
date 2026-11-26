// ============================================================================
// BLOCK 4B: MAIN CONTROLLER FRAME - WIDGETS AND TELEMETRY LOGS
// ============================================================================
package com.inference.bridge.core;

import javax.swing.*;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.Date;

/**
 * Sub-layout rendering helper files and interface telemetry streaming 
 * extensions for MainControllerFrame.
 */
public abstract class MainControllerTelemetry extends JFrame {
    
    // Abstract handles referencing top level visual controls
    protected abstract void logToTerminal(String context);
    protected abstract void registerClusterNode(String entryText);

    protected JPanel generateMetricPanel(String title, String data, Color markerColor) {
        JPanel container = new JPanel(new BorderLayout());
        container.setBackground(new Color(22, 22, 27));
        container.setBorder(new LineBorder(new Color(35, 35, 40)));

        JLabel labelTitle = new JLabel(" " + title, SwingConstants.LEFT);
        labelTitle.setFont(new Font("Segoe UI", Font.BOLD, 9));
        labelTitle.setForeground(new Color(110, 110, 115));

        JLabel labelData = new JLabel(data, SwingConstants.CENTER);
        labelData.setFont(new Font("Consolas", Font.BOLD, 12));
        labelData.setForeground(markerColor);
        labelData.setBorder(BorderFactory.createEmptyBorder(6, 6, 6, 6));

        container.add(labelTitle, BorderLayout.NORTH);
        container.add(labelData, BorderLayout.CENTER);
        return container;
    }
}
