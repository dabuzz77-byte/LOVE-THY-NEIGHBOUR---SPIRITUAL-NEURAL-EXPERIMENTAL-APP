package com.virtue.ihn;
import neural.studio.*;


import javax.swing.*;
import java.awt.*;

// Class block rendering individual hardware nodes visually
class DeviceCard extends JPanel {
    private final JLabel ipLabel;
    private final JLabel statusLabel;
    private final JLabel responseLabel;

    public DeviceCard(String ipAddress) {
        setLayout(new GridLayout(3, 1, 5, 5));
        setBackground(new Color(40, 40, 40));
        setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(65, 65, 65), 1),
            BorderFactory.createEmptyBorder(12, 12, 12, 12)
        ));

        ipLabel = new JLabel("IP: " + ipAddress);
        ipLabel.setForeground(Color.WHITE);
        ipLabel.setFont(new Font("Monospaced", Font.BOLD, 13));

        statusLabel = new JLabel("STATUS: DISCOVERING SUBSTRATE");
        statusLabel.setForeground(new Color(160, 160, 160));
        statusLabel.setFont(new Font("SansSerif", Font.BOLD, 10));

        responseLabel = new JLabel("LATENCY: AWAITING INTERCEPT");
        responseLabel.setForeground(Color.GRAY);
        responseLabel.setFont(new Font("SansSerif", Font.PLAIN, 10));

        add(ipLabel);
        add(statusLabel);
        add(responseLabel);
    }

    public void setOperationalState(String status, String latency, Color statusColor) {
        statusLabel.setText("STATUS: " + status);
        statusLabel.setForeground(statusColor);
        responseLabel.setText("LATENCY: " + latency);
        responseLabel.setForeground(Color.LIGHT_GRAY);
    }
}

// Class block managing the open console data ledger output stream
class ConsoleLogPanel extends JPanel {
    private final JTextArea consoleLog;

    public ConsoleLogPanel() {
        setLayout(new BorderLayout());
        setBackground(new Color(15, 15, 15));
        setPreferredSize(new Dimension(0, 200));

        consoleLog = new JTextArea();
        consoleLog.setBackground(new Color(10, 10, 10));
        consoleLog.setForeground(new Color(50, 220, 50));
        consoleLog.setFont(new Font("Monospaced", Font.PLAIN, 11));
        consoleLog.setEditable(false);
        consoleLog.setBorder(BorderFactory.createEmptyBorder(8, 8, 8, 8));

        JScrollPane scrollPane = new JScrollPane(consoleLog);
        scrollPane.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(50, 50, 50)),
            "IHN PARITY COMPLIANCE LOG REGISTER", 0, 0,
            new Font("Monospaced", Font.BOLD, 11), Color.GRAY
        ));

        add(scrollPane, BorderLayout.CENTER);
    }

    public void writeLogEntry(String text) {
        consoleLog.append(text + "\n");
        consoleLog.setCaretPosition(consoleLog.getDocument().getLength());
    }
}
