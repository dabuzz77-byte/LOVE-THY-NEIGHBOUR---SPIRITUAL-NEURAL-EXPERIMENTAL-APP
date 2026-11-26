import javax.swing.*;
import java.awt.*;
import java.lang.management.ManagementFactory;
import com.sun.management.OperatingSystemMXBean;

public class SystemSovereigntyMonitor extends JFrame {
    private JLabel cpuLabel;
    private JLabel ramLabel;
    private OperatingSystemMXBean osBean;

    public SystemSovereigntyMonitor() {
        osBean = (OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();
        
        setTitle("Local Hardware Node Monitor");
        setSize(400, 200);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new GridLayout(2, 1));
        getContentPane().setBackground(Color.BLACK);

        cpuLabel = createStyledLabel("CPU Load: Calculating...");
        ramLabel = createStyledLabel("Free RAM: Calculating...");

        add(cpuLabel);
        add(ramLabel);

        startHardwarePolling();
    }

    private JLabel createStyledLabel(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setForeground(new Color(0, 255, 0)); // Terminal green
        label.setFont(new Font("Monospaced", Font.BOLD, 16));
        return label;
    }

    private void startHardwarePolling() {
        Timer timer = new Timer(1000, e -> {
            double cpuLoad = osBean.getCpuLoad() * 100;
            long freeRam = osBean.getFreeMemorySize() / (1024 * 1024);
            long totalRam = osBean.getTotalMemorySize() / (1024 * 1024);

            cpuLabel.setText(String.format("Local CPU Load: %.1f%%", cpuLoad));
            ramLabel.setText(String.format("Available RAM: %d MB / %d MB", freeRam, totalRam));
        });
        timer.start();
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new SystemSovereigntyMonitor().setVisible(true);
        });
    }
}