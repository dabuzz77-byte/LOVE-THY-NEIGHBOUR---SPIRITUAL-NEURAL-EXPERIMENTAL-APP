import javax.swing.*;
import javax.swing.border.*;
import javax.swing.event.*;
import javax.swing.table.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.util.*;
import java.util.List;

/** Responsive Swing dashboard with accessible native controls and custom vector charts. */
@SuppressWarnings("serial") // Swing views are never serialized.
public final class LANMatrixCanvas extends JPanel {
    private static final long serialVersionUID = 1L;
    static final Color BG = new Color(10, 17, 29);
    static final Color PANEL = new Color(17, 28, 44);
    static final Color BORDER = new Color(36, 52, 72);
    static final Color TEXT = new Color(232, 241, 249);
    static final Color MUTED = new Color(144, 165, 186);
    static final Color CYAN = new Color(72, 217, 211);
    static final Color BLUE = new Color(99, 160, 255);
    static final Color PURPLE = new Color(185, 149, 255);
    static final Color AMBER = new Color(244, 194, 107);
    private final QuantumTernaryBinaryCore core;
    private final LocalNetworkLatchingEngine network;
    private final JPanel actions = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
    private final JLabel receiverState = label("STARTING", 12, CYAN);
    private final JLabel footer = label("Waiting for receiver...", 12, MUTED);
    private final MetricCard deviceCard = new MetricCard("CONNECTED DEVICES", "0", "Android + iOS", CYAN);
    private final MetricCard frameCard = new MetricCard("TELEMETRY FRAMES", "0", "Accepted this session", BLUE);
    private final MetricCard cpuCard = new MetricCard("HOST CPU", "--", "Real system utilization", PURPLE);
    private final MetricCard heapCard = new MetricCard("JAVA HEAP", "--", "Used / maximum memory", AMBER);
    private final HistoryChart history = new HistoryChart();
    private final StateChart state;
    private final DeviceTableModel model = new DeviceTableModel();
    private final JTable table = new JTable(model);
    private final TableRowSorter<DeviceTableModel> sorter = new TableRowSorter<>(model);
    private final JTextField search = new JTextField(15);
    private final JComboBox<String> platform = new JComboBox<>(new String[] {"All platforms", "Android", "iOS"});
    private final JTextArea eventLog = new JTextArea();
    private final JLabel listInfo = label("0 devices", 12, MUTED);
    private final JLabel emptyMessage = label("No devices yet. Use Connect a device to get started.", 13, MUTED);
    private long lastSample;
    private final JPanel metricGrid = transparent(new GridLayout(1, 4, 14, 0));
    private final JPanel chartGrid = transparent(new GridLayout(1, 2, 16, 0));
    private JSplitPane lowerSplit;
    private int layoutWidth;

    public static void configureTheme() {
        Font font = new Font("Segoe UI", Font.PLAIN, 13);
        for (String key : new String[] {"Button.font", "Label.font", "Table.font", "TextField.font",
                "ComboBox.font", "OptionPane.messageFont", "OptionPane.buttonFont"}) UIManager.put(key, font);
        UIManager.put("ToolTip.background", PANEL);
        UIManager.put("ToolTip.foreground", TEXT);
    }

