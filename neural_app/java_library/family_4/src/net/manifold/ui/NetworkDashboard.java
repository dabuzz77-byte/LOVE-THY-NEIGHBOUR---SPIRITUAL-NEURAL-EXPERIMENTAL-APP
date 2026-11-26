package net.manifold.ui;
import neural.studio.*;


import net.manifold.engine.InferenceNetworkBroadcaster;
import net.manifold.telemetry.NetworkSnapshot;
import net.manifold.telemetry.NetworkSnapshot.*;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;
import javax.swing.table.*;
import java.awt.*;
import java.awt.geom.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;

/** Swing view of measured OS activity. All model changes are made on the event dispatch thread. */
public final class NetworkDashboard extends JPanel {
    private static final Color BG = new Color(10, 16, 25), PANEL = new Color(17, 26, 38),
            BORDER = new Color(37, 53, 68), TEXT = new Color(227, 238, 243),
            MUTED = new Color(137, 159, 176), GREEN = new Color(69, 226, 180),
            BLUE = new Color(94, 168, 255), AMBER = new Color(255, 194, 112);
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm:ss").withZone(ZoneId.systemDefault());
    private final InferenceNetworkBroadcaster engine;
    private NetworkSnapshot latest = NetworkSnapshot.waiting(), shown = latest;
    private final JComboBox<Adapter> adapters = new JComboBox<>();
    private final JTextField search = new JTextField(22);
    private final JCheckBox listeners = new JCheckBox("Listening ports"), loopback = new JCheckBox("Loopback", true);
    private final JLabel state = new JLabel("STARTING"), status = new JLabel("Reading Windows network activity..."),
            engineStatus = new JLabel(), tableCount = new JLabel();
    private final JLabel receive = valueLabel(), send = valueLabel(), connections = valueLabel(), processes = valueLabel();
    private final JLabel receiveNote = noteLabel(), sendNote = noteLabel();
    private final List<RatePoint> history = new ArrayList<>();
    private final List<Connection> visible = new ArrayList<>();
    private final ConnectionModel connectionModel = new ConnectionModel();
    private final EventModel eventModel = new EventModel();
    private final Topology topology = new Topology();
    private final TrafficChart chart = new TrafficChart();
    private final neural.studio.SharedTimer timer;
    private boolean paused, updatingAdapters;
    private String selectedId = "";
    private long graphedSequence = -1;
    private record RatePoint(long time, double receive, double send) {}

