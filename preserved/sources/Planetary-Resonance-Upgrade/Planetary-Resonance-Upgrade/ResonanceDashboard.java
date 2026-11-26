import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.event.*;
import javax.swing.table.*;
import java.awt.*;
import java.awt.geom.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;

/** Native dashboard; every status and plotted sample comes from GridEngine. */
public final class ResonanceDashboard extends JPanel implements AutoCloseable {
    private static final Color BG = new Color(9, 13, 24), PANEL = new Color(15, 22, 38),
            LINE = new Color(36, 48, 68), TEXT = new Color(229, 238, 249), MUTED = new Color(132, 150, 176),
            CYAN = new Color(74, 221, 239), GREEN = new Color(95, 231, 174), PURPLE = new Color(167, 142, 255),
            AMBER = new Color(255, 191, 104), RED = new Color(255, 115, 137);
    private static final DateTimeFormatter CLOCK = DateTimeFormatter.ofPattern("HH:mm:ss").withZone(ZoneId.systemDefault());
    private final GridEngine engine;
    private GridEngine.Snapshot snapshot;
    private final List<Endpoint> endpoints = new ArrayList<>();
    private LocalTestServer localServer;
    private final DefaultListModel<Endpoint> endpointModel = new DefaultListModel<>();
    private final JList<Endpoint> endpointList = new JList<>(endpointModel);
    private final JLabel connectionCount = value(), successCount = value(), average = value(), sendingCount = value(),
            mode = label("READY / NO ENDPOINTS", 11, MUTED, true), footer = label("Add your endpoints, or try the local HTTP test.", 11, MUTED, false),
            detail = label("Select an endpoint to inspect its latest result.", 11, MUTED, false);
    private final JButton send = button("Send once", CYAN), repeat = button("Start loop", TEXT), cancel = button("Cancel", RED),
            localTest = button("Local HTTP test", PURPLE), add = button("+ Add", TEXT), edit = button("Edit", TEXT),
            remove = button("Remove", MUTED), load = button("Load profile", TEXT), save = button("Save profile", TEXT),
            clear = button("Clear history", MUTED);
    private final JSpinner timeout = spinner(5, 1, 60), concurrency = spinner(4, 1, 8), interval = spinner(10, 5, 300);
    private final JTextField session = field("142857"), signature = field("local-operator");
    private final JTextArea telemetry = area("Hello from Planetary Resonance", 12), preview = area("", 11);
    private final ActivityModel activity = new ActivityModel();
    private final OrbitCanvas orbit = new OrbitCanvas();
    private final LatencyChart chart = new LatencyChart();
    private final javax.swing.Timer timer;
    private boolean looping, disposed;
    private long nextRunNanos;

