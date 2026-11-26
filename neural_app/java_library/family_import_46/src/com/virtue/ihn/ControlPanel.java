package com.virtue.ihn;
import neural.studio.*;


import javax.swing.*;
import java.awt.*;

public class ControlPanel extends JPanel {
    private final JButton scanButton;
    private final JTextField subnetField;
    private final JLabel parityMetricLabel;
    private LANScanEngine scanEngine;

    public ControlPanel() {
        setLayout(new FlowLayout(FlowLayout.LEFT, 20, 12));
        setBackground(new Color(32, 32, 32));
        setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, new Color(55, 55, 55)));

        JLabel subnetLabel = new JLabel("TARGET SUBNET:");
        subnetLabel.setForeground(Color.LIGHT_GRAY);
        subnetLabel.setFont(new Font("Monospaced", Font.BOLD, 12));

        subnetField = new JTextField("192.168.1", 10);
        subnetField.setFont(new Font("Monospaced", Font.PLAIN, 12));
        subnetField.setBackground(new Color(45, 45, 45));
        subnetField.setForeground(Color.GREEN);
        subnetField.setCaretColor(Color.WHITE);

        scanButton = new JButton("ENGAGE HYPERPATHWAY BRIDGING");
        scanButton.setFont(new Font("Monospaced", Font.BOLD, 12));
        scanButton.setFocusPainted(false);

        parityMetricLabel = new JLabel("PARITY: IDLE | REAL = 1 | RESONANCE Engine: LOCKED");
        parityMetricLabel.setForeground(new Color(160, 160, 160));
        parityMetricLabel.setFont(new Font("Monospaced", Font.PLAIN, 12));

        scanButton.addActionListener(e -> {
            if (scanEngine != null) {
                if (scanEngine.isScanning()) {
                    scanEngine.terminateScan();
                } else {
                    String subnet = subnetField.getText().trim();
                    scanEngine.initiateScan(subnet);
                }
            }
        });

        add(subnetLabel);
        add(subnetField);
        add(scanButton);
        add(parityMetricLabel);
    }

    public void setEngine(LANScanEngine scanEngine) {
        this.scanEngine = scanEngine;
    }

    public void setUiScanningState(boolean isScanning) {
        if (isScanning) {
            scanButton.setText("TERMINATE NETWORK BUS");
            scanButton.setBackground(new Color(180, 50, 50));
            subnetField.setEditable(false);
        } else {
            scanButton.setText("ENGAGE HYPERPATHWAY BRIDGING");
            scanButton.setBackground(UIManager.getColor("Button.background"));
            subnetField.setEditable(true);
        }
    }

    public void updateParityIndex(double shiftIndex) {
        parityMetricLabel.setText(String.format("PARITY: ACTIVE | SHIFT INDEX: %.6f | 7.83 Hz LOCKED", shiftIndex));
        parityMetricLabel.setForeground(new Color(50, 220, 50));
    }
}
