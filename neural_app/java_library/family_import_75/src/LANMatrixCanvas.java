import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.util.Map;

/**
 * VISUALIZATION SYSTEM: METADATA EXPANDED PERIMETER DRAW SUITE
 */
public class LANMatrixCanvas extends JPanel {
    private final QuantumTernaryBinaryCore localCore;
    private final LocalNetworkLatchingEngine networkEngine;

    public LANMatrixCanvas(QuantumTernaryBinaryCore localCore, LocalNetworkLatchingEngine networkEngine) {
        this.localCore = localCore;
        this.networkEngine = networkEngine;
        setBackground(new Color(6, 8, 14));
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth();
        int h = getHeight();

        // 1. Draw structural geometric matrix wireframe grid
        g2d.setColor(new Color(20, 32, 55, 50));
        for (int i = 0; i < w; i += 40) g2d.drawLine(i, 0, i, h);
        for (int j = 0; j < h; j += 40) g2d.drawLine(0, j, w, j);

        // 2. Render local node probability outputs
        g2d.setColor(new Color(0, 255, 190));
        g2d.setFont(new Font("Consolas", Font.BOLD, 12));
        g2d.drawString("// LOCAL COORDINATOR QUANTUM FIELD MAP", 30, 35);
        
        double[] localProbs = localCore.getProbabilities();
        int step = Math.max(2, (w / 4) / localProbs.length);
        for (int i = 0; i < Math.min(localProbs.length, 64); i++) {
            int barH = (int) (localProbs[i] * 280);
            g2d.setColor(new Color(0, 180, 255, 160));
            g2d.fillRect(30 + (i * (step + 2)), 320 - barH, step, barH);
        }

        // 3. Render Latched LAN Perimeter devices grid matrix
        int startX = w / 2;
        g2d.setColor(new Color(255, 180, 0));
        g2d.drawString("// LATCHED PERIMETER NETWORK LAN NODES (AUTO-DISCOVERED)", startX, 35);

        int index = 0;
        Map<String, RemoteDeviceNode> devices = networkEngine.getLatchedDevices();
        for (RemoteDeviceNode device : devices.values()) {
            int nodeY = 70 + (index * 65);
            
            // Outer device perimeter bracket bounds
            g2d.setColor(new Color(25, 35, 60));
            g2d.fillRect(startX, nodeY, 360, 50);
            g2d.setColor(device.platformType.equalsIgnoreCase("ANDROID") ? new Color(100, 220, 100) : new Color(200, 100, 255));
            g2d.drawRect(startX, nodeY, 360, 50);

            g2d.setFont(new Font("Segoe UI", Font.BOLD, 11));
            g2d.drawString(device.platformType + " ID: " + device.deviceId, startX + 15, nodeY + 20);
            g2d.setFont(new Font("Consolas", Font.PLAIN, 10));
            g2d.setColor(new Color(0, 230, 255));
            g2d.drawString(String.format("IP: %s | Latent Entropy: %.4f | Salience: %.3f", 
                    device.ipAddress, device.lastEntropy, device.lastSalience), startX + 15, nodeY + 40);
            
            index++;
        }
    }
}
