import neural.studio.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;
import javax.swing.*;

/** Renders the real Swing component with explicitly labelled fixture data, without opening a window. */
public final class DashboardPreview {
    public static void main(String[] args) throws Exception {
        String output = args[0];
        try (LocalNetworkLatchingEngine engine = new LocalNetworkLatchingEngine(0, 0, 30_000)) {
            engine.startEngine();
            EngineSelfTest.send(engine.getTcpPort(), "LAN1|ANDROID|demo-pixel-9|1.82|0.84|0.1,0.2,0.3,0.4\n");
            EngineSelfTest.send(engine.getTcpPort(), "LAN1|IOS|demo-iphone-16|1.96|0.72|0.2,0.25,0.25,0.3\n");
            EngineSelfTest.send(engine.getTcpPort(), "LAN1|ANDROID|demo-tablet|1.72|0.62|0.1,0.15,0.25,0.5\n");
            SwingUtilities.invokeAndWait(() -> {
                try {
                    UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
                    LANMatrixCanvas.configureTheme();
                    render(fixture(engine), 1420, 900, output + "/dashboard-preview.png", "PREVIEW - SAMPLE DEVICES AND METRICS");
                    render(fixture(engine), 1080, 760, output + "/dashboard-compact.png", "PREVIEW - SAMPLE DEVICES AND METRICS");
                    engine.stopEngine();
                    LANMatrixCanvas canvas = new LANMatrixCanvas(new QuantumTernaryBinaryCore(6, .4), engine);
                    canvas.addAction(new JButton("Start receiver"));
                    canvas.addAction(new JButton("Connect a device"));
                    canvas.addAction(new JButton("Export CSV"));
                    canvas.refresh(new HardwareMetricSampler.Sample(-1, 20L * 1048576, 2048L * 1048576, 20));
                    render(canvas, 1420, 900, output + "/dashboard-empty.png", "PREVIEW - STOPPED RECEIVER");
                } catch (Exception ex) { throw new RuntimeException(ex); }
            });
        }
    }

    private static LANMatrixCanvas fixture(LocalNetworkLatchingEngine engine) throws InterruptedException {
        QuantumTernaryBinaryCore core = new QuantumTernaryBinaryCore(6, .4);
        LANMatrixCanvas canvas = new LANMatrixCanvas(core, engine);
        canvas.addAction(new JButton("Stop receiver"));
        canvas.addAction(new JButton("Connect a device"));
        canvas.addAction(new JButton("Export CSV"));
        for (int i = 0; i < 60; i++) {
            HardwareMetricSampler.Sample sample = new HardwareMetricSampler.Sample(.38 + .14 * Math.sin(i * .22),
                    180L * 1048576, 2048L * 1048576, 27);
            core.processQuantumState(sample.channels());
            canvas.refresh(sample);
            Thread.sleep(2);
        }
        return canvas;
    }

    private static void layout(Container parent) {
        parent.doLayout();
        for (Component child : parent.getComponents()) if (child instanceof Container) layout((Container) child);
    }

    private static void render(JComponent component, int width, int height, String path, String caption) throws Exception {
        component.setSize(width, height);
        layout(component);
        BufferedImage image = new BufferedImage(width, height + 26, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = image.createGraphics();
        graphics.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        component.printAll(graphics);
        graphics.setColor(new Color(21, 38, 56));
        graphics.fillRect(0, height, width, 26);
        graphics.setColor(Color.WHITE);
        graphics.setFont(new Font("Segoe UI", Font.BOLD, 11));
        graphics.drawString(caption, 30, height + 18);
        graphics.dispose();
        ImageIO.write(image, "png", new File(path));
    }
}
