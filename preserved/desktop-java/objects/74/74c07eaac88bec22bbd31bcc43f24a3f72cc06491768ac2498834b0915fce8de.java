package com.virtue.bus;

import javax.swing.*;
import java.awt.*;
import java.util.HashMap;
import java.util.Map;

public class TelemetryPanel extends JPanel {
    private final Map<String, VectorTile> tiles = new HashMap<>();
    private final JTextArea terminalLog;

    public TelemetryPanel() {
        setLayout(new BorderLayout());
        setBackground(new Color(20, 20, 20));

        // Create Grid Container for Vector Tiles
        JPanel gridPanel = new JPanel(new GridLayout(2, 2, 10, 10));
        gridPanel.setBackground(new Color(20, 20, 20));
        gridPanel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));

        // Initialize Vector Strata according to statutory definitions
        tiles.put("V1", new VectorTile("VECTOR 1/4: ALGORITHM PURGE", "DMCC Act Compliance • Opaque Profiling Stripped"));
        tiles.put("V2", new VectorTile("VECTOR 2/4: RESTITUTION ROUTE", "Consolidated Fund Pathway • Bank of England"));
        tiles.put("V3", new VectorTile("VECTOR 3/4: ECO FLOOR FUNDING", "£120M Statutory Levy Allocation • NHS Hubs"));
        tiles.put("V4", new VectorTile("VECTOR 4/4: SOUL INSULATION", "FCA Consumer Duty • Ring 3 Sandbox Active"));

        gridPanel.add(tiles.get("V1"));
        gridPanel.add(tiles.get("V2"));
        gridPanel.add(tiles.get("V3"));
        gridPanel.add(tiles.get("V4"));

        // Built-in Log Console Area
        terminalLog = new JTextArea(8, 50);
        terminalLog.setBackground(new Color(10, 10, 10));
        terminalLog.setForeground(new Color(0, 220, 0));
        terminalLog.setFont(new Font("Monospaced", Font.PLAIN, 11));
        terminalLog.setEditable(false);
        terminalLog.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));
        
        JScrollPane logScroll = new JScrollPane(terminalLog);
        logScroll.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(60, 60, 60)), 
            "LIVE LEDGER TX LOG STREAM", 0, 0, 
            new Font("Monospaced", Font.BOLD, 10), new Color(150, 150, 150)
        ));

        add(gridPanel, BorderLayout.CENTER);
        add(logScroll, BorderLayout.SOUTH);
    }

    public void updateVectorState(String key, String status, Color color) {
        VectorTile tile = tiles.get(key);
        if (tile != null) {
            tile.setStatusText(status, color);
        }
    }

    public void appendLog(String message) {
        terminalLog.append(message + "\n");
        terminalLog.setCaretPosition(terminalLog.getDocument().getLength());
    }
}
