package com.virtue.bus;

import javax.swing.*;
import java.awt.*;

public class VectorTile extends JPanel {
    private final JLabel titleLabel;
    private final JLabel subLabel;
    private final JLabel statusLabel;

    public VectorTile(String title, String subtitle) {
        setLayout(new BorderLayout());
        setBackground(new Color(40, 40, 40));
        setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(60, 60, 60), 1),
            BorderFactory.createEmptyBorder(15, 15, 15, 15)
        ));

        titleLabel = new JLabel(title);
        titleLabel.setForeground(Color.WHITE);
        titleLabel.setFont(new Font("SansSerif", Font.BOLD, 14));

        subLabel = new JLabel(subtitle);
        subLabel.setForeground(new Color(180, 180, 180));
        subLabel.setFont(new Font("SansSerif", Font.PLAIN, 11));

        statusLabel = new JLabel("STATUS: IDLE | AWAITING RESONSANCE LINK");
        statusLabel.setForeground(new Color(130, 130, 130));
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 11));

        JPanel textContainer = new JPanel(new GridLayout(2, 1, 5, 5));
        textContainer.setOpaque(false);
        textContainer.add(titleLabel);
        textContainer.add(subLabel);

        add(textContainer, BorderLayout.NORTH);
        add(statusLabel, BorderLayout.SOUTH);
    }

    public void setStatusText(String status, Color color) {
        statusLabel.setText("STATUS: " + status);
        statusLabel.setForeground(color);
    }
}
