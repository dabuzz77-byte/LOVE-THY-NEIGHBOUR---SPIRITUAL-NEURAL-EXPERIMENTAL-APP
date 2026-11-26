import net.manifold.engine.InferenceNetworkBroadcaster;
import net.manifold.telemetry.NetworkSnapshot;
import net.manifold.ui.NetworkDashboard;
import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.nio.file.*;
import java.util.*;
import java.util.List;
import javax.imageio.ImageIO;

/** UI regression fixtures are deliberately labelled; production never uses fixture traffic. */
public final class DashboardTests {
    private static int checks;
    private static void check(boolean condition, String message) { checks++; if (!condition) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        try (var engine = new InferenceNetworkBroadcaster()) {
            SwingUtilities.invokeAndWait(() -> {
                var dashboard = new NetworkDashboard(engine);
                try {
                    long now = System.currentTimeMillis();
                    List<NetworkSnapshot.Connection> rows = new ArrayList<>();
                    for (int i = 1; i <= 9; i++) rows.add(new NetworkSnapshot.Connection("192.0.2.2:" + (50000 + i), "203.0.113." + i + ":443", "ESTABLISHED", 100 + i, "fixture-app-" + i));
                    rows.add(new NetworkSnapshot.Connection("127.0.0.1:50000", "127.0.0.1:8080", "ESTABLISHED", 90, "fixture-loopback"));
                    rows.add(new NetworkSnapshot.Connection("0.0.0.0:8000", "0.0.0.0:0", "LISTENING", 80, "fixture-listener"));
                    NetworkSnapshot fixture = null;
                    for (int i = 0; i < 100; i++) {
                        fixture = new NetworkSnapshot(now - (99 - i) * 2500, i + 1,
                                List.of(new NetworkSnapshot.Adapter("test", "TEST INTERFACE", 1_500_000_000, 200_000_000,
                                        200_000 + 170_000 * Math.sin(i / 8.0), 90_000 + 80_000 * Math.sin(i / 5.0), true)), rows,
                                List.of(new NetworkSnapshot.Event(now, "TEST", "UI fixture only; these are not live endpoints")),
                                true, "UI TEST FIXTURE · generated values for layout verification only", "");
                        dashboard.accept(fixture);
                    }
                    if (args.length > 0) {
                        render(dashboard, 1380, 900, Path.of(args[0], "dashboard-fixture.png"));
                        render(dashboard, 1100, 760, Path.of(args[0], "dashboard-fixture-small.png"));
                    }
                    List<Component> controls = new ArrayList<>(); collect(dashboard, controls);
                    JTable table = controls.stream().filter(c -> c instanceof JTable t && t.getColumnCount() == 5).map(c -> (JTable)c).findFirst().orElseThrow();
                    check(table.getRowCount() == 10, "Listening ports hidden by default");
                    JTextField search = controls.stream().filter(JTextField.class::isInstance).map(JTextField.class::cast).findFirst().orElseThrow();
                    search.setText("fixture-app-3"); check(table.getRowCount() == 1, "Application filter works");
                    search.setText("203.0.113.4:443"); check(table.getRowCount() == 1, "Endpoint filter works");
                    search.setText("");
                    JCheckBox loopback = checkbox(controls, "Loopback"); loopback.doClick(); check(table.getRowCount() == 9, "Loopback filter works"); loopback.doClick();
                    checkbox(controls, "Listening ports").doClick(); check(table.getRowCount() == 11, "Listener toggle works");
                    checkbox(controls, "Listening ports").doClick();
                    JButton pause = button(controls, "Pause view"); pause.doClick();
                    dashboard.accept(NetworkSnapshot.waiting()); check(table.getRowCount() == 10, "Paused view retains snapshot");
                    pause.doClick(); check(table.getRowCount() == 0, "Resume shows current snapshot");
                    dashboard.accept(fixture);
                    button(controls, "Recent changes").doClick(); button(controls, "Connections").doClick();
                    check(controls.stream().filter(JTable.class::isInstance).map(JTable.class::cast).allMatch(t -> t.getTableHeader().getParent() != null), "Headers attached in both table views");
                } catch (Exception failure) { throw new RuntimeException(failure); }
                finally { dashboard.close(); }
            });
        }
        System.out.println("PASS: " + checks + " dashboard interaction checks");
    }
    private static JButton button(List<Component> controls, String text) { return controls.stream().filter(c -> c instanceof JButton b && b.getText().equals(text)).map(c -> (JButton)c).findFirst().orElseThrow(); }
    private static JCheckBox checkbox(List<Component> controls, String text) { return controls.stream().filter(c -> c instanceof JCheckBox b && b.getText().equals(text)).map(c -> (JCheckBox)c).findFirst().orElseThrow(); }
    private static void collect(Container container, List<Component> controls) {
        for (Component c : container.getComponents()) { controls.add(c); if (c instanceof Container nested) collect(nested, controls); }
    }
    private static void layout(Container container) { container.doLayout(); for (Component c : container.getComponents()) if (c instanceof Container nested) layout(nested); }
    private static void render(NetworkDashboard panel, int width, int height, Path path) throws Exception {
        panel.setSize(width, height); layout(panel);
        var image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        var graphics = image.createGraphics(); panel.printAll(graphics); graphics.dispose(); ImageIO.write(image, "png", path.toFile());
    }
}
