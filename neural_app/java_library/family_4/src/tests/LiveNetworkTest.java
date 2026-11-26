import neural.studio.*;
import net.manifold.engine.InferenceNetworkBroadcaster;
import net.manifold.telemetry.*;
import net.manifold.ui.NetworkDashboard;
import java.net.*;
import java.nio.file.*;
import java.util.concurrent.*;
import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;

/** Integration check using a held local TCP socket and real Windows telemetry. */
public final class LiveNetworkTest {
    public static void main(String[] args) throws Exception {
        NetworkDashboard[] view = new NetworkDashboard[1];
        try {
        try (ServerSocket server = new ServerSocket(0, 1, InetAddress.getLoopbackAddress());
             Socket client = new Socket(InetAddress.getLoopbackAddress(), server.getLocalPort());
             Socket accepted = server.accept();
             InferenceNetworkBroadcaster engine = new InferenceNetworkBroadcaster();
             NetworkMonitor monitor = new NetworkMonitor(engine)) {
            client.getOutputStream().write(new byte[1024]);
            if (accepted.getInputStream().readNBytes(1024).length != 1024) throw new AssertionError("Loopback transfer failed");
            CountDownLatch ready = new CountDownLatch(3);
            SwingUtilities.invokeAndWait(() -> view[0] = new NetworkDashboard(engine));
            monitor.addListener(s -> { view[0].accept(s); if (s.sequence() > 0 && s.error().isEmpty()) ready.countDown(); });
            monitor.start();
            if (!ready.await(45, TimeUnit.SECONDS)) throw new AssertionError("Collector failed: " + monitor.snapshot().error());
            var snapshot = monitor.snapshot();
            boolean found = snapshot.connections().stream().anyMatch(c -> c.established() && c.pid() == ProcessHandle.current().pid()
                    && (c.local().endsWith(":" + server.getLocalPort()) || c.remote().endsWith(":" + server.getLocalPort())));
            if (snapshot.adapters().isEmpty()) throw new AssertionError("No interface counters available");
            if (snapshot.adapters().stream().noneMatch(NetworkSnapshot.Adapter::rateAvailable)) throw new AssertionError("Rate baseline did not establish");
            if (args.length > 0) SwingUtilities.invokeAndWait(() -> {
                try {
                    NetworkDashboard panel = view[0]; panel.setSize(1380, 900); layout(panel);
                    BufferedImage image = new BufferedImage(1380, 900, BufferedImage.TYPE_INT_RGB);
                    Graphics2D graphics = image.createGraphics(); panel.printAll(graphics); graphics.dispose();
                    ImageIO.write(image, "png", Path.of(args[0]).toFile());
                } catch (Exception failure) { throw new RuntimeException(failure); }
            });
            if (!found) throw new AssertionError("TCP verification unavailable: " + snapshot.warning());
            System.out.println("PASS: actual loopback connection and PID detected; " + snapshot.connections().size()
                    + " TCP rows; " + snapshot.adapters().size() + " interfaces; " + snapshot.sequence() + " real samples");
        }
        } finally { if (view[0] != null) SwingUtilities.invokeAndWait(() -> view[0].close()); }
    }
    private static void layout(Container container) {
        container.doLayout();
        for (Component child : container.getComponents()) if (child instanceof Container nested) layout(nested);
    }
}