    public LANMatrixCanvas(QuantumTernaryBinaryCore core, LocalNetworkLatchingEngine network) {
        this.core = core;
        this.network = network;
        state = new StateChart(core);
        setBackground(BG);
        setLayout(new BorderLayout(0, 22));
        setBorder(new EmptyBorder(26, 30, 18, 30));
        add(buildHeader(), BorderLayout.NORTH);
        JPanel body = transparent(new BorderLayout(0, 20));
        JPanel upper = transparent(new BorderLayout(0, 18));
        JPanel metrics = metricGrid;
        metrics.add(deviceCard); metrics.add(frameCard); metrics.add(cpuCard); metrics.add(heapCard);
        metrics.setPreferredSize(new Dimension(0, 116));
        upper.add(metrics, BorderLayout.NORTH);
        JPanel charts = chartGrid;
        charts.add(history); charts.add(state);
        charts.setPreferredSize(new Dimension(0, 212));
        upper.add(charts, BorderLayout.CENTER);
        body.add(upper, BorderLayout.NORTH);
        JSplitPane lower = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, buildDevices(), buildEvents());
        lowerSplit = lower;
        lower.setResizeWeight(0.73);
        lower.setDividerSize(12);
        lower.setBorder(null);
        lower.setOpaque(false);
        lower.setContinuousLayout(true);
        body.add(lower, BorderLayout.CENTER);
        add(body, BorderLayout.CENTER);
        JPanel bottom = transparent(new BorderLayout());
        bottom.add(footer, BorderLayout.WEST);
        bottom.add(label("LOCAL NETWORK  /  ANDROID + iOS", 11, MUTED), BorderLayout.EAST);
        add(bottom, BorderLayout.SOUTH);
    }

    @Override public void doLayout() {
        boolean compact = getHeight() < 820;
        metricGrid.setPreferredSize(new Dimension(0, compact ? 108 : 116));
        chartGrid.setPreferredSize(new Dimension(0, compact ? 150 : 212));
        if (lowerSplit != null && layoutWidth != getWidth()) {
            lowerSplit.setDividerLocation((int) ((getWidth() - 72) * 0.70));
            layoutWidth = getWidth();
        }
        super.doLayout();
    }

    private JPanel buildHeader() {
        JPanel header = transparent(new BorderLayout(0, 15));
        JPanel top = transparent(new BorderLayout());
        JLabel eyebrow = label("LAN  /  OBSERVATORY", 12, CYAN);
        eyebrow.setFont(new Font("Segoe UI", Font.BOLD, 12));
        top.add(eyebrow, BorderLayout.WEST);
        top.add(receiverState, BorderLayout.EAST);
        header.add(top, BorderLayout.NORTH);
        JPanel heading = transparent(new BorderLayout(20, 0));
        JPanel title = transparent(new BorderLayout(0, 5));
        title.add(label("Your network, in view.", 30, TEXT), BorderLayout.NORTH);
        title.add(label("Live mobile telemetry and host performance in one workspace.", 13, MUTED), BorderLayout.SOUTH);
        heading.add(title, BorderLayout.WEST);
        actions.setOpaque(false);
        JPanel controls = transparent(new BorderLayout());
        controls.setBorder(new EmptyBorder(15, 0, 0, 0));
        controls.add(actions, BorderLayout.EAST);
        heading.add(controls, BorderLayout.CENTER);
        header.add(heading, BorderLayout.CENTER);
        return header;
    }

    public void addAction(JButton button) {
        styleButton(button);
        actions.add(button);
    }

    static void styleButton(JButton button) {
        button.setBackground(new Color(30, 48, 66));
        button.setForeground(TEXT);
        button.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        button.setFocusPainted(true);
        button.setBorder(BorderFactory.createCompoundBorder(new LineBorder(BORDER, 1, true),
                new EmptyBorder(9, 12, 9, 12)));
        button.setContentAreaFilled(false);
        button.setOpaque(true);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
    }

    private JPanel buildDevices() {
        JPanel panel = card(new BorderLayout(0, 12));
        panel.setMinimumSize(new Dimension(600, 150));
        JPanel header = transparent(new BorderLayout(12, 0));
        JPanel titles = transparent(new BorderLayout(0, 4));
        titles.add(label("Device activity", 18, TEXT), BorderLayout.NORTH);
        titles.add(listInfo, BorderLayout.SOUTH);
        header.add(titles, BorderLayout.WEST);
        JPanel filters = transparent(new FlowLayout(FlowLayout.RIGHT, 8, 2));
        filters.add(label("Search", 12, MUTED));
        search.setToolTipText("Search by device ID or IP address");
        search.getAccessibleContext().setAccessibleName("Search devices");
        search.setBackground(BG); search.setForeground(TEXT); search.setCaretColor(CYAN);
        search.setBorder(new CompoundBorder(new LineBorder(BORDER), new EmptyBorder(6, 8, 6, 8)));
        platform.getAccessibleContext().setAccessibleName("Platform filter");
        platform.setBackground(BG); platform.setForeground(TEXT);
        platform.setBorder(new LineBorder(BORDER));
        platform.setUI(new javax.swing.plaf.basic.BasicComboBoxUI() {
            @Override protected JButton createArrowButton() {
                return new javax.swing.plaf.basic.BasicArrowButton(SwingConstants.SOUTH, BG, BG, MUTED, BG);
            }
        });
        platform.setPreferredSize(new Dimension(122, 32));
        filters.add(search); filters.add(platform);
        header.add(filters, BorderLayout.EAST);
        panel.add(header, BorderLayout.NORTH);
        table.setRowSorter(sorter);
        table.setBackground(PANEL); table.setForeground(TEXT);
        table.setSelectionBackground(new Color(35, 67, 86)); table.setSelectionForeground(Color.WHITE);
        table.setGridColor(BORDER);
        table.setShowVerticalLines(false);
        table.setShowHorizontalLines(true);
        table.setRowHeight(44);
        table.setIntercellSpacing(new Dimension(0, 1));
        table.setFillsViewportHeight(true);
        table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        table.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        table.getTableHeader().setReorderingAllowed(false);
        table.getTableHeader().setPreferredSize(new Dimension(0, 34));
        table.getTableHeader().setDefaultRenderer(new DefaultTableCellRenderer() {
            @Override public Component getTableCellRendererComponent(JTable t, Object value, boolean selected,
                    boolean focus, int row, int column) {
                super.getTableCellRendererComponent(t, value, selected, focus, row, column);
                setBackground(BG); setForeground(MUTED);
                setFont(new Font("Segoe UI", Font.BOLD, 10));
                setBorder(new EmptyBorder(0, 10, 0, 4));
                return this;
            }
        });
        DefaultTableCellRenderer renderer = new DefaultTableCellRenderer() {
            @Override public Component getTableCellRendererComponent(JTable t, Object value, boolean selected,
                    boolean focus, int row, int column) {
                super.getTableCellRendererComponent(t, value, selected, focus, row, column);
                setBorder(new EmptyBorder(0, 10, 0, 4));
                setBackground(selected ? t.getSelectionBackground() : row % 2 == 0 ? PANEL : new Color(20, 32, 48));
                setForeground(selected ? Color.WHITE : column == 1 ? ("ANDROID".equals(value) ? CYAN : PURPLE)
                        : column == 3 ? ("Streaming".equals(value) ? CYAN : AMBER) : TEXT);
                if (value instanceof Double) setText(String.format(Locale.ROOT, "%.3f", value));
                setToolTipText(value == null ? null : String.valueOf(value));
                return this;
            }
        };
        table.setDefaultRenderer(Object.class, renderer);
        table.setDefaultRenderer(Double.class, renderer);
        table.setDefaultRenderer(Long.class, renderer);
        int[] widths = {175, 90, 115, 110, 75, 75, 65};
        for (int i = 0; i < widths.length; i++) table.getColumnModel().getColumn(i).setPreferredWidth(widths[i]);
        JScrollPane scroll = new JScrollPane(table);
        scroll.setColumnHeaderView(table.getTableHeader());
        scroll.setBorder(new LineBorder(BORDER));
        scroll.getViewport().setBackground(PANEL);
        styleScrollPane(scroll);
        panel.add(scroll, BorderLayout.CENTER);
        JPanel below = transparent(new BorderLayout(8, 0));
        below.add(emptyMessage, BorderLayout.CENTER);
        JButton details = new JButton("View details");
        styleButton(details);
        details.addActionListener(event -> showDetails());
        below.add(details, BorderLayout.EAST);
        panel.add(below, BorderLayout.SOUTH);
        table.addMouseListener(new MouseAdapter() {
            @Override public void mouseClicked(MouseEvent event) { if (event.getClickCount() == 2) showDetails(); }
        });
        table.getInputMap().put(KeyStroke.getKeyStroke("ENTER"), "details");
        table.getActionMap().put("details", new AbstractAction() {
            @Override public void actionPerformed(ActionEvent event) { showDetails(); }
        });
        search.getDocument().addDocumentListener(new DocumentListener() {
            public void insertUpdate(DocumentEvent event) { applyFilter(); }
            public void removeUpdate(DocumentEvent event) { applyFilter(); }
            public void changedUpdate(DocumentEvent event) { applyFilter(); }
        });
        platform.addActionListener(event -> applyFilter());
        return panel;
    }

    private JPanel buildEvents() {
        JPanel panel = card(new BorderLayout(0, 10));
        panel.setMinimumSize(new Dimension(240, 150));
        JPanel header = transparent(new BorderLayout(0, 4));
        header.add(label("Receiver journal", 18, TEXT), BorderLayout.NORTH);
        header.add(label("Connections, expiry and diagnostics", 12, MUTED), BorderLayout.SOUTH);
        panel.add(header, BorderLayout.NORTH);
        eventLog.setEditable(false);
        eventLog.setBackground(PANEL); eventLog.setForeground(MUTED);
        eventLog.setFont(new Font("Consolas", Font.PLAIN, 12));
        eventLog.setLineWrap(true); eventLog.setWrapStyleWord(true);
        eventLog.setMargin(new Insets(4, 0, 4, 0));
        eventLog.setText("Receiver events will appear here.");
        JScrollPane scroll = new JScrollPane(eventLog);
        scroll.setBorder(null); scroll.getViewport().setBackground(PANEL);
        styleScrollPane(scroll);
        panel.add(scroll, BorderLayout.CENTER);
        panel.add(label("Most recent first  /  last 100 events", 11, MUTED), BorderLayout.SOUTH);
        return panel;
    }

    private void applyFilter() {
        final String query = search.getText().trim().toLowerCase(Locale.ROOT);
        final String selectedPlatform = (String) platform.getSelectedItem();
        sorter.setRowFilter(new RowFilter<DeviceTableModel, Integer>() {
            @Override public boolean include(Entry<? extends DeviceTableModel, ? extends Integer> entry) {
                RemoteDeviceNode node = model.rows.get(entry.getIdentifier());
                boolean matchesPlatform = "All platforms".equals(selectedPlatform) || node.platformType.equalsIgnoreCase(selectedPlatform);
                return matchesPlatform && (node.deviceId.toLowerCase(Locale.ROOT).contains(query) || node.ipAddress.contains(query));
            }
        });
        updateListInfo();
    }

    private void updateListInfo() {
        listInfo.setText(table.getRowCount() + " shown / " + model.rows.size() + " connected");
        emptyMessage.setText(model.rows.isEmpty() ? "No devices yet. Use Connect a device to get started."
                : table.getRowCount() == 0 ? "No devices match these filters." : "Select a device for its latest telemetry.");
    }

    public void refresh(HardwareMetricSampler.Sample sample) {
        if (!SwingUtilities.isEventDispatchThread()) throw new IllegalStateException("Refresh on the Swing event thread");
        String selected = table.getSelectedRow() < 0 ? null : model.rows.get(table.convertRowIndexToModel(table.getSelectedRow())).deviceId;
        model.rows = new ArrayList<>(network.getLatchedDevices().values());
        model.fireTableDataChanged();
        if (selected != null) {
            for (int i = 0; i < model.rows.size(); i++) if (model.rows.get(i).deviceId.equals(selected)) {
                int view = table.convertRowIndexToView(i);
                if (view >= 0) table.setRowSelectionInterval(view, view);
                break;
            }
        }
        updateListInfo();
        long android = model.rows.stream().filter(node -> node.platformType.equals("ANDROID")).count();
        deviceCard.setValue(Integer.toString(model.rows.size()), android + " Android  /  " + (model.rows.size() - android) + " iOS");
        frameCard.setValue(Long.toString(network.getAcceptedCount()), network.getRejectedCount() + " rejected  /  this session");
        cpuCard.setValue(sample.cpu < 0 ? "N/A" : String.format(Locale.ROOT, "%.0f%%", sample.cpu * 100), "Real system utilization");
        heapCard.setValue(String.format(Locale.ROOT, "%.0f MB", sample.heapUsed / 1048576.0),
                String.format(Locale.ROOT, "of %.0f MB maximum", sample.heapMax / 1048576.0));
        if (sample.timestamp != lastSample) {
            history.push(sample.cpu);
            lastSample = sample.timestamp;
        }
        receiverState.setText((network.isRunning() ? "\u25cf  " : "\u25cb  ") + network.getStatus().toUpperCase(Locale.ROOT));
        receiverState.setForeground(network.isRunning() ? CYAN : AMBER);
        footer.setText("UDP " + network.getDiscoveryPort() + "  /  TCP " + network.getTcpPort()
                + "     |     Uptime " + formatUptime(network.getUptimeSeconds()) + "     |     Refresh 1s");
        String log = String.join("\n\n", network.getEvents());
        if (!eventLog.getText().equals(log)) {
            eventLog.setText(log.isEmpty() ? "Receiver events will appear here." : log);
            eventLog.setCaretPosition(0);
        }
        state.repaint();
    }

    private static String formatUptime(long seconds) {
        return String.format(Locale.ROOT, "%02d:%02d:%02d", seconds / 3600, seconds / 60 % 60, seconds % 60);
    }

    private void showDetails() {
        if (table.getSelectedRow() < 0) {
            JOptionPane.showMessageDialog(this, "Select a device in the list first.", "Device details", JOptionPane.INFORMATION_MESSAGE);
            return;
        }
        RemoteDeviceNode node = model.rows.get(table.convertRowIndexToModel(table.getSelectedRow()));
        JPanel details = new JPanel(new BorderLayout(0, 12));
        details.setBackground(PANEL);
        details.setBorder(new EmptyBorder(16, 16, 16, 16));
        JTextArea text = new JTextArea("Device: " + node.deviceId + "\nPlatform: " + node.platformType
                + "\nAddress: " + node.ipAddress + "\nStatus: " + node.status(System.currentTimeMillis())
                + "\nMessages: " + node.messageCount + "\nEntropy: "
                + (node.lastTelemetryTimestamp == 0 ? "No telemetry" : String.format(Locale.ROOT, "%.4f bits", node.lastEntropy))
                + "\nSalience: " + (node.lastTelemetryTimestamp == 0 ? "No telemetry" : String.format(Locale.ROOT, "%.3f", node.lastSalience))
                + "\n\nLatest probability snapshot (not a live view):\n" + Arrays.toString(node.getProbabilities()));
        text.setEditable(false); text.setLineWrap(true); text.setWrapStyleWord(true);
        text.setFont(new Font("Segoe UI", Font.PLAIN, 14)); text.setBackground(PANEL); text.setForeground(TEXT);
        JScrollPane scroll = new JScrollPane(text);
        scroll.setPreferredSize(new Dimension(540, 300)); scroll.setBorder(null);
        details.add(scroll);
        JOptionPane.showMessageDialog(this, details, "Device details", JOptionPane.PLAIN_MESSAGE);
    }

    private static JPanel transparent(LayoutManager layout) {
        JPanel panel = new JPanel(layout); panel.setOpaque(false); return panel;
    }

    private static void styleScrollPane(JScrollPane pane) {
        for (JScrollBar bar : new JScrollBar[] {pane.getVerticalScrollBar(), pane.getHorizontalScrollBar()}) {
            bar.setUI(new javax.swing.plaf.basic.BasicScrollBarUI() {
                @Override protected void configureScrollBarColors() { thumbColor = BORDER; trackColor = BG; }
                @Override protected JButton createDecreaseButton(int direction) { return noArrow(); }
                @Override protected JButton createIncreaseButton(int direction) { return noArrow(); }
                private JButton noArrow() {
                    JButton button = new JButton();
                    button.setPreferredSize(new Dimension(0, 0));
                    button.setMinimumSize(new Dimension(0, 0));
                    button.setMaximumSize(new Dimension(0, 0));
                    return button;
                }
            });
            bar.setPreferredSize(bar.getOrientation() == JScrollBar.VERTICAL ? new Dimension(8, 0) : new Dimension(0, 8));
            bar.setUnitIncrement(16);
        }
    }

    private static JPanel card(LayoutManager layout) {
        JPanel panel = new JPanel(layout);
        panel.setBackground(PANEL);
        panel.setBorder(new CompoundBorder(new LineBorder(BORDER, 1, true), new EmptyBorder(18, 18, 16, 18)));
        return panel;
    }

    static JLabel label(String text, int size, Color color) {
        JLabel label = new JLabel(text);
        label.setForeground(color); label.setFont(new Font("Segoe UI", Font.PLAIN, size));
        return label;
    }

    private static Graphics2D quality(Graphics graphics) {
        Graphics2D g = (Graphics2D) graphics.create();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        return g;
    }

    private static void chartShell(Graphics2D g, int w, int h, String title, String subtitle) {
        g.setColor(PANEL); g.fillRoundRect(0, 0, w - 1, h - 1, 18, 18);
        g.setColor(BORDER); g.drawRoundRect(0, 0, w - 1, h - 1, 18, 18);
        g.setFont(new Font("Segoe UI", Font.PLAIN, 17)); g.setColor(TEXT); g.drawString(title, 20, 31);
        g.setFont(new Font("Segoe UI", Font.PLAIN, 11)); g.setColor(MUTED); g.drawString(subtitle, 20, 51);
    }

    private static final class MetricCard extends JPanel {
        private static final long serialVersionUID = 1L;
        final String title;
        final Color accent;
        String value, note;
        MetricCard(String title, String value, String note, Color accent) {
            this.title = title; this.value = value; this.note = note; this.accent = accent; setOpaque(false);
            getAccessibleContext().setAccessibleName(title);
        }
        void setValue(String value, String note) {
            this.value = value; this.note = note;
            getAccessibleContext().setAccessibleDescription(value + ", " + note);
            repaint();
        }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = quality(graphics);
            int w = getWidth(), h = getHeight();
            g.setPaint(new GradientPaint(0, 0, new Color(24, 39, 56), w, h, PANEL));
            g.fillRoundRect(0, 0, w - 1, h - 1, 18, 18);
            g.setColor(BORDER); g.drawRoundRect(0, 0, w - 1, h - 1, 18, 18);
            g.setColor(accent); g.fillRoundRect(19, 20, 4, 14, 3, 3);
            g.setColor(MUTED); g.setFont(new Font("Segoe UI", Font.BOLD, 10)); g.drawString(title, 31, 31);
            g.setColor(TEXT); g.setFont(new Font("Segoe UI", Font.PLAIN, 31)); g.drawString(value, 19, 72);
            g.setColor(MUTED); g.setFont(new Font("Segoe UI", Font.PLAIN, 11)); g.drawString(note, 20, 96);
            g.dispose();
        }
    }

    private static final class HistoryChart extends JPanel {
        private static final long serialVersionUID = 1L;
        private final Deque<Double> values = new ArrayDeque<>();
        HistoryChart() {
            setOpaque(false);
            getAccessibleContext().setAccessibleName("Host CPU history, up to 60 samples");
        }
        void push(double value) { values.addLast(value); while (values.size() > 60) values.removeFirst(); repaint(); }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = quality(graphics);
            int w = getWidth(), h = getHeight(), left = 45, right = w - 22, top = 77, bottom = h - 33;
            chartShell(g, w, h, "Host performance", "System CPU  /  one sample per second");
            g.setFont(new Font("Segoe UI", Font.PLAIN, 10));
            for (int i = 0; i <= 2; i++) {
                int y = top + (bottom - top) * i / 2;
                g.setColor(BORDER); g.drawLine(left, y, right, y);
                g.setColor(MUTED); g.drawString(Integer.toString(100 - i * 50), 17, y + 4);
            }
            Path2D line = new Path2D.Double();
            int index = 0;
            boolean segment = false;
            double lastX = left, lastY = bottom;
            for (double value : values) {
                double x = left + (right - left) * (60 - values.size() + index++) / 59.0;
                if (value < 0) { segment = false; continue; }
                double y = bottom - value * (bottom - top);
                if (!segment) line.moveTo(x, y); else line.lineTo(x, y);
                segment = true; lastX = x; lastY = y;
            }
            g.setColor(new Color(72, 217, 211, 30)); g.setStroke(new BasicStroke(8, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)); g.draw(line);
            g.setColor(CYAN); g.setStroke(new BasicStroke(2, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)); g.draw(line);
            if (segment) g.fill(new Ellipse2D.Double(lastX - 3, lastY - 3, 6, 6));
            if (values.isEmpty() || values.stream().allMatch(value -> value < 0)) {
                g.setColor(MUTED); g.drawString("Waiting for a CPU measurement", left + 12, top + 36);
            }
            g.setColor(MUTED); g.drawString("60 seconds ago", left, h - 13); g.drawString("Now", right - 22, h - 13);
            g.dispose();
        }
    }

    private static final class StateChart extends JPanel {
        private static final long serialVersionUID = 1L;
        private final QuantumTernaryBinaryCore core;
        StateChart(QuantumTernaryBinaryCore core) {
            this.core = core; setOpaque(false);
            getAccessibleContext().setAccessibleName("Normalized host signal distribution, derived from four host metrics");
        }
        @Override protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = quality(graphics);
            int w = getWidth(), h = getHeight(), left = 22, right = w - 22, top = 77, bottom = h - 33;
            chartShell(g, w, h, "Signal distribution", "64 channels derived from CPU, heap, thread and processor counts");
            double[] values = core.getProbabilities();
            double max = Arrays.stream(values).max().orElse(1);
            double step = (right - left) / (double) values.length;
            for (int i = 0; i < values.length; i++) {
                double bar = max == 0 ? 0 : values[i] / max * (bottom - top);
                g.setPaint(new GradientPaint(0, top, i % 4 == 0 ? CYAN : BLUE, 0, bottom, new Color(44, 74, 119)));
                g.fill(new RoundRectangle2D.Double(left + i * step, bottom - bar, Math.max(1, step - 3), bar, 3, 3));
            }
            g.setColor(MUTED); g.setFont(new Font("Segoe UI", Font.PLAIN, 10));
            g.drawString(String.format(Locale.ROOT, "Entropy %.3f bits", core.getEntropy()), left, h - 13);
            String peak = String.format(Locale.ROOT, "Peak %.2f%%  /  auto scale", max * 100);
            g.drawString(peak, right - g.getFontMetrics().stringWidth(peak), h - 13);
            g.dispose();
        }
    }

    private static final class DeviceTableModel extends AbstractTableModel {
        private static final long serialVersionUID = 1L;
        final String[] columns = {"DEVICE", "PLATFORM", "IP ADDRESS", "STATUS", "ENTROPY", "SALIENCE", "FRAMES"};
        List<RemoteDeviceNode> rows = new ArrayList<>();
        @Override public int getRowCount() { return rows.size(); }
        @Override public int getColumnCount() { return columns.length; }
        @Override public String getColumnName(int column) { return columns[column]; }
        @Override public Class<?> getColumnClass(int column) { return column == 4 || column == 5 ? Double.class : column == 6 ? Long.class : String.class; }
        @Override public Object getValueAt(int row, int column) {
            RemoteDeviceNode node = rows.get(row);
            switch (column) {
                case 0: return node.deviceId;
                case 1: return node.platformType;
                case 2: return node.ipAddress;
                case 3: return node.status(System.currentTimeMillis());
                case 4: return node.lastTelemetryTimestamp == 0 ? null : node.lastEntropy;
                case 5: return node.lastTelemetryTimestamp == 0 ? null : node.lastSalience;
                default: return node.messageCount;
            }
        }
    }
}

