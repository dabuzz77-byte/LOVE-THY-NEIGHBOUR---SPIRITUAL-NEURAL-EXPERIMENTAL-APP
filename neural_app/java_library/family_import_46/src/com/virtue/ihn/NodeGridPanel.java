package com.virtue.ihn;
import neural.studio.*;


import javax.swing.*;
import java.awt.*;
import java.util.HashMap;
import java.util.Map;

public class NodeGridPanel extends JPanel {
    private final JPanel gridContent;
    private final Map<String, DeviceCard> deviceRegistry = new HashMap<>();

    public NodeGridPanel() {
        setLayout(new BorderLayout());
        setBackground(new Color(22, 22, 22));
        setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));

        gridContent = new JPanel(new GridLayout(0, 3, 15, 15));
        gridContent.setBackground(new Color(22, 22, 22));

        JScrollPane scrollPane = new JScrollPane(gridContent);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);

        add(scrollPane, BorderLayout.CENTER);
    }

    public void clearGrid() {
        deviceRegistry.clear();
        gridContent.removeAll();
        gridContent.revalidate();
        gridContent.repaint();
    }

    public void registerDeviceNode(String ipAddress) {
        if (!deviceRegistry.containsKey(ipAddress)) {
            DeviceCard newCard = new DeviceCard(ipAddress);
            deviceRegistry.put(ipAddress, newCard);
            gridContent.add(newCard);
            gridContent.revalidate();
            gridContent.repaint();
        }
    }

    public void setDeviceOnline(String ipAddress, String responseTime) {
        DeviceCard card = deviceRegistry.get(ipAddress);
        if (card != null) {
            card.setOperationalState("IHN CONNECTED / 0->1 FLIPPED", responseTime, new Color(50, 220, 50));
        }
    }
}