    public ResonanceDashboard(GridEngine engine) {
        this.engine = engine; snapshot = engine.snapshot();
        setLayout(new BorderLayout(0, 16)); setBackground(BG); setBorder(new EmptyBorder(22, 24, 14, 24));
        setPreferredSize(new Dimension(1460, 980));
        JPanel top = transparent(new BorderLayout(0, 16));
        JPanel heading = transparent(new BorderLayout());
        JPanel identity = transparent(new GridLayout(2, 1, 0, 7));
        identity.add(label("PLANETARY RESONANCE", 25, TEXT, true));
        identity.add(label("HTTP DISPATCH ENGINE    /    LIVE ENDPOINT TELEMETRY", 10, MUTED, true));
        heading.add(identity, BorderLayout.WEST); heading.add(mode, BorderLayout.EAST); top.add(heading, BorderLayout.NORTH);

        JPanel middle = transparent(new BorderLayout(0, 16));
        JPanel toolbar = transparent(new BorderLayout());
        JPanel leftActions = transparent(new FlowLayout(FlowLayout.LEFT, 8, 0));
        leftActions.add(send); leftActions.add(repeat); leftActions.add(cancel);
        leftActions.add(label("EVERY", 10, MUTED, true)); leftActions.add(interval); leftActions.add(label("SEC", 10, MUTED, true));
        JPanel rightActions = transparent(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        rightActions.add(localTest); rightActions.add(load); rightActions.add(save);
        toolbar.add(leftActions, BorderLayout.WEST); toolbar.add(rightActions, BorderLayout.EAST); middle.add(toolbar, BorderLayout.NORTH);
        JPanel metrics = transparent(new GridLayout(1, 4, 12, 0));
        metrics.add(metric("CONFIGURED ENDPOINTS", connectionCount, "Up to 24 configured destinations", PURPLE));
        metrics.add(metric("ACCEPTED / COMPLETED", successCount, "Confirmed HTTP 2xx responses", GREEN));
        metrics.add(metric("MEAN DURATION", average, "Latest 120 completed attempts", CYAN));
        metrics.add(metric("IN FLIGHT / QUEUED", sendingCount, "Bounded request execution", TEXT));
        middle.add(metrics, BorderLayout.CENTER); top.add(middle, BorderLayout.CENTER); add(top, BorderLayout.NORTH);

        JPanel map = panel(new BorderLayout());
        map.add(section("RESONANCE TOPOLOGY", "Configured routes · schematic layout, not geographic location"), BorderLayout.NORTH);
        map.add(orbit, BorderLayout.CENTER);
        JPanel legend = transparent(new FlowLayout(FlowLayout.LEFT, 18, 10));
        legend.add(label("●  Accepted", 10, GREEN, true)); legend.add(label("●  Sending", 10, CYAN, true));
        legend.add(label("●  Queued", 10, PURPLE, true)); legend.add(label("●  Error / timeout", 10, RED, true));
        map.add(legend, BorderLayout.SOUTH); map.setMinimumSize(new Dimension(540, 280));
        map.setPreferredSize(new Dimension(900, 360));

        JPanel endpointPanel = panel(new BorderLayout(0, 8));
        endpointPanel.add(section("DESTINATIONS", "Choose an endpoint to inspect its result"), BorderLayout.NORTH);
        endpointList.setBackground(PANEL); endpointList.setForeground(TEXT); endpointList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        endpointList.setFixedCellHeight(57); endpointList.setCellRenderer(new EndpointRenderer());
        endpointList.addListSelectionListener(e -> { updateDetail(); orbit.repaint(); });
        endpointPanel.add(scroll(endpointList), BorderLayout.CENTER);
        JPanel endpointBottom = transparent(new BorderLayout(0, 10));
        endpointBottom.setBorder(new EmptyBorder(0, 14, 12, 14));
        JPanel editActions = transparent(new FlowLayout(FlowLayout.LEFT, 6, 0)); editActions.add(add); editActions.add(edit); editActions.add(remove);
        endpointBottom.add(editActions, BorderLayout.NORTH);
        detail.setPreferredSize(new Dimension(340, 31)); endpointBottom.add(detail, BorderLayout.CENTER);
        JPanel settings = transparent(new FlowLayout(FlowLayout.LEFT, 8, 0));
        settings.add(label("TIMEOUT", 10, MUTED, true)); settings.add(timeout); settings.add(label("SEC", 10, MUTED, true));
        settings.add(label("WORKERS", 10, MUTED, true)); settings.add(concurrency);
        endpointBottom.add(settings, BorderLayout.SOUTH); endpointPanel.add(endpointBottom, BorderLayout.SOUTH);
        endpointPanel.setMinimumSize(new Dimension(370, 280)); endpointPanel.setPreferredSize(new Dimension(390, 360));
        JSplitPane upper = split(JSplitPane.HORIZONTAL_SPLIT, map, endpointPanel, .69);

        JPanel bottom = panel(new BorderLayout(0, 0));
        JPanel nav = transparent(new FlowLayout(FlowLayout.LEFT, 8, 10)); nav.setBorder(new EmptyBorder(0, 8, 0, 8));
        JButton activityButton = button("Activity", CYAN), payloadButton = button("Request composer", MUTED), export = button("Export activity", MUTED);
        nav.add(activityButton); nav.add(payloadButton); nav.add(export); nav.add(clear); bottom.add(nav, BorderLayout.NORTH);
        CardLayout cards = new CardLayout(); JPanel body = transparent(cards);
        JTable table = table(activity); table.getColumnModel().getColumn(0).setMaxWidth(90); table.getColumnModel().getColumn(2).setMaxWidth(115);
        table.getColumnModel().getColumn(0).setPreferredWidth(85);
        table.getColumnModel().getColumn(1).setPreferredWidth(180);
        table.getColumnModel().getColumn(2).setMinWidth(105); table.getColumnModel().getColumn(2).setPreferredWidth(115);
        table.getColumnModel().getColumn(3).setPreferredWidth(440);
        JSplitPane activityArea = split(JSplitPane.HORIZONTAL_SPLIT, scroll(table), chart, .66);
        body.add(activityArea, "activity"); body.add(composer(), "payload"); bottom.add(body, BorderLayout.CENTER);
        bottom.setMinimumSize(new Dimension(800, 235));
        activityButton.addActionListener(e -> { cards.show(body, "activity"); activityButton.setForeground(CYAN); payloadButton.setForeground(MUTED); });
        payloadButton.addActionListener(e -> { cards.show(body, "payload"); payloadButton.setForeground(CYAN); activityButton.setForeground(MUTED); });
        JSplitPane vertical = split(JSplitPane.VERTICAL_SPLIT, upper, bottom, .64); add(vertical, BorderLayout.CENTER);
        add(footer, BorderLayout.SOUTH);

        send.addActionListener(e -> dispatch(false));
        repeat.addActionListener(e -> {
            if (looping) { looping = false; refresh(); }
            else { looping = true; dispatch(true); }
        });
        cancel.addActionListener(e -> { looping = false; engine.cancel(); refresh(); });
        localTest.addActionListener(e -> localTest());
        add.addActionListener(e -> editEndpoint(false)); edit.addActionListener(e -> editEndpoint(true));
        remove.addActionListener(e -> { int index = endpointList.getSelectedIndex(); if (index >= 0) { List<Endpoint> next = new ArrayList<>(endpoints); next.remove(index); setEndpoints(next); } });
        load.addActionListener(e -> loadProfile()); save.addActionListener(e -> saveProfile());
        clear.addActionListener(e -> engine.clearHistory()); export.addActionListener(e -> exportActivity());
        timer = new javax.swing.Timer(50, e -> {
            if (disposed) return;
            if (looping && !snapshot.active() && System.nanoTime() >= nextRunNanos) dispatch(true);
            if (isShowing()) orbit.repaint();
            updateFooter();
        });
        engine.addListener(this::accept); refresh(); updatePreview(); timer.start();
    }

    private JPanel composer() {
        JPanel editor = transparent(new BorderLayout(14, 10)); editor.setBorder(new EmptyBorder(4, 16, 14, 16));
        JPanel inputs = transparent(new BorderLayout(0, 10));
        JPanel fields = transparent(new GridLayout(1, 2, 12, 0));
        fields.add(labeled("SESSION HEIGHT", session)); fields.add(labeled("SIGNATURE LABEL", signature)); inputs.add(fields, BorderLayout.NORTH);
        telemetry.setLineWrap(true); telemetry.setWrapStyleWord(true); inputs.add(labeled("TELEMETRY TEXT", scroll(telemetry)), BorderLayout.CENTER);
        preview.setEditable(false); preview.setLineWrap(true); preview.setWrapStyleWord(true);
        editor.add(split(JSplitPane.HORIZONTAL_SPLIT, inputs, labeled("JSON REQUEST PREVIEW", scroll(preview)), .47), BorderLayout.CENTER);
        DocumentListener update = new DocumentListener() {
            public void insertUpdate(DocumentEvent e) { updatePreview(); } public void removeUpdate(DocumentEvent e) { updatePreview(); }
            public void changedUpdate(DocumentEvent e) { updatePreview(); }
        };
        session.getDocument().addDocumentListener(update); signature.getDocument().addDocumentListener(update); telemetry.getDocument().addDocumentListener(update);
        return editor;
    }
    private DispatchPayload payload() { return new DispatchPayload(Long.parseLong(session.getText().strip()), signature.getText(), telemetry.getText()); }
    private void updatePreview() {
        try { DispatchPayload draft = payload(); draft.bytes(); preview.setForeground(TEXT); preview.setText(draft.json()); }
        catch (Exception failure) { preview.setForeground(AMBER); preview.setText("Correct the request before sending:\n" + message(failure)); }
    }
    private void dispatch(boolean automatic) {
        try {
            engine.dispatch(payload(), Duration.ofSeconds((int) timeout.getValue()), (int) concurrency.getValue());
            nextRunNanos = System.nanoTime() + Duration.ofSeconds((int) interval.getValue()).toNanos();
        } catch (Exception failure) { looping = false; showError(failure); }
        refresh();
    }
    public void setEndpoints(List<Endpoint> next) {
        engine.configure(next); endpoints.clear(); endpoints.addAll(next);
        UUID selection = endpointList.getSelectedValue() == null ? null : endpointList.getSelectedValue().id();
        endpointModel.clear(); next.forEach(endpointModel::addElement);
        for (int i = 0; i < next.size(); i++) if (next.get(i).id().equals(selection)) endpointList.setSelectedIndex(i);
        if (endpointList.getSelectedIndex() < 0 && !next.isEmpty()) endpointList.setSelectedIndex(0);
        refresh();
    }
    public void accept(GridEngine.Snapshot update) {
        if (!SwingUtilities.isEventDispatchThread()) { SwingUtilities.invokeLater(() -> accept(update)); return; }
        if (disposed || update.revision() < snapshot.revision()) return;
        snapshot = update; refresh();
    }
    private void refresh() {
        boolean busy = snapshot.active() || looping;
        connectionCount.setText("" + snapshot.nodes().size()); successCount.setText(snapshot.succeeded() + " / " + snapshot.completed());
        average.setText(snapshot.history().isEmpty() ? "—" : duration(snapshot.averageMs()));
        sendingCount.setText(snapshot.sending() + " / " + snapshot.queued());
        send.setEnabled(!busy && !endpoints.isEmpty()); repeat.setEnabled(looping || !snapshot.active() && !endpoints.isEmpty());
        repeat.setText(looping ? "Stop loop" : "Start loop"); cancel.setEnabled(snapshot.active() || looping);
        for (JComponent component : List.of(add, edit, remove, load, localTest, timeout, concurrency, interval, session, signature, telemetry, clear)) component.setEnabled(!busy);
        edit.setEnabled(!busy && endpointList.getSelectedIndex() >= 0); remove.setEnabled(!busy && endpointList.getSelectedIndex() >= 0);
        mode.setText(snapshot.active() ? "●  DISPATCHING / BATCH " + snapshot.batch() : looping ? "●  LOOP ACTIVE" : endpoints.isEmpty() ? "READY / NO ENDPOINTS" : "●  READY / " + endpoints.size() + " ENDPOINTS");
        mode.setForeground(snapshot.active() ? CYAN : looping ? GREEN : MUTED);
        activity.fireTableDataChanged(); endpointList.repaint(); updateDetail(); chart.repaint(); orbit.repaint(); updateFooter();
    }
    private void updateFooter() {
        String text = endpoints.isEmpty() ? "Add your endpoints, or try the local HTTP test." : "POST / JSON  ·  Real HTTP results  ·  No automatic retries or redirects";
        if (localServer != null) text += "  ·  Local test server running";
        if (looping && !snapshot.active()) text += "  ·  Next batch in " + Math.max(0, (nextRunNanos - System.nanoTime() + 999_999_999) / 1_000_000_000) + "s";
        if (snapshot.cancelled() > 0) text += "  ·  " + snapshot.cancelled() + " cancelled";
        footer.setText(text); footer.setToolTipText(text);
    }
    private void updateDetail() {
        Endpoint selected = endpointList.getSelectedValue();
        GridEngine.Result result = selected == null ? null : snapshot.nodes().stream().filter(r -> r.endpoint().id().equals(selected.id())).findFirst().orElse(null);
        String text = result == null ? "Select an endpoint to inspect its latest result." : result.state().label() + " · " + result.detail();
        detail.setText(shorten(text, 65)); detail.setToolTipText(text); detail.setForeground(result == null ? MUTED : color(result.state()));
        boolean enabled = !snapshot.active() && !looping && selected != null; edit.setEnabled(enabled); remove.setEnabled(enabled);
    }
    private void editEndpoint(boolean editing) {
        Endpoint existing = editing ? endpointList.getSelectedValue() : null;
        if (editing && existing == null) return;
        JTextField name = new JTextField(existing == null ? "" : existing.name(), 28), url = new JTextField(existing == null ? "https://" : existing.uri().toString(), 34);
        JPanel form = new JPanel(new GridLayout(4, 1, 0, 6)); form.add(new JLabel("Name")); form.add(name); form.add(new JLabel("HTTP(S) URL")); form.add(url);
        if (JOptionPane.showConfirmDialog(this, form, editing ? "Edit endpoint" : "Add endpoint", JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE) != JOptionPane.OK_OPTION) return;
        try {
            Endpoint endpoint = new Endpoint(existing == null ? UUID.randomUUID() : existing.id(), name.getText(), java.net.URI.create(url.getText().strip()));
            List<Endpoint> next = new ArrayList<>(endpoints); if (editing) next.set(endpointList.getSelectedIndex(), endpoint); else next.add(endpoint);
            setEndpoints(next);
        } catch (Exception failure) { showError(failure); }
    }
    private void localTest() {
        if (!endpoints.isEmpty() && JOptionPane.showConfirmDialog(this, "Replace the current endpoints with three local test routes?\nThe test will send the current request to a server on this PC.", "Local HTTP test", JOptionPane.OK_CANCEL_OPTION) != JOptionPane.OK_OPTION) return;
        try {
            payload().bytes();
            if (localServer == null) localServer = new LocalTestServer();
            setEndpoints(localServer.endpoints()); dispatch(false);
        } catch (Exception failure) { showError(failure); }
    }
    private GridConfig config() { return new GridConfig(endpoints, (int)timeout.getValue(), (int)concurrency.getValue(), (int)interval.getValue()); }
    private void saveProfile() {
        Path path = choose("Save endpoint profile", "resonance.properties", true); if (path == null) return;
        try { config().save(path); } catch (Exception failure) { showError(failure); }
    }
    private void loadProfile() {
        Path path = choose("Load endpoint profile", "resonance.properties", false); if (path == null) return;
        try { GridConfig config = GridConfig.load(path); setEndpoints(config.endpoints()); timeout.setValue(config.timeoutSeconds()); concurrency.setValue(config.concurrency()); interval.setValue(config.intervalSeconds()); }
        catch (Exception failure) { showError(failure); }
    }
    private void exportActivity() {
        Path path = choose("Export activity", "resonance-activity.csv", true); if (path == null) return;
        try { Files.writeString(path, csv(snapshot.events()), StandardCharsets.UTF_8); } catch (Exception failure) { showError(failure); }
    }
    private Path choose(String title, String name, boolean saving) {
        JFileChooser chooser = new JFileChooser(); chooser.setDialogTitle(title); chooser.setSelectedFile(new java.io.File(name));
        int result = saving ? chooser.showSaveDialog(this) : chooser.showOpenDialog(this);
        if (result != JFileChooser.APPROVE_OPTION) return null;
        Path path = chooser.getSelectedFile().toPath();
        if (saving && Files.exists(path) && JOptionPane.showConfirmDialog(this, "Replace " + path.getFileName() + "?", "Replace file", JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return null;
        return path;
    }
    public static String csv(List<GridEngine.Event> events) {
        StringBuilder out = new StringBuilder("Time,Endpoint,State,Detail\r\n");
        for (var event : events) {
            String[] fields = {Instant.ofEpochMilli(event.time()).toString(), event.endpoint(), event.state().label(), event.detail()};
            for (int i = 0; i < fields.length; i++) {
                if (i > 0) out.append(','); String value = fields[i];
                if (!value.isEmpty() && "=+-@\t\r".indexOf(value.charAt(0)) >= 0) value = "'" + value;
                out.append('"').append(value.replace("\"", "\"\"")).append('"');
            }
            out.append("\r\n");
        }
        return out.toString();
    }
    private void showError(Exception failure) { JOptionPane.showMessageDialog(this, message(failure), "Unable to continue", JOptionPane.ERROR_MESSAGE); }
    private static String message(Exception failure) { return failure instanceof NumberFormatException ? "Session must be a non-negative whole number." : Objects.toString(failure.getMessage(), failure.getClass().getSimpleName()); }
    @Override public void close() { disposed = true; looping = false; timer.stop(); engine.close(); if (localServer != null) localServer.close(); }

    private final class EndpointRenderer extends JPanel implements ListCellRenderer<Endpoint> {
        private Endpoint endpoint;
        private GridEngine.Result result;
        EndpointRenderer() { setPreferredSize(new Dimension(340, 57)); }
        public Component getListCellRendererComponent(JList<? extends Endpoint> list, Endpoint value, int index, boolean selected, boolean focus) {
            endpoint = value;
            result = snapshot.nodes().stream().filter(r -> r.endpoint().id().equals(value.id())).findFirst().orElse(null);
            setBackground(selected ? new Color(31, 43, 65) : index % 2 == 0 ? PANEL : new Color(18, 27, 43));
            setToolTipText(value.uri().toString()); return this;
        }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); if (endpoint == null) return;
            Graphics2D g = (Graphics2D)graphics.create(); quality(g);
            String status = result == null ? "READY" : result.code() > 0 ? "HTTP " + result.code() : result.state().label();
            g.setFont(font(10, true)); int statusWidth = g.getFontMetrics().stringWidth(status);
            g.setColor(result == null ? MUTED : color(result.state())); g.drawString(status, getWidth() - 14 - statusWidth, 23);
            g.setFont(font(12, true)); g.setColor(TEXT); g.drawString(fit(g, endpoint.name(), getWidth() - statusWidth - 45), 14, 23);
            g.setFont(font(10, false)); g.setColor(MUTED); g.drawString(fit(g, endpoint.uri().toString(), getWidth() - 28), 14, 42);
            g.dispose();
        }
    }
    private final class ActivityModel extends AbstractTableModel {
        private final String[] columns = {"TIME", "ENDPOINT", "STATE", "DETAIL"};
        public int getColumnCount() { return columns.length; } public int getRowCount() { return snapshot.events().size(); }
        public String getColumnName(int column) { return columns[column]; }
        public Object getValueAt(int row, int column) {
            GridEngine.Event event = snapshot.events().get(row);
            return switch (column) { case 0 -> CLOCK.format(Instant.ofEpochMilli(event.time())); case 1 -> event.endpoint(); case 2 -> event.state().label(); default -> event.detail(); };
        }
    }

    private final class OrbitCanvas extends JPanel {
        OrbitCanvas() { setOpaque(false); setToolTipText("Schematic endpoint layout. Lines animate only while a real request is in flight."); }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); Graphics2D g = (Graphics2D) graphics.create(); quality(g);
            int w = getWidth(), h = getHeight(), cx = w / 2, cy = h / 2;
            float radius = Math.max(42, Math.min(h * .32f, w * .15f));
            for (int i = 0; i < 95; i++) {
                int x = (i * 127 + i * i * 13 + 41) % Math.max(1, w), y = (i * 61 + i * i * 7 + 13) % Math.max(1, h);
                g.setColor(new Color(122, 167, 207, i % 5 == 0 ? 85 : 35)); g.fillOval(x, y, i % 5 == 0 ? 2 : 1, i % 5 == 0 ? 2 : 1);
            }
            g.setColor(new Color(34, 51, 72)); g.setStroke(new BasicStroke(1));
            g.draw(new Ellipse2D.Double(cx - radius * 1.45, cy - radius * 1.08, radius * 2.9, radius * 2.16));
            g.draw(new Ellipse2D.Double(cx - radius * 1.2, cy - radius * .7, radius * 2.4, radius * 1.4));
            UUID selected = endpointList.getSelectedValue() == null ? null : endpointList.getSelectedValue().id();
            List<GridEngine.Result> shown = new ArrayList<>(snapshot.nodes().stream().limit(h < 270 ? 6 : 8).toList());
            GridEngine.Result selectedResult = snapshot.nodes().stream().filter(r -> r.endpoint().id().equals(selected)).findFirst().orElse(null);
            if (selectedResult != null && !shown.contains(selectedResult) && !shown.isEmpty()) shown.set(shown.size() - 1, selectedResult);
            for (int i = 0; i < shown.size(); i++) {
                var result = shown.get(i); boolean left = i % 2 == 0;
                int rows = (shown.size() + (left ? 1 : 0)) / 2;
                int x = (int)(w * (left ? .25 : .75)), y = rows == 1 ? cy : 35 + (h - 82) * (i / 2) / (rows - 1);
                Color color = color(result.state());
                g.setColor(new Color(color.getRed(), color.getGreen(), color.getBlue(), 75));
                g.setStroke(new BasicStroke(1.3f)); g.draw(new QuadCurve2D.Double(cx, cy, (cx + x) / 2.0, y, x, y));
                if (result.state() == GridEngine.State.SENDING) {
                    double t = (System.nanoTime() / 1_000_000.0 % 1200) / 1200;
                    double px = (1-t)*(1-t)*cx + 2*(1-t)*t*(cx+x)/2.0 + t*t*x;
                    double py = (1-t)*(1-t)*cy + 2*(1-t)*t*y + t*t*y;
                    g.setColor(CYAN); g.fill(new Ellipse2D.Double(px-3, py-3, 6, 6));
                }
                g.setColor(new Color(color.getRed(), color.getGreen(), color.getBlue(), 25)); g.fillOval(x-17,y-17,34,34);
                g.setColor(color); g.fillOval(x-5,y-5,10,10);
                if (result.endpoint().id().equals(selected)) { g.setStroke(new BasicStroke(1)); g.drawOval(x-12,y-12,24,24); }
                String name = shorten(result.endpoint().name(), Math.max(12, Math.min(22, w / 40)));
                g.setFont(font(11, true)); g.setColor(TEXT);
                g.drawString(name, left ? x - 22 - g.getFontMetrics().stringWidth(name) : x + 22, y - 3);
                String state = result.state().terminal() ? (result.code() > 0 ? result.code() + " · " : "") + duration(result.latencyMs()) : result.state().label();
                g.setFont(font(10, false)); g.setColor(color);
                g.drawString(state, left ? x - 22 - g.getFontMetrics().stringWidth(state) : x + 22, y + 14);
            }
            Paint old = g.getPaint();
            g.setPaint(new RadialGradientPaint(cx, cy, radius * 1.65f, new float[]{0,.55f,1},
                    new Color[]{new Color(49,132,170,48), new Color(34,103,142,25), new Color(15,22,38,0)}));
            g.fill(new Ellipse2D.Double(cx-radius*1.65,cy-radius*1.65,radius*3.3,radius*3.3));
            g.setPaint(new RadialGradientPaint(cx-radius*.3f,cy-radius*.3f,radius*1.7f,new float[]{0,1},
                    new Color[]{new Color(24,70,90),new Color(11,24,43)}));
            g.fill(new Ellipse2D.Double(cx-radius,cy-radius,radius*2,radius*2)); g.setPaint(old);
            Shape oldClip = g.getClip(); g.clip(new Ellipse2D.Double(cx-radius,cy-radius,radius*2,radius*2));
            g.setColor(new Color(80,202,220,70)); g.setStroke(new BasicStroke(.8f));
            for (double s : new double[]{.25,.55,.82}) g.draw(new Ellipse2D.Double(cx-radius*s,cy-radius,radius*s*2,radius*2));
            for (double s : new double[]{-.6,-.3,0,.3,.6}) {
                double half = radius * Math.sqrt(1-s*s);
                g.draw(new Ellipse2D.Double(cx-half,cy+radius*s-radius*.10,half*2,radius*.20));
            }
            g.setClip(oldClip); g.setColor(new Color(87,218,237,150)); g.draw(new Ellipse2D.Double(cx-radius,cy-radius,radius*2,radius*2));
            g.setColor(new Color(9,20,34,220)); g.fillRoundRect(cx-57,cy-22,114,45,12,12);
            g.setFont(font(12,true)); g.setColor(TEXT); centered(g,"LOCAL ENGINE",cx,cy-3);
            g.setFont(font(10,false)); g.setColor(snapshot.active()?CYAN:MUTED); centered(g,snapshot.active()?"DISPATCHING":"READY",cx,cy+14);
            if (shown.isEmpty()) { g.setFont(font(11,false)); g.setColor(MUTED); centered(g,"Add endpoints or run a local HTTP test",cx,Math.min(h-12,(int)(cy+radius+33))); }
            if (snapshot.nodes().size()>shown.size()) { g.setFont(font(10,false)); g.setColor(MUTED); g.drawString("+ "+(snapshot.nodes().size()-shown.size())+" destinations in the list",18,h-12); }
            g.dispose();
        }
    }
    private final class LatencyChart extends JPanel {
        LatencyChart() { setBackground(PANEL); setMinimumSize(new Dimension(240,150)); }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); Graphics2D g=(Graphics2D)graphics.create(); quality(g);
            g.setFont(font(11,true));g.setColor(TEXT);g.drawString("REQUEST DURATION",18,23);
            boolean compact=getHeight()<170;
            g.setFont(font(10,false));g.setColor(MUTED);if(!compact)g.drawString("Recent completed attempts · milliseconds",18,42);
            int left=52,right=Math.max(53,getWidth()-24),top=compact?38:67,bottom=Math.max(top+20,getHeight()-27);
            double maximum=Math.max(100,snapshot.history().stream().mapToDouble(GridEngine.Sample::latencyMs).max().orElse(100)*1.15);
            int steps=bottom-top<70?1:3;
            for(int i=0;i<=steps;i++){int y=top+(bottom-top)*i/steps;g.setColor(LINE);g.drawLine(left,y,right,y);g.setColor(MUTED);g.drawString(""+(int)(maximum*(steps-i)/steps),8,y+3);}
            List<GridEngine.Sample> values=snapshot.history();
            for(int i=0;i<values.size();i++){
                var point=values.get(i);double x=left+(right-left)*(i+1.0)/Math.max(12,values.size());double y=bottom-point.latencyMs()/maximum*(bottom-top);
                g.setColor(point.success()?GREEN:RED);g.setStroke(new BasicStroke(3));g.draw(new Line2D.Double(x,bottom,x,y));g.fill(new Ellipse2D.Double(x-3,y-3,6,6));
            }
            g.setColor(MUTED);g.drawString("older",left,bottom+19);g.drawString("latest",right-29,bottom+19);
            if(values.isEmpty()){g.setFont(font(11,false));centered(g,"Results appear after a request",(left+right)/2,(top+bottom)/2);}
            g.dispose();
        }
    }

    private static Color color(GridEngine.State state) { return switch(state){case SUCCESS->GREEN;case SENDING->CYAN;case QUEUED->PURPLE;case HTTP_ERROR,FAILED,TIMED_OUT->RED;case CANCELLED->AMBER;default->MUTED;}; }
    private static JPanel transparent(LayoutManager layout){JPanel p=new JPanel(layout);p.setOpaque(false);return p;}
    private static JPanel panel(LayoutManager layout){JPanel p=new JPanel(layout);p.setBackground(PANEL);p.setBorder(BorderFactory.createLineBorder(LINE));return p;}
    private static Font font(int size,boolean bold){return new Font("Segoe UI",bold?Font.BOLD:Font.PLAIN,size);}
    private static JLabel label(String text,int size,Color color,boolean bold){JLabel l=new JLabel(text);l.setFont(font(size,bold));l.setForeground(color);return l;}
    private static JLabel value(){return label("—",30,TEXT,true);}
    private static JPanel metric(String name,JLabel value,String note,Color color){JPanel p=panel(new BorderLayout(0,8));p.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(LINE),new EmptyBorder(14,18,14,18)));p.add(label(name,10,MUTED,true),BorderLayout.NORTH);value.setForeground(color);p.add(value);p.add(label(note,10,MUTED,false),BorderLayout.SOUTH);return p;}
    private static JPanel section(String title,String subtitle){JPanel p=transparent(new GridLayout(2,1,0,5));p.setBorder(new EmptyBorder(14,18,4,18));p.add(label(title,11,TEXT,true));p.add(label(subtitle,10,MUTED,false));return p;}
    private static JPanel labeled(String title,JComponent component){JPanel p=transparent(new BorderLayout(0,6));p.add(label(title,10,MUTED,true),BorderLayout.NORTH);p.add(component);return p;}
    private static JButton button(String text,Color color){JButton b=new JButton(text);b.setFont(font(11,true));b.setForeground(color);b.setBackground(PANEL);b.setFocusPainted(false);b.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(LINE),new EmptyBorder(8,12,8,12)));return b;}
    private static JTextField field(String text){JTextField f=new JTextField(text);f.setFont(font(12,false));f.setForeground(TEXT);f.setCaretColor(CYAN);f.setBackground(BG);f.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(LINE),new EmptyBorder(6,8,6,8)));return f;}
    private static JTextArea area(String text,int size){JTextArea a=new JTextArea(text);a.setFont(new Font("Consolas",Font.PLAIN,size));a.setForeground(TEXT);a.setCaretColor(CYAN);a.setBackground(BG);a.setBorder(new EmptyBorder(8,10,8,10));return a;}
    private static JSpinner spinner(int value,int min,int max){JSpinner s=new JSpinner(new SpinnerNumberModel(value,min,max,1));s.setPreferredSize(new Dimension(59,30));s.setFont(font(11,false));JFormattedTextField f=((JSpinner.DefaultEditor)s.getEditor()).getTextField();f.setBackground(PANEL);f.setForeground(TEXT);f.setCaretColor(CYAN);s.setBorder(BorderFactory.createLineBorder(LINE));return s;}
    private static JSplitPane split(int orientation,JComponent a,JComponent b,double weight){JSplitPane s=new JSplitPane(orientation,a,b){private boolean positioned;@Override public void doLayout(){if(!positioned&&getWidth()>0&&getHeight()>0){setDividerLocation(weight);positioned=true;}super.doLayout();}};s.setBorder(null);s.setBackground(BG);s.setDividerSize(13);s.setResizeWeight(weight);s.setContinuousLayout(true);return s;}
    private static JScrollPane scroll(JComponent child){JScrollPane s=new JScrollPane(child);s.setBorder(null);s.getViewport().setBackground(PANEL);if(child instanceof JTable t)s.setColumnHeaderView(t.getTableHeader());s.getVerticalScrollBar().setPreferredSize(new Dimension(9,0));s.getVerticalScrollBar().setUI(new javax.swing.plaf.basic.BasicScrollBarUI(){protected void configureScrollBarColors(){thumbColor=LINE.brighter();trackColor=PANEL;}protected JButton createDecreaseButton(int o){return empty();}protected JButton createIncreaseButton(int o){return empty();}private JButton empty(){JButton b=new JButton();b.setPreferredSize(new Dimension(0,0));return b;}});return s;}
    private static JTable table(TableModel model){JTable t=new JTable(model);t.setBackground(PANEL);t.setForeground(TEXT);t.setFont(font(11,false));t.setRowHeight(29);t.setShowGrid(false);t.setFillsViewportHeight(true);t.setIntercellSpacing(new Dimension(0,0));t.setSelectionBackground(new Color(35,54,74));t.setSelectionForeground(TEXT);t.setAutoCreateRowSorter(true);t.getTableHeader().setReorderingAllowed(false);t.getTableHeader().setDefaultRenderer(new DefaultTableCellRenderer(){public Component getTableCellRendererComponent(JTable table,Object v,boolean s,boolean f,int r,int c){super.getTableCellRendererComponent(table,v,s,f,r,c);setBackground(LINE);setForeground(MUTED);setFont(font(9,true));setBorder(new EmptyBorder(7,12,7,8));return this;}});t.setDefaultRenderer(Object.class,new DefaultTableCellRenderer(){public Component getTableCellRendererComponent(JTable table,Object v,boolean s,boolean f,int r,int c){super.getTableCellRendererComponent(table,v,s,f,r,c);setBorder(new EmptyBorder(0,12,0,8));setToolTipText(Objects.toString(v));if(!s){setBackground(r%2==0?PANEL:new Color(18,27,43));setForeground(TEXT);if(c==2)try{setForeground(color(GridEngine.State.valueOf(v.toString().replace(' ','_'))));}catch(Exception ignored){}}return this;}});return t;}
    private static void quality(Graphics2D g){g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,RenderingHints.VALUE_TEXT_ANTIALIAS_ON);}
    private static void centered(Graphics2D g,String s,int x,int y){g.drawString(s,x-g.getFontMetrics().stringWidth(s)/2,y);}
    private static String shorten(String s,int max){return s.length()<=max?s:s.substring(0,max-1)+"…";}
    private static String fit(Graphics2D g,String text,int width){if(g.getFontMetrics().stringWidth(text)<=width)return text;int count=text.length();while(count>0&&g.getFontMetrics().stringWidth(text.substring(0,count)+"…")>width)count--;return text.substring(0,count)+"…";}
    private static String duration(double ms){return ms>=1000?String.format(Locale.ROOT,"%.2f s",ms/1000):String.format(Locale.ROOT,"%.0f ms",ms);}
}
