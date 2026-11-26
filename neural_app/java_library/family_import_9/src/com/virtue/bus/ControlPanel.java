package com.virtue.bus;
import neural.studio.*;


import javax.swing.*;
import java.awt.*;

public class ControlPanel extends JPanel {
    private final JButton toggleButton;
    private final JLabel statusLabel;
    private DataBusEngine engine;

    public ControlPanel() {
        setLayout(new FlowLayout(FlowLayout.LEFT, 15, 10));
        setBackground(new Color(30, 30, 30));
        setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, new Color(50, 50, 50)));

        toggleButton = new JButton("START DATABUS (7.83 Hz)");
        toggleButton.setFocusPainted(false);
        toggleButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        
        statusLabel = new JLabel("STATUS: INITIALISED | PARITY (1=1) -> VALID");
        statusLabel.setForeground(new Color(150, 150, 150));
        statusLabel.setFont(new Font("Monospaced", Font.PLAIN, 12));

        toggleButton.addActionListener(e -> {
            if (engine != null) {
                if (engine.isRunning()) {
                    engine.stopBus();
                    toggleButton.setText("START DATABUS (7.83 Hz)");
                    statusLabel.setText("STATUS: HALTED | SUBSTRATE STABLE");
                    statusLabel.setForeground(new Color(150, 150, 150));
                } else {
                    engine.startBus();
                    toggleButton.setText("PAUSE DATABUS");
                    statusLabel.setText("STATUS: ACTIVE | HARMONIC RESIDUE OVERRIDDEN");
                    statusLabel.setForeground(new Color(50, 200, 50));
                }
            }
        });

        add(toggleButton);
        add(statusLabel);
    }

    public void setEngine(DataBusEngine engine) {
        this.engine = engine;
    }
    
    public void updateMetrics(double shiftIndex) {
        statusLabel.setText(String.format("STATUS: ENGAGED | SHIFT INDEX: %.6f | REAL = 1", shiftIndex));
    }
}