    public NetworkDashboard(InferenceNetworkBroadcaster engine) {
        this.engine = engine;
        setLayout(new BorderLayout(0, 16));
        setBackground(BG);
        setBorder(new EmptyBorder(22, 24, 14, 24));
        setPreferredSize(new Dimension(1380, 900));

        JPanel top = transparent(new BorderLayout(0, 18));
        JPanel title = transparent(new BorderLayout());
        JPanel identity = transparent(new GridLayout(2, 1, 0, 6));
        identity.add(label("MANIFOLD   /   NETWORK OBSERVATORY", 23, TEXT, true));
        identity.add(label("A live view of this computer's connections and traffic", 12, MUTED, false));
        title.add(identity, BorderLayout.WEST);
        state.setFont(font(12, true)); state.setForeground(GREEN);
        title.add(state, BorderLayout.EAST);
        top.add(title, BorderLayout.NORTH);

        JPanel toolbar = transparent(new BorderLayout(12, 0));
        JPanel selector = transparent(new FlowLayout(FlowLayout.LEFT, 10, 0));
        selector.add(label("NETWORK INTERFACE", 11, MUTED, true));
        adapters.setPreferredSize(new Dimension(250, 30)); style(adapters);
        adapters.setToolTipText("Transfer rates belong to this interface; the TCP table covers the whole computer.");
        adapters.addActionListener(e -> {
            if (updatingAdapters) return;
            Adapter adapter = (Adapter) adapters.getSelectedItem();
            selectedId = adapter == null ? "" : adapter.id();
            history.clear(); graphedSequence = -1;
            updateMetrics(); addHistory(); chart.repaint(); topology.repaint();
        });
        selector.add(adapters);
        toolbar.add(selector, BorderLayout.WEST);
        JPanel actions = transparent(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        JButton pause = button("Pause view");
        pause.setToolTipText("Freeze the view while collection continues in the background.");
        pause.addActionListener(e -> {
            paused = !paused;
            pause.setText(paused ? "Resume live" : "Pause view");
            if (!paused) { history.clear(); graphedSequence = -1; accept(latest); }
            refreshStatus();
        });
        JButton export = button("Export connections"); export.addActionListener(e -> exportConnections());
        actions.add(pause); actions.add(export); toolbar.add(actions, BorderLayout.EAST);
        JPanel topBody = transparent(new BorderLayout(0, 16));
        topBody.add(toolbar, BorderLayout.NORTH);
        JPanel metrics = transparent(new GridLayout(1, 4, 12, 0));
        metrics.add(metric("DOWNLOAD", receive, receiveNote, GREEN));
        metrics.add(metric("UPLOAD", send, sendNote, BLUE));
        metrics.add(metric("ESTABLISHED TCP", connections, label("Across this computer", 11, MUTED, false), TEXT));
        metrics.add(metric("CONNECTED APPS", processes, label("Distinct process IDs", 11, MUTED, false), TEXT));
        topBody.add(metrics, BorderLayout.CENTER); top.add(topBody, BorderLayout.CENTER);
        add(top, BorderLayout.NORTH);

        JPanel mapPanel = panel(new BorderLayout());
        mapPanel.add(section("CONNECTION MAP", "Established endpoints · size = connection count"), BorderLayout.NORTH);
        mapPanel.add(topology, BorderLayout.CENTER);
        JLabel mapNote = label("Links show connections. Traffic rates are measured per interface.", 11, MUTED, false);
        mapNote.setBorder(new EmptyBorder(0, 18, 12, 12)); mapPanel.add(mapNote, BorderLayout.SOUTH);
        JPanel chartPanel = panel(new BorderLayout());
        chartPanel.add(section("TRAFFIC HISTORY", "Download / upload · last 5 minutes"), BorderLayout.NORTH);
        chartPanel.add(chart, BorderLayout.CENTER);
        JPanel legend = transparent(new FlowLayout(FlowLayout.LEFT, 18, 10));
        legend.add(label("●  Download", 12, GREEN, true)); legend.add(label("●  Upload", 12, BLUE, true));
        chartPanel.add(legend, BorderLayout.SOUTH);
        JSplitPane upper = split(JSplitPane.HORIZONTAL_SPLIT, mapPanel, chartPanel, .62);
        mapPanel.setMinimumSize(new Dimension(420, 220)); chartPanel.setMinimumSize(new Dimension(300, 220));

        JPanel tablePanel = panel(new BorderLayout(0, 8));
        JPanel tableTools = transparent(new BorderLayout(10, 0));
        tableTools.setBorder(new EmptyBorder(12, 14, 2, 14));
        JPanel filters = transparent(new FlowLayout(FlowLayout.LEFT, 10, 0));
        filters.add(label("FILTER", 11, MUTED, true));
        style(search); search.setPreferredSize(new Dimension(220, 28));
        search.setToolTipText("Search application, address, port, state, or PID");
        search.getAccessibleContext().setAccessibleName("Search connections");
        filters.add(search);
        for (JCheckBox checkbox : List.of(listeners, loopback)) {
            checkbox.setOpaque(false); checkbox.setForeground(MUTED); checkbox.setFont(font(11, false));
            checkbox.addActionListener(e -> filter()); filters.add(checkbox);
        }
        search.getDocument().addDocumentListener(new DocumentListener() {
            public void insertUpdate(DocumentEvent e) { filter(); }
            public void removeUpdate(DocumentEvent e) { filter(); }
            public void changedUpdate(DocumentEvent e) { filter(); }
        });
        tableTools.add(filters, BorderLayout.WEST);
        tableCount.setForeground(MUTED); tableCount.setFont(font(11, false)); tableTools.add(tableCount, BorderLayout.EAST);
        tablePanel.add(tableTools, BorderLayout.NORTH);
        CardLayout tableLayout = new CardLayout();
        JPanel tables = transparent(tableLayout);
        JTable table = table(connectionModel);
        table.getColumnModel().getColumn(0).setPreferredWidth(180);
        table.getColumnModel().getColumn(1).setPreferredWidth(70);
        table.getColumnModel().getColumn(2).setPreferredWidth(230);
        table.getColumnModel().getColumn(3).setPreferredWidth(230);
        table.getColumnModel().getColumn(4).setPreferredWidth(110);
        tables.add(scroll(table), "connections");
        JTable eventsTable = table(eventModel);
        eventsTable.getColumnModel().getColumn(0).setMaxWidth(110);
        eventsTable.getColumnModel().getColumn(1).setMaxWidth(95);
        tables.add(scroll(eventsTable), "events");
        JPanel tableNavigation = transparent(new FlowLayout(FlowLayout.LEFT, 8, 0));
        tableNavigation.setBorder(new EmptyBorder(0, 14, 9, 14));
        JButton connectionTab = button("Connections"), eventTab = button("Recent changes");
        connectionTab.setForeground(GREEN); eventTab.setForeground(MUTED);
        connectionTab.addActionListener(e -> { tableLayout.show(tables, "connections"); connectionTab.setForeground(GREEN); eventTab.setForeground(MUTED); });
        eventTab.addActionListener(e -> { tableLayout.show(tables, "events"); eventTab.setForeground(GREEN); connectionTab.setForeground(MUTED); });
        tableNavigation.add(connectionTab); tableNavigation.add(eventTab);
        JPanel tableBody = transparent(new BorderLayout()); tableBody.add(tableNavigation, BorderLayout.NORTH);
        tableBody.add(tables, BorderLayout.CENTER); tablePanel.add(tableBody, BorderLayout.CENTER);
        tablePanel.setMinimumSize(new Dimension(700, 200));
        JSplitPane content = split(JSplitPane.VERTICAL_SPLIT, upper, tablePanel, .56);
        add(content, BorderLayout.CENTER);

        JPanel footer = transparent(new BorderLayout(16, 0));
        status.setFont(font(11, false)); status.setForeground(MUTED);
        engineStatus.setFont(font(11, false)); engineStatus.setForeground(MUTED);
        footer.add(status, BorderLayout.CENTER); footer.add(engineStatus, BorderLayout.EAST); add(footer, BorderLayout.SOUTH);
        timer = new neural.studio.SharedTimer(100, e -> { refreshStatus(); if (!paused && isShowing()) topology.repaint(); });
        timer.start();
    }

    public void accept(NetworkSnapshot snapshot) {
        if (!SwingUtilities.isEventDispatchThread()) { SwingUtilities.invokeLater(() -> accept(snapshot)); return; }
        latest = snapshot;
        if (paused) return;
        shown = snapshot;
        updatingAdapters = true;
        adapters.removeAllItems();
        Adapter chosen = snapshot.adapters().stream().filter(a -> a.id().equals(selectedId)).findFirst().orElse(null);
        if (chosen == null) chosen = snapshot.adapters().stream().max(Comparator.comparingLong(a -> a.receivedBytes() + a.sentBytes())).orElse(null);
        String nextId = chosen == null ? "" : chosen.id();
        if (!nextId.equals(selectedId)) { history.clear(); graphedSequence = -1; }
        selectedId = nextId;
        for (Adapter adapter : snapshot.adapters()) adapters.addItem(adapter);
        adapters.setSelectedItem(chosen); updatingAdapters = false;
        updateMetrics(); addHistory(); filter(); eventModel.fireTableDataChanged(); refreshStatus(); chart.repaint(); topology.repaint();
    }

    private Adapter selected() { return (Adapter) adapters.getSelectedItem(); }
    private void updateMetrics() {
        Adapter adapter = selected();
        boolean valid = adapter != null && adapter.rateAvailable() && shown.error().isEmpty() && !shown.stale();
        receive.setText(valid ? rate(adapter.receiveRate()) : "—");
        send.setText(valid ? rate(adapter.sendRate()) : "—");
        receiveNote.setText(adapter == null ? "No active interface" : "Interface total  " + bytes(adapter.receivedBytes()));
        sendNote.setText(adapter == null ? "Waiting for readings" : "Interface total  " + bytes(adapter.sentBytes()));
        connections.setText(shown.tcpAvailable() ? Long.toString(shown.establishedCount()) : "—");
        processes.setText(shown.tcpAvailable() ? Long.toString(shown.processCount()) : "—");
    }

    private void addHistory() {
        if (shown.sequence() == graphedSequence || shown.sequence() == 0 || !shown.error().isEmpty()) return;
        graphedSequence = shown.sequence();
        Adapter adapter = selected();
        history.add(new RatePoint(shown.capturedAt(), adapter != null && adapter.rateAvailable() ? adapter.receiveRate() : Double.NaN,
                adapter != null && adapter.rateAvailable() ? adapter.sendRate() : Double.NaN));
        history.removeIf(p -> shown.capturedAt() - p.time() > 300_000);
        while (history.size() > 180) history.remove(0);
    }

    private void filter() {
        String query = search.getText().strip().toLowerCase(Locale.ROOT);
        visible.clear();
        for (Connection c : shown.connections()) {
            if (!listeners.isSelected() && c.listening() || !loopback.isSelected() && c.loopback()) continue;
            if ((c.process() + " " + c.pid() + " " + c.local() + " " + c.remote() + " " + c.state()).toLowerCase(Locale.ROOT).contains(query)) visible.add(c);
        }
        visible.sort(Comparator.comparing(Connection::process).thenComparing(Connection::remote).thenComparingInt(Connection::pid));
        connectionModel.fireTableDataChanged();
        tableCount.setText(shown.tcpAvailable() ? visible.size() + " / " + shown.connections().size() + " rows" : "TCP data unavailable");
        topology.repaint();
    }

    private void refreshStatus() {
        boolean bad = !shown.error().isEmpty(), stale = shown.stale();
        String badge = paused ? "VIEW PAUSED" : bad ? "RETRYING" : stale ? "STALE DATA" : shown.sequence() == 0 ? "STARTING"
                : !shown.warning().isEmpty() || !shown.tcpAvailable() ? "PARTIAL DATA" : "●  LIVE / LOCAL";
        state.setText(badge); state.setForeground(paused || bad || stale || !shown.warning().isEmpty() ? AMBER : GREEN);
        String detail = bad ? shown.error() : !shown.warning().isEmpty() ? shown.warning()
                : shown.sequence() == 0 ? "Reading Windows network activity..."
                : "Updated " + TIME.format(Instant.ofEpochMilli(shown.capturedAt())) + "  ·  Windows TCP + interface counters  ·  Nominal 2s interval";
        if (paused) detail = "View frozen at " + (shown.capturedAt() == 0 ? "startup" : TIME.format(Instant.ofEpochMilli(shown.capturedAt()))) + " · collection continues";
        status.setText(detail); status.setToolTipText(detail);
        engineStatus.setText(engine.getProcessedCount() + " samples processed  ·  " + engine.getQueueDepth() + " queued");
        if (!paused && (bad || stale)) updateMetrics();
    }

    private void exportConnections() {
        SectionFileChooser chooser = new SectionFileChooser(); chooser.setDialogTitle("Export visible TCP connections");
        chooser.setSelectedFile(new java.io.File("manifold-connections.csv"));
        if (chooser.showSaveDialog(this) != SectionFileChooser.APPROVE_OPTION) return;
        Path path = chooser.getSelectedFile().toPath();
        if (Files.exists(path) && SectionDialogs.showConfirmDialog(this, "Replace " + path.getFileName() + "?", "Replace file",
                JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return;
        try {
            Files.writeString(path, csv(visible, shown.capturedAt()), StandardCharsets.UTF_8);
            SectionDialogs.showMessageDialog(this, "Exported " + visible.size() + " connections.");
        } catch (IOException failure) { SectionDialogs.showMessageDialog(this, failure.getMessage(), "Export failed", JOptionPane.ERROR_MESSAGE); }
    }

    public static String csv(List<Connection> connections, long capturedAt) {
        StringBuilder result = new StringBuilder("Captured at,Process,PID,Local endpoint,Remote endpoint,State\r\n");
        for (Connection c : connections) {
            String[] cells = { Instant.ofEpochMilli(capturedAt).toString(), c.process(), Integer.toString(c.pid()), c.local(), c.remote(), c.state() };
            for (int i = 0; i < cells.length; i++) {
                if (i > 0) result.append(',');
                String cell = cells[i];
                if (!cell.isEmpty() && "=+-@\t\r".indexOf(cell.charAt(0)) >= 0) cell = "'" + cell;
                result.append('"').append(cell.replace("\"", "\"\"")).append('"');
            }
            result.append("\r\n");
        }
        return result.toString();
    }
    public void close() { timer.stop(); }

    private final class ConnectionModel extends AbstractTableModel {
        private final String[] columns = {"APPLICATION", "PID", "LOCAL ENDPOINT", "REMOTE ENDPOINT", "STATE"};
        public int getRowCount() { return visible.size(); }
        public int getColumnCount() { return columns.length; }
        public String getColumnName(int column) { return columns[column]; }
        public Class<?> getColumnClass(int column) { return column == 1 ? Integer.class : String.class; }
        public Object getValueAt(int row, int column) {
            Connection c = visible.get(row);
            return switch (column) { case 0 -> c.process(); case 1 -> c.pid(); case 2 -> c.local(); case 3 -> c.remote(); default -> c.state(); };
        }
    }
    private final class EventModel extends AbstractTableModel {
        private final String[] columns = {"TIME", "CHANGE", "OBSERVATION"};
        public int getRowCount() { return shown.events().size(); }
        public int getColumnCount() { return columns.length; }
        public String getColumnName(int column) { return columns[column]; }
        public Object getValueAt(int row, int column) {
            NetworkSnapshot.Event event = shown.events().get(row);
            return switch (column) { case 0 -> TIME.format(Instant.ofEpochMilli(event.time())); case 1 -> event.type(); default -> event.description(); };
        }
    }

    private final class Topology extends JPanel {
        Topology() { setOpaque(false); setToolTipText("Established TCP endpoints matching the filters below. No packet-level or per-process bandwidth is inferred."); }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create(); quality(g);
            int w = getWidth(), h = getHeight(), cx = w / 2, cy = h / 2;
            g.setColor(new Color(28, 42, 55));
            for (int x = 20; x < w; x += 24) for (int y = 14; y < h; y += 24) g.fillOval(x, y, 1, 1);
            Map<String, Integer> counts = new HashMap<>();
            visible.stream().filter(Connection::established).forEach(c -> counts.merge(c.remoteHost(), 1, Integer::sum));
            int limit = h < 210 ? 6 : 8;
            List<Map.Entry<String, Integer>> endpoints = counts.entrySet().stream()
                    .sorted(Map.Entry.<String, Integer>comparingByValue().reversed().thenComparing(Map.Entry.comparingByKey()))
                    .limit(limit).toList();
            double rx = Math.max(95, w * .31), ry = Math.max(30, (h - 100) * .5);
            g.setColor(BORDER); g.setStroke(new BasicStroke(1));
            g.draw(new Ellipse2D.Double(cx - rx, cy - ry, rx * 2, ry * 2));
            for (int i = 0; i < endpoints.size(); i++) {
                boolean onLeft = i % 2 == 0;
                int rowCount = (endpoints.size() + (onLeft ? 1 : 0)) / 2;
                int x = (int) (w * (onLeft ? .28 : .72));
                int y = rowCount == 1 ? cy : 28 + (h - 64) * (i / 2) / (rowCount - 1);
                var endpoint = endpoints.get(i);
                g.setColor(new Color(49, 108, 114));
                g.draw(new QuadCurve2D.Double(cx, cy, (cx + x) / 2.0, y, x, y));
                int radius = Math.min(17, 8 + endpoint.getValue());
                g.setColor(new Color(30, 72, 73)); g.fillOval(x - radius - 5, y - radius - 5, radius * 2 + 10, radius * 2 + 10);
                g.setColor(GREEN); g.fillOval(x - 4, y - 4, 8, 8);
                g.setFont(font(11, true)); g.setColor(TEXT);
                String host = shorten(endpoint.getKey(), Math.max(12, Math.min(23, w / 40)));
                int labelX = onLeft ? x - 22 - g.getFontMetrics().stringWidth(host) : x + 22;
                g.drawString(host, labelX, y - 2);
                g.setFont(font(10, false)); g.setColor(MUTED);
                String count = endpoint.getValue() + (endpoint.getValue() == 1 ? " connection" : " connections");
                g.drawString(count, onLeft ? x - 22 - g.getFontMetrics().stringWidth(count) : x + 22, y + 13);
            }
            Adapter adapter = selected();
            boolean traffic = adapter != null && adapter.rateAvailable() && adapter.receiveRate() + adapter.sendRate() > 0
                    && !paused && !shown.stale() && shown.error().isEmpty();
            int pulse = traffic ? (int) (System.nanoTime() / 30_000_000 % 23) : 0;
            g.setColor(new Color(69, 226, 180, traffic ? 55 - pulse * 2 : 25));
            g.drawOval(cx - 47 - pulse, cy - 47 - pulse, 94 + pulse * 2, 94 + pulse * 2);
            g.setColor(PANEL); g.fillOval(cx - 44, cy - 44, 88, 88); g.setColor(GREEN); g.drawOval(cx - 44, cy - 44, 88, 88);
            g.setFont(font(12, true)); centered(g, "THIS PC", cx, cy - 2);
            g.setColor(MUTED); g.setFont(font(10, false)); centered(g, "LOCAL HOST", cx, cy + 16);
            if (endpoints.isEmpty()) {
                g.setColor(MUTED); g.setFont(font(12, false));
                centered(g, shown.sequence() == 0 ? "Waiting for the first snapshot" : !shown.tcpAvailable()
                        ? "TCP access unavailable · see status below" : "No established connections match the filters", cx, Math.min(h - 12, cy + 85));
            }
            if (counts.size() > limit) { g.setColor(MUTED); g.setFont(font(10, false)); g.drawString("+ " + (counts.size() - limit) + " endpoints in the table", 18, h - 10); }
            g.dispose();
        }
    }

    private final class TrafficChart extends JPanel {
        TrafficChart() { setOpaque(false); }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create(); quality(g);
            int left = 76, top = 26, right = Math.max(left + 1, getWidth() - 24), bottom = Math.max(top + 1, getHeight() - 28);
            double peak = history.stream().mapToDouble(p -> Math.max(p.receive(), p.send())).filter(Double::isFinite).max().orElse(0);
            double max = Math.max(1024, peak * 1.2);
            g.setFont(font(10, false));
            for (int i = 0; i <= 4; i++) {
                int y = top + (bottom - top) * i / 4;
                g.setColor(BORDER); g.drawLine(left, y, right, y); g.setColor(MUTED);
                g.drawString(bytes(max * (4 - i) / 4) + "/s", 12, y + 4);
            }
            g.setColor(MUTED); g.drawString("−5 min", left, bottom + 20); g.drawString("now", right - 20, bottom + 20);
            long end = history.isEmpty() ? System.currentTimeMillis() : history.get(history.size() - 1).time();
            for (int stream = 0; stream < 2; stream++) {
                Path2D path = new Path2D.Double(); boolean connected = false;
                for (RatePoint point : history) {
                    double value = stream == 0 ? point.receive() : point.send();
                    if (!Double.isFinite(value)) { connected = false; continue; }
                    double x = right - (end - point.time()) / 300_000.0 * (right - left);
                    double y = bottom - value / max * (bottom - top);
                    if (!connected) path.moveTo(x, y); else path.lineTo(x, y);
                    connected = true;
                    g.setColor(stream == 0 ? GREEN : BLUE); g.fill(new Ellipse2D.Double(x - 2, y - 2, 4, 4));
                }
                g.setColor(stream == 0 ? GREEN : BLUE); g.setStroke(new BasicStroke(2.1f)); g.draw(path);
            }
            if (history.stream().noneMatch(p -> Double.isFinite(p.receive()))) {
                g.setColor(MUTED); g.setFont(font(12, false)); centered(g, "Collecting a rate baseline...", (left + right) / 2, (top + bottom) / 2);
            }
            g.dispose();
        }
    }

    private static JPanel transparent(LayoutManager layout) { JPanel panel = new JPanel(layout); panel.setOpaque(false); return panel; }
    private static JPanel panel(LayoutManager layout) {
        JPanel panel = new JPanel(layout); panel.setBackground(PANEL); panel.setBorder(BorderFactory.createLineBorder(BORDER)); return panel;
    }
    private static Font font(int size, boolean bold) { return new Font("Segoe UI", bold ? Font.BOLD : Font.PLAIN, size); }
    private static JLabel label(String text, int size, Color color, boolean bold) {
        JLabel label = new JLabel(text); label.setFont(font(size, bold)); label.setForeground(color); return label;
    }
    private static JLabel valueLabel() { return label("—", 30, TEXT, true); }
    private static JLabel noteLabel() { return label("Waiting for readings", 11, MUTED, false); }
    private static JPanel metric(String name, JLabel value, JLabel note, Color accent) {
        JPanel card = panel(new BorderLayout(0, 7)); card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(BORDER), new EmptyBorder(14, 18, 14, 18)));
        card.add(label(name, 11, MUTED, true), BorderLayout.NORTH); value.setForeground(accent);
        card.add(value, BorderLayout.CENTER); card.add(note, BorderLayout.SOUTH); return card;
    }
    private static JPanel section(String title, String subtitle) {
        JPanel panel = transparent(new GridLayout(2, 1, 0, 5)); panel.setBorder(new EmptyBorder(15, 18, 4, 18));
        panel.add(label(title, 12, TEXT, true)); panel.add(label(subtitle, 11, MUTED, false)); return panel;
    }
    private static JButton button(String text) {
        JButton button = new JButton(text); style(button); button.setFocusPainted(false);
        button.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(BORDER), new EmptyBorder(7, 12, 7, 12)));
        return button;
    }
    private static void style(JComponent component) {
        component.setBackground(PANEL); component.setForeground(TEXT); component.setFont(font(12, false));
        if (component instanceof JTextField field) { field.setCaretColor(GREEN); field.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(BORDER), new EmptyBorder(5, 8, 5, 8))); }
    }
    private static JSplitPane split(int direction, JComponent a, JComponent b, double weight) {
        JSplitPane split = new JSplitPane(direction, a, b); split.setBorder(null); split.setOpaque(false);
        split.setBackground(BG); split.setDividerSize(14); split.setResizeWeight(weight); split.setContinuousLayout(true); return split;
    }
    private static JTable table(TableModel model) {
        JTable table = new JTable(model); table.setBackground(PANEL); table.setForeground(TEXT); table.setFont(font(12, false));
        table.setRowHeight(29); table.setShowGrid(false); table.setIntercellSpacing(new Dimension(0, 0));
        table.setFillsViewportHeight(true); table.setSelectionBackground(new Color(33, 67, 77)); table.setSelectionForeground(TEXT);
        table.setAutoCreateRowSorter(true); table.getTableHeader().setReorderingAllowed(false);
        table.getTableHeader().setFont(font(10, true)); table.getTableHeader().setBackground(BORDER); table.getTableHeader().setForeground(TEXT);
        table.getTableHeader().setDefaultRenderer(new DefaultTableCellRenderer() {
            @Override public Component getTableCellRendererComponent(JTable t, Object value, boolean selected, boolean focus, int row, int column) {
                super.getTableCellRendererComponent(t, value, selected, focus, row, column);
                setBackground(BORDER); setForeground(MUTED); setFont(font(10, true));
                setBorder(new EmptyBorder(7, 12, 7, 8)); return this;
            }
        });
        DefaultTableCellRenderer renderer = new DefaultTableCellRenderer() {
            @Override public Component getTableCellRendererComponent(JTable t, Object value, boolean selected, boolean focus, int row, int column) {
                super.getTableCellRendererComponent(t, value, selected, focus, row, column);
                setBorder(new EmptyBorder(0, 12, 0, 8)); setToolTipText(Objects.toString(value));
                if (!selected) { setBackground(row % 2 == 0 ? PANEL : new Color(20, 31, 43)); setForeground("ESTABLISHED".equals(value) ? GREEN : TEXT); }
                return this;
            }
        };
        table.setDefaultRenderer(Object.class, renderer); table.setDefaultRenderer(Integer.class, renderer); return table;
    }
    private static JScrollPane scroll(JTable table) {
        JScrollPane scroll = new JScrollPane(table); scroll.setBorder(null); scroll.getViewport().setBackground(PANEL);
        scroll.setColumnHeaderView(table.getTableHeader());
        scroll.getVerticalScrollBar().setPreferredSize(new Dimension(9, 0));
        scroll.getVerticalScrollBar().setUI(new javax.swing.plaf.basic.BasicScrollBarUI() {
            @Override protected void configureScrollBarColors() { thumbColor = BORDER.brighter(); trackColor = PANEL; }
            @Override protected JButton createDecreaseButton(int orientation) { return hiddenButton(); }
            @Override protected JButton createIncreaseButton(int orientation) { return hiddenButton(); }
            private JButton hiddenButton() { JButton button = new JButton(); button.setPreferredSize(new Dimension(0, 0)); return button; }
        });
        return scroll;
    }
    private static void quality(Graphics2D g) {
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
    }
    private static void centered(Graphics2D g, String text, int x, int y) { g.drawString(text, x - g.getFontMetrics().stringWidth(text) / 2, y); }
    private static String shorten(String text, int length) { return text.length() <= length ? text : text.substring(0, length - 1) + "…"; }
    public static String bytes(double value) {
        String[] units = {"B", "KiB", "MiB", "GiB", "TiB"}; int i = 0;
        while (value >= 1024 && i < units.length - 1) { value /= 1024; i++; }
        return String.format(Locale.ROOT, value >= 100 || i == 0 ? "%.0f %s" : "%.1f %s", value, units[i]);
    }
    public static String rate(double value) { return bytes(value) + "/s"; }
}
