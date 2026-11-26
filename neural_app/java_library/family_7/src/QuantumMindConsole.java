import neural.studio.*;
import javax.swing.*;
import javax.swing.border.*;
import javax.swing.event.*;
import javax.swing.table.*;
import javax.swing.plaf.basic.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.*;
import javax.imageio.ImageIO;

/** A local, read-only process monitor and interactive binary field. Java 17+. */
@SuppressWarnings("serial")
public final class QuantumMindConsole extends SectionFrame {
    static final Color BG = new Color(9, 14, 23), PANEL = new Color(16, 24, 37);
    static final Color LINE = new Color(35, 51, 70), TEXT = new Color(224, 237, 249);
    static final Color MUTED = new Color(133, 156, 181), CYAN = new Color(83, 218, 245);
    static final Color GREEN = new Color(100, 232, 181), PURPLE = new Color(172, 157, 255);
    static final Font BODY = new Font("Segoe UI", Font.PLAIN, 13);
    static final Font MONO = new Font("Consolas", Font.PLAIN, 12);
    final SimulationPanel field = new SimulationPanel();
    final MetricCard cpuCard = new MetricCard("SYSTEM CPU", CYAN);
    final MetricCard ramCard = new MetricCard("PHYSICAL MEMORY", GREEN);
    final MetricCard javaCard = new MetricCard("JAVA RUNTIMES", CYAN);
    final MetricCard pythonCard = new MetricCard("PYTHON RUNTIMES", PURPLE);
    final HistoryPanel history = new HistoryPanel();
    final ProcessModel processModel = new ProcessModel();
    final JTable processTable = new JTable(processModel);
    final TableRowSorter<ProcessModel> sorter = new TableRowSorter<>(processModel);
    final JComboBox<String> language = new JComboBox<>(new String[]{"All runtimes", "Java", "Python"});
    final JTextField search = new JTextField();
    final JTextField input = new JTextField();
    final JToggleButton zero = toggle("0"), one = toggle("1");
    final JButton align = button("ALIGN STATE", true), ground = button("GROUND FRICTION", false);
    final JButton flow = button("FREE FLOW", false), send = button("SEND TEXT", true);
    final JLabel live = label("CONNECTING  /  reading system telemetry", MUTED, 12);
    final JLabel status = label("Ready. Choose a bit, align the field, or send text.", MUTED, 12);
    final JLabel selection = label("Select a runtime to highlight it in the field.", MUTED, 12);
    final JLabel processCount = label("SCANNING", MUTED, 11);
    final JLabel fieldMode = label("FREE FLOW", CYAN, 11);
    final JTextArea journal = new JTextArea();
    final Telemetry telemetry = new Telemetry();
    final neural.studio.SharedTimer animation;
    final ScheduledExecutorService sampler = SharedScheduler.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "system-telemetry"); t.setDaemon(true); return t;
    });
    final AtomicBoolean closed = new AtomicBoolean();
    Set<String> priorProcesses = null;
    long selectedPid = -1;
    int alignBit = 1;
    final boolean collect;
    long lastAnimation = System.nanoTime();

    public QuantumMindConsole() { this(false); }

    QuantumMindConsole(boolean collect) {
        super("Quantum Mind Console | Live System Field");
        this.collect = collect;
        setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        setMinimumSize(new Dimension(1020, 720));
        Dimension screen = new Dimension(1440,900);
        setSize(Math.min(1540, screen.width - 60), Math.min(980, screen.height - 80));
        setLocationRelativeTo(null);
        JPanel root = panel(new BorderLayout(0, 18));
        root.setOpaque(true);
        root.setBackground(BG);
        root.setBorder(new EmptyBorder(22, 26, 18, 26));
        setContentPane(root);
        root.add(buildTop(), BorderLayout.NORTH);
        root.add(buildCenter(), BorderLayout.CENTER);
        root.add(buildControls(), BorderLayout.SOUTH);
        wireActions();
        animation = new neural.studio.SharedTimer(25, e -> {
            long now = System.nanoTime();
            double dt = Math.min(.06, (now - lastAnimation) / 1_000_000_000.0);
            lastAnimation = now;
            if (getState() != Frame.ICONIFIED) { field.advance(dt); field.repaint(); }
        });
        animation.start();
        addWindowListener(new WindowAdapter() { public void windowClosed(WindowEvent e) { shutdown(); } });
        if (collect) {
            telemetry.start();
            sampler.scheduleWithFixedDelay(() -> {
                try { Snapshot s = telemetry.sample(); SwingUtilities.invokeLater(() -> { if (!closed.get()) apply(s); }); }
                catch (Exception ex) { SwingUtilities.invokeLater(() -> live.setText("TELEMETRY RETRY  /  " + ex.getClass().getSimpleName())); }
            }, 0, 2, TimeUnit.SECONDS);
        }
        log("Console ready. Alignment and text control the local field.");
    }

    JPanel buildTop() {
        JPanel top = panel(new BorderLayout(0, 22));
        JPanel heading = panel(new BorderLayout());
        JPanel names = panel(new GridLayout(2, 1, 0, 3));
        names.add(label("QUANTUM MIND", TEXT, 27));
        names.add(label("SYSTEM CONSCIOUSNESS  /  LIVE RUNTIME TELEMETRY", MUTED, 10));
        heading.add(names, BorderLayout.WEST);
        JPanel tag = panel(new GridLayout(2, 1));
        JLabel version = label("STABLE CORE  /  2.0", GREEN, 12); version.setHorizontalAlignment(SwingConstants.RIGHT);
        live.setHorizontalAlignment(SwingConstants.RIGHT);
        tag.add(version); tag.add(live); heading.add(tag, BorderLayout.EAST);
        top.add(heading, BorderLayout.NORTH);
        JPanel metrics = panel(new GridLayout(1, 4, 14, 0));
        metrics.add(cpuCard); metrics.add(ramCard); metrics.add(javaCard); metrics.add(pythonCard);
        top.add(metrics, BorderLayout.CENTER);
        return top;
    }

    JSplitPane buildCenter() {
        JPanel visual = card(new BorderLayout(0, 0));
        JPanel caption = panel(new BorderLayout()); caption.setBorder(new EmptyBorder(14, 17, 12, 17));
        caption.add(label("BINARY FIELD", TEXT, 12), BorderLayout.WEST);
        caption.add(fieldMode, BorderLayout.EAST);
        visual.add(caption, BorderLayout.NORTH);
        visual.add(field, BorderLayout.CENTER);
        JPanel under = panel(new BorderLayout(15, 0)); under.setBorder(new EmptyBorder(9, 17, 13, 17));
        under.add(label("JAVA  /  cyan     PYTHON  /  violet", MUTED, 10), BorderLayout.WEST);
        under.add(label("Node motion responds to CPU activity", MUTED, 10), BorderLayout.EAST);
        visual.add(under, BorderLayout.SOUTH);
        ResponsiveSide side = new ResponsiveSide(history); side.setPreferredSize(new Dimension(425, 520));
        side.setMinimumSize(new Dimension(345, 220));
        JPanel processes = card(new BorderLayout(0, 9)); processes.setBorder(new CompoundBorder(new LineBorder(LINE), new EmptyBorder(14, 14, 12, 14)));
        JPanel controls = panel(new BorderLayout(0, 10));
        JPanel title = panel(new BorderLayout()); title.add(label("RUNNING PROCESSES", TEXT, 12), BorderLayout.WEST);
        title.add(processCount, BorderLayout.EAST); controls.add(title, BorderLayout.NORTH);
        JPanel filters = panel(new BorderLayout(8, 0)); styleInput(search); styleInput(language);
        search.setToolTipText("Filter by application, language or process ID");
        search.getAccessibleContext().setAccessibleName("Filter running processes");
        search.putClientProperty("JTextField.placeholderText", "Filter processes");
        JPanel searchGroup = panel(new BorderLayout(6, 0)); searchGroup.add(label("FIND", MUTED, 10), BorderLayout.WEST); searchGroup.add(search);
        filters.add(language, BorderLayout.WEST); filters.add(searchGroup, BorderLayout.CENTER); controls.add(filters);
        processes.add(controls, BorderLayout.NORTH);
        processTable.setRowSorter(sorter); processTable.setRowHeight(39);
        processTable.setBackground(PANEL); processTable.setForeground(TEXT); processTable.setFont(BODY);
        processTable.setSelectionBackground(new Color(30, 64, 81)); processTable.setSelectionForeground(TEXT);
        processTable.setShowGrid(false); processTable.setIntercellSpacing(new Dimension(0, 0));
        processTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        processTable.setFillsViewportHeight(true);
        processTable.getTableHeader().setBackground(PANEL); processTable.getTableHeader().setForeground(MUTED);
        processTable.getTableHeader().setFont(MONO); processTable.getTableHeader().setReorderingAllowed(false);
        int[] widths = {190, 55, 58, 72};
        for (int i = 0; i < widths.length; i++) processTable.getColumnModel().getColumn(i).setPreferredWidth(widths[i]);
        processTable.setDefaultRenderer(Object.class, new DefaultTableCellRenderer() {
            public Component getTableCellRendererComponent(JTable table, Object value, boolean sel, boolean focus, int row, int col) {
                super.getTableCellRendererComponent(table, value, sel, focus, row, col);
                setBorder(new EmptyBorder(0, 6, 0, 6));
                if (!sel) setForeground(col == 0 ? (processModel.rows.get(table.convertRowIndexToModel(row)).language.equals("Python") ? PURPLE : CYAN) : TEXT);
                setToolTipText(col == 0 ? processModel.rows.get(table.convertRowIndexToModel(row)).label : "CPU is a share of total system capacity; memory is resident RAM.");
                return this;
            }
        });
        processTable.setDefaultRenderer(Double.class, new DefaultTableCellRenderer() {
            public Component getTableCellRendererComponent(JTable table, Object value, boolean sel, boolean focus, int row, int col) {
                double number = (Double)value;
                super.getTableCellRendererComponent(table, number < 0 ? "\u2014" : col == 2 ? String.format(Locale.ROOT, "%.1f%%", number) : memory((long)number), sel, focus, row, col);
                setHorizontalAlignment(SwingConstants.RIGHT); setBorder(new EmptyBorder(0, 5, 0, 8)); return this;
            }
        });
        JScrollPane scroll = new JScrollPane(processTable); scroll.setBorder(BorderFactory.createEmptyBorder()); scroll.getViewport().setBackground(PANEL);
        processes.add(scroll, BorderLayout.CENTER);
        selection.setPreferredSize(new Dimension(1, 26)); processes.add(selection, BorderLayout.SOUTH);
        side.add(processes, BorderLayout.CENTER);
        JPanel lower = panel(new BorderLayout(0, 13));
        lower.add(history, BorderLayout.NORTH);
        JPanel events = card(new BorderLayout(0, 7)); events.setBorder(new CompoundBorder(new LineBorder(LINE), new EmptyBorder(12, 14, 10, 14)));
        events.add(label("ACTIVITY JOURNAL", MUTED, 10), BorderLayout.NORTH);
        journal.setEditable(false); journal.setBackground(PANEL); journal.setForeground(MUTED); journal.setFont(new Font("Consolas", Font.PLAIN, 11));
        journal.setLineWrap(true); journal.setWrapStyleWord(true);
        JScrollPane logs = new JScrollPane(journal); logs.setBorder(null); logs.setPreferredSize(new Dimension(1, 67));
        events.add(logs); lower.add(events, BorderLayout.CENTER); side.add(lower, BorderLayout.SOUTH);
        side.lower = lower; side.events = events;
        JSplitPane split = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, visual, side);
        split.setUI(new BasicSplitPaneUI() {
            public BasicSplitPaneDivider createDefaultDivider() {
                return new BasicSplitPaneDivider(this) {
                    public void paint(Graphics g) { g.setColor(BG); g.fillRect(0, 0, getWidth(), getHeight()); g.setColor(LINE); for (int y = -7; y <= 7; y += 7) g.fillOval(getWidth() / 2 - 1, getHeight() / 2 + y, 3, 3); }
                };
            }
        });
        split.setOpaque(false); split.setBorder(null); split.setDividerSize(15); split.setResizeWeight(.71);
        visual.setMinimumSize(new Dimension(450, 220)); return split;
    }

    JPanel buildControls() {
        JPanel bottom = panel(new BorderLayout(0, 11));
        JPanel controls = card(new BorderLayout(20, 0)); controls.setBorder(new CompoundBorder(new LineBorder(LINE), new EmptyBorder(14, 16, 14, 16)));
        JPanel alignment = panel(new BorderLayout(0, 8));
        alignment.add(label("ALIGNMENT TARGET", MUTED, 10), BorderLayout.NORTH);
        JPanel buttons = panel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        ButtonGroup bits = new ButtonGroup(); bits.add(zero); bits.add(one); one.setSelected(true);
        buttons.add(zero); buttons.add(one); buttons.add(align); buttons.add(ground); buttons.add(flow);
        alignment.add(buttons); controls.add(alignment, BorderLayout.WEST);
        JPanel text = panel(new BorderLayout(0, 8)); text.add(label("TEXT INPUT  /  UTF-8 BINARY SIGNAL", MUTED, 10), BorderLayout.NORTH);
        JPanel entry = panel(new BorderLayout(8, 0)); styleInput(input);
        input.setToolTipText("Type text and press Enter. Its UTF-8 bits seed the local binary field.");
        input.getAccessibleContext().setAccessibleName("Text input for binary field");
        entry.add(input, BorderLayout.CENTER); entry.add(send, BorderLayout.EAST); text.add(entry); controls.add(text);
        bottom.add(controls, BorderLayout.CENTER);
        JPanel foot = panel(new BorderLayout(10, 0)); foot.add(status, BorderLayout.CENTER);
        foot.add(label("LOCAL FIELD CONTROLS  /  READ-ONLY MONITOR", MUTED, 10), BorderLayout.EAST);
        bottom.add(foot, BorderLayout.SOUTH); return bottom;
    }

    void wireActions() {
        zero.addActionListener(e -> selectBit(0)); one.addActionListener(e -> selectBit(1));
        align.addActionListener(e -> { field.mode = Mode.ALIGNED; fieldMode.setText("ALIGNED  /  " + alignBit); status.setText("Field aligned to " + alignBit + ". Live telemetry continues."); log("Aligned the field to binary " + alignBit + "."); });
        ground.addActionListener(e -> { field.mode = Mode.GROUNDED; fieldMode.setText("GROUNDED"); status.setText("Field motion held. Telemetry and runtime detection stay live."); log("Ground friction applied. Field motion held."); });
        flow.addActionListener(e -> { field.mode = Mode.FLOW; fieldMode.setText("FREE FLOW"); status.setText("Free flow restored. Motion follows system and runtime CPU activity."); log("Free flow restored."); });
        send.addActionListener(e -> sendText()); input.addActionListener(e -> sendText());
        language.addActionListener(e -> filter());
        search.getDocument().addDocumentListener(new DocumentListener() {
            public void insertUpdate(DocumentEvent e) { filter(); } public void removeUpdate(DocumentEvent e) { filter(); } public void changedUpdate(DocumentEvent e) { filter(); }
        });
        processTable.getSelectionModel().addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                int row = processTable.getSelectedRow();
                if (row >= 0) { RuntimeProcess p = processModel.rows.get(processTable.convertRowIndexToModel(row)); selectedPid = p.pid; field.selectedPid = p.pid; selection.setText(p.language + "  /  PID " + p.pid + "  /  " + p.label); selection.setToolTipText(selection.getText()); }
                else { selectedPid = -1; field.selectedPid = -1; selection.setText("Select a runtime to highlight it in the field."); }
            }
        });
    }

    void selectBit(int bit) {
        alignBit = bit; field.alignBit = bit;
        if (field.mode == Mode.ALIGNED) fieldMode.setText("ALIGNED  /  " + bit);
        status.setText("Alignment target set to " + bit + ".");
    }

    void sendText() {
        String text = input.getText();
        if (text.isBlank()) { status.setText("Enter some text to send a binary signal."); return; }
        if (text.length() > 4096) { status.setText("Please keep the input to 4,096 characters or fewer."); return; }
        field.signal = bits(text); field.signalLabel = text;
        field.pulse = 1; field.distributeSignal();
        status.setText("Text received: " + field.signal.length() + " UTF-8 bits. Signal loaded into the field.");
        log("Text signal received / " + field.signal.length() + " bits.");
    }

    void filter() {
        String term = search.getText().trim().toLowerCase(Locale.ROOT);
        String lang = (String)language.getSelectedItem();
        sorter.setRowFilter(new RowFilter<ProcessModel, Integer>() {
            public boolean include(Entry<? extends ProcessModel, ? extends Integer> e) {
                RuntimeProcess p = processModel.rows.get(e.getIdentifier());
                return (lang.equals("All runtimes") || lang.equals(p.language)) && (p.label + " " + p.pid + " " + p.language).toLowerCase(Locale.ROOT).contains(term);
            }
        });
        updateCount();
    }

    void updateCount() { processCount.setText(processTable.getRowCount() + " / " + processModel.rows.size() + " LIVE"); }

    void apply(Snapshot s) {
        cpuCard.update(s.cpu < 0 ? "\u2014" : String.format(Locale.ROOT, "%.1f%%", s.cpu), s.cpu < 0 ? "Waiting for CPU sample" : s.cores + " logical processors", s.cpu / 100);
        double ramRatio = s.totalMemory <= 0 ? -1 : (double)s.usedMemory / s.totalMemory;
        ramCard.update(s.usedMemory < 0 ? "\u2014" : memory(s.usedMemory), s.totalMemory <= 0 ? "Memory unavailable" : "of " + memory(s.totalMemory) + "  /  " + Math.round(ramRatio * 100) + "% used", ramRatio);
        long javaCount = s.processes.stream().filter(p -> p.language.equals("Java")).count();
        long pyCount = s.processes.size() - javaCount;
        javaCard.update(String.valueOf(javaCount), runtimeSummary(s.processes, "Java"), Math.min(1, javaCount / 20.0));
        pythonCard.update(String.valueOf(pyCount), runtimeSummary(s.processes, "Python"), Math.min(1, pyCount / 20.0));
        String when = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
        live.setText("LIVE  /  " + when + "  /  " + s.source); live.setForeground(s.degraded ? MUTED : GREEN);
        Set<String> current = new HashSet<>(); for (RuntimeProcess p : s.processes) current.add(p.identity());
        if (priorProcesses != null && !s.degraded) {
            long added = current.stream().filter(k -> !priorProcesses.contains(k)).count();
            long removed = priorProcesses.stream().filter(k -> !current.contains(k)).count();
            if (added > 0) log(added + " runtime" + (added == 1 ? " started." : "s started."));
            if (removed > 0) log(removed + " runtime" + (removed == 1 ? " exited." : "s exited."));
        }
        if (!s.degraded) priorProcesses = current;
        long restore = selectedPid;
        processModel.rows = s.processes; processModel.fireTableDataChanged();
        for (int i = 0; i < processModel.rows.size(); i++) if (processModel.rows.get(i).pid == restore) {
            int view = processTable.convertRowIndexToView(i); if (view >= 0) processTable.setRowSelectionInterval(view, view); break;
        }
        updateCount(); field.processes = s.processes; field.systemCpu = s.cpu; field.memoryRatio = ramRatio; history.add(s.cpu, ramRatio * 100);
        field.repaint();
    }

    static String runtimeSummary(List<RuntimeProcess> ps, String language) {
        long total = 0; int known = 0, count = 0;
        for (RuntimeProcess p : ps) if (p.language.equals(language)) { count++; if (p.rss >= 0) { total += p.rss; known++; } }
        return count == 0 ? "No active runtimes" : known == 0 ? "Resident memory unavailable" : memory(total) + " resident" + (known < count ? " / partial" : "");
    }

    void log(String message) {
        journal.append(LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")) + "  " + message + "\n");
        if (journal.getLineCount() > 150) try { journal.replaceRange("", 0, journal.getLineEndOffset(0)); } catch (Exception ignored) { }
        journal.setCaretPosition(journal.getDocument().getLength());
    }

    void shutdown() { if (closed.compareAndSet(false, true)) { animation.stop(); sampler.shutdownNow(); telemetry.close(); } }

    static JPanel panel(LayoutManager layout) { JPanel p = new JPanel(layout); p.setOpaque(false); return p; }
    static JPanel card(LayoutManager layout) { JPanel p = new JPanel(layout); p.setBackground(PANEL); p.setBorder(new LineBorder(LINE)); return p; }
    static JLabel label(String text, Color color, int size) { JLabel l = new JLabel(text); l.setForeground(color); l.setFont(new Font("Segoe UI", size > 20 ? Font.BOLD : Font.PLAIN, size)); return l; }
    static JButton button(String text, boolean primary) { JButton b = new JButton(text); styleButton(b, primary); return b; }
    static JToggleButton toggle(String text) { JToggleButton b = new JToggleButton(text); styleButton(b, false); b.setPreferredSize(new Dimension(39, 37)); b.setFont(new Font("Consolas", Font.BOLD, 17)); b.getAccessibleContext().setAccessibleName("Align state " + text); return b; }
    static void styleButton(AbstractButton b, boolean primary) { b.setBackground(primary ? new Color(30, 95, 114) : new Color(29, 41, 58)); b.setForeground(TEXT); b.setFocusPainted(true); b.setFont(new Font("Segoe UI", Font.BOLD, 10)); b.setBorder(new CompoundBorder(new LineBorder(primary ? new Color(58, 140, 158) : LINE), new EmptyBorder(10, 11, 10, 11))); b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)); }
    static void styleInput(JComponent c) { c.setFont(BODY); c.setBackground(new Color(10, 17, 28)); c.setForeground(TEXT); c.setBorder(new CompoundBorder(new LineBorder(LINE), new EmptyBorder(6, 7, 6, 7))); if (c instanceof JTextField t) t.setCaretColor(CYAN); }
    static String memory(long bytes) { if (bytes < 0) return "\u2014"; if (bytes >= 1024L * 1024 * 1024) return String.format(Locale.ROOT, "%.1f GB", bytes / (1024.0 * 1024 * 1024)); return String.format(Locale.ROOT, "%.0f MB", bytes / (1024.0 * 1024)); }
    static String bits(String text) { StringBuilder b = new StringBuilder(); for (byte item : text.getBytes(StandardCharsets.UTF_8)) for (int i = 7; i >= 0; i--) b.append((item >> i) & 1); return b.toString(); }
    static void quality(Graphics2D g) { g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON); g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON); }

    static class ResponsiveSide extends JPanel {
        final HistoryPanel history; JPanel lower, events;
        ResponsiveSide(HistoryPanel history) { super(new BorderLayout(0, 14)); this.history = history; setOpaque(false); }
        public void doLayout() {
            if (lower != null) {
                boolean compact = getHeight() < 430;
                lower.setVisible(getHeight() >= 360);
                events.setVisible(!compact);
                history.setPreferredSize(new Dimension(1, compact ? 95 : 100));
                lower.setPreferredSize(new Dimension(1, compact ? 95 : 210));
            }
            super.doLayout();
        }
    }

    static class MetricCard extends JPanel {
        final JLabel value = label("\u2014", TEXT, 30), detail = label("Waiting for telemetry", MUTED, 11);
        final Color accent; double ratio;
        MetricCard(String title, Color accent) {
            super(new BorderLayout(0, 5)); this.accent = accent; setBackground(PANEL);
            setBorder(new CompoundBorder(new LineBorder(LINE), new EmptyBorder(13, 17, 17, 17)));
            add(label(title, MUTED, 10), BorderLayout.NORTH); add(value); add(detail, BorderLayout.SOUTH);
        }
        void update(String text, String sub, double ratio) { value.setText(text); detail.setText(sub); this.ratio = ratio; repaint(); }
        protected void paintComponent(Graphics graphics) { super.paintComponent(graphics); Graphics2D g = (Graphics2D)graphics.create(); quality(g); g.setColor(LINE); g.fillRoundRect(17, getHeight() - 9, getWidth() - 34, 3, 3, 3); g.setColor(accent); g.fillRoundRect(17, getHeight() - 9, (int)((getWidth() - 34) * Math.max(0, Math.min(1, ratio))), 3, 3, 3); g.dispose(); }
    }

    static class HistoryPanel extends JPanel {
        final Deque<double[]> values = new ArrayDeque<>();
        HistoryPanel() { setBackground(PANEL); setPreferredSize(new Dimension(1, 125)); setBorder(new LineBorder(LINE)); }
        void add(double cpu, double ram) { values.add(new double[]{cpu, ram}); while (values.size() > 60) values.removeFirst(); repaint(); }
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); Graphics2D g = (Graphics2D)graphics.create(); quality(g);
            g.setFont(new Font("Segoe UI", Font.PLAIN, 10)); g.setColor(MUTED); g.drawString("SYSTEM HISTORY  /  LAST 2 MIN", 14, 21);
            g.setColor(CYAN); g.drawString("CPU", getWidth() - 91, 21); g.setColor(GREEN); g.drawString("RAM", getWidth() - 49, 21);
            int left = 14, top = 37, w = getWidth() - 28, h = getHeight() - 51;
            g.setColor(LINE); for (int i = 0; i <= 2; i++) g.drawLine(left, top + i * h / 2, left + w, top + i * h / 2);
            for (int series = 0; series < 2; series++) { Path2D path = new Path2D.Double(); boolean connected = false; int i = 60 - values.size(); double lastX = -1, lastY = -1;
                for (double[] v : values) { double x = left + i++ * w / 59.0, y = top + h * (1 - Math.max(0, Math.min(100, v[series])) / 100.0); if (v[series] < 0) { connected = false; continue; } if (!connected) path.moveTo(x, y); else path.lineTo(x, y); connected = true; lastX = x; lastY = y; }
                g.setColor(series == 0 ? CYAN : GREEN); g.setStroke(new BasicStroke(1.8f)); g.draw(path);
                if (lastX >= 0) g.fill(new Ellipse2D.Double(lastX - 2, lastY - 2, 4, 4));
            } g.dispose();
        }
    }

    enum Mode { FLOW, ALIGNED, GROUNDED }
    static class Node {
        double x, y, vx, vy; char bit;
        Node(Random r) { x = .05 + r.nextDouble() * .9; y = .05 + r.nextDouble() * .9; vx = (r.nextDouble() - .5) * .024; vy = (r.nextDouble() - .5) * .024; bit = r.nextBoolean() ? '1' : '0'; }
    }
    static class SimulationPanel extends JPanel {
        final List<Node> nodes = new ArrayList<>();
        List<RuntimeProcess> processes = List.of();
        Mode mode = Mode.FLOW; int alignBit = 1; long selectedPid = -1;
        double systemCpu = -1, memoryRatio = -1, phase = 0, pulse = 0;
        String signal = "", signalLabel = "";
        SimulationPanel() { setBackground(new Color(8, 15, 25)); Random r = new Random(410); for (int i = 0; i < 90; i++) nodes.add(new Node(r)); }
        void distributeSignal() { if (!signal.isEmpty()) for (int i = 0; i < nodes.size(); i++) nodes.get(i).bit = signal.charAt(i % signal.length()); }
        void advance(double dt) {
            if (mode == Mode.GROUNDED) return;
            double activity = 1 + Math.max(0, systemCpu) / 40;
            phase += dt * .11; pulse = Math.max(0, pulse - dt * .35);
            for (int i = 0; i < nodes.size(); i++) {
                Node n = nodes.get(i);
                if (mode == Mode.ALIGNED) {
                    double theta = i * Math.PI * 2 / nodes.size(); double radius = .16 + (i % 3) * .055;
                    n.x += (.5 + Math.cos(theta) * radius - n.x) * Math.min(1, dt * 3);
                    n.y += (.5 + Math.sin(theta) * radius - n.y) * Math.min(1, dt * 3);
                } else {
                    n.x += n.vx * dt * activity; n.y += n.vy * dt * activity;
                    if (n.x < .02) { n.x = .02; n.vx = Math.abs(n.vx); } if (n.x > .98) { n.x = .98; n.vx = -Math.abs(n.vx); }
                    if (n.y < .03) { n.y = .03; n.vy = Math.abs(n.vy); } if (n.y > .97) { n.y = .97; n.vy = -Math.abs(n.vy); }
                }
            }
        }
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics); Graphics2D g = (Graphics2D)graphics.create(); quality(g);
            int w = getWidth(), h = getHeight(); if (w <= 0 || h <= 0) { g.dispose(); return; }
            int cx = w / 2, cy = h / 2; double size = Math.min(w, h);
            g.setPaint(new RadialGradientPaint(new Point2D.Double(cx, cy), (float)Math.max(1, size * .7), new float[]{0, 1}, new Color[]{new Color(17, 40, 54), getBackground()})); g.fillRect(0, 0, w, h);
            g.setColor(new Color(36, 65, 85, 58)); for (int x = 20; x < w; x += 30) for (int y = 20; y < h; y += 30) g.fillRect(x, y, 1, 1);
            g.setStroke(new BasicStroke(1));
            for (int ring = 1; ring <= 3; ring++) { double r = size * (.14 + ring * .11); g.setColor(new Color(63, 108, 135, 30 + ring * 6)); g.draw(new Ellipse2D.Double(cx - r, cy - r, r * 2, r * 2)); }
            g.setColor(new Color(54, 97, 123, 55)); g.drawLine(cx, 25, cx, h - 25); g.drawLine(25, cy, w - 25, cy);
            double linkage = Math.min(130, Math.max(65, size * .22));
            for (int i = 0; i < nodes.size(); i++) for (int j = i + 1; j < nodes.size(); j++) {
                Node a = nodes.get(i), b = nodes.get(j); double d = Math.hypot((a.x - b.x) * w, (a.y - b.y) * h);
                if (d < linkage) { int alpha = (int)((1 - d / linkage) * 70); g.setColor(new Color(57, 156, 190, alpha)); g.draw(new Line2D.Double(a.x * w, a.y * h, b.x * w, b.y * h)); }
            }
            g.setFont(new Font("Consolas", Font.BOLD, 13));
            for (Node n : nodes) { int x = (int)(n.x * w), y = (int)(n.y * h); g.setColor(new Color(65, 210, 223, 16)); g.fillOval(x - 8, y - 15, 22, 22); g.setColor(mode == Mode.ALIGNED ? GREEN : new Color(94, 154, 190, 165)); g.drawString(mode == Mode.ALIGNED ? Integer.toString(alignBit) : Character.toString(n.bit), x, y); }
            // Every runtime contributes to telemetry. Up to 24 hubs keep the field legible.
            List<RuntimeProcess> visible = new ArrayList<>(processes);
            visible.sort(Comparator.<RuntimeProcess>comparingInt(p -> p.pid == selectedPid ? 0 : 1).thenComparing(Comparator.comparingDouble((RuntimeProcess p) -> p.cpu).reversed()).thenComparingLong(p -> p.pid));
            int count = Math.min(24, visible.size());
            for (int i = 0; i < count; i++) {
                RuntimeProcess p = visible.get(i); double angle = i * Math.PI * 2 / Math.max(1, count) + phase;
                double radius = size * (i % 2 == 0 ? .34 : .43); int x = cx + (int)(Math.cos(angle) * radius), y = cy + (int)(Math.sin(angle) * radius);
                Color c = p.language.equals("Python") ? PURPLE : CYAN;
                g.setColor(new Color(c.getRed(), c.getGreen(), c.getBlue(), p.pid == selectedPid ? 140 : 40)); g.drawLine(cx, cy, x, y);
                int r = 6 + (int)Math.min(11, Math.max(0, p.cpu) * .45);
                g.setColor(new Color(c.getRed(), c.getGreen(), c.getBlue(), 20)); g.fillOval(x - r * 3, y - r * 3, r * 6, r * 6);
                g.setColor(c); g.fillOval(x - r / 2, y - r / 2, r, r); g.drawOval(x - r - 3, y - r - 3, r * 2 + 6, r * 2 + 6);
                if (p.pid == selectedPid) { g.setColor(TEXT); g.drawOval(x - r - 7, y - r - 7, r * 2 + 14, r * 2 + 14); }
                String name = elide(g, p.label, 115); int labelX = Math.max(8, Math.min(w - g.getFontMetrics().stringWidth(name) - 8, x + 15)); int labelY = Math.max(18, Math.min(h - 25, y - 3));
                g.setFont(new Font("Segoe UI", Font.PLAIN, 10)); g.setColor(TEXT); g.drawString(name, labelX, labelY); g.setColor(MUTED); g.drawString("PID " + p.pid, labelX, labelY + 14);
            }
            int r = (int)(size * .12); Color core = mode == Mode.ALIGNED ? GREEN : CYAN;
            g.setColor(new Color(7, 19, 30, 235)); g.fillOval(cx - r, cy - r, r * 2, r * 2);
            g.setColor(new Color(core.getRed(), core.getGreen(), core.getBlue(), 75)); g.setStroke(new BasicStroke(1.5f)); g.drawOval(cx - r, cy - r, r * 2, r * 2);
            g.setColor(core); g.drawArc(cx - r - 7, cy - r - 7, r * 2 + 14, r * 2 + 14, (int)(phase * 100), mode == Mode.ALIGNED ? 360 : 90 + (int)Math.max(0, systemCpu));
            g.setFont(new Font("Consolas", Font.BOLD, Math.max(24, r / 2))); center(g, mode == Mode.ALIGNED ? Integer.toString(alignBit) : mode == Mode.GROUNDED ? "HOLD" : "01", cx, cy + 5);
            g.setFont(new Font("Segoe UI", Font.PLAIN, 9)); g.setColor(MUTED); center(g, mode == Mode.ALIGNED ? "ALIGNED STATE" : mode == Mode.GROUNDED ? "GROUND FRICTION" : "LIVE FIELD", cx, cy + 25);
            if (pulse > 0) { double pr = size * (.15 + (1 - pulse) * .65); g.setColor(new Color(100, 232, 181, (int)(pulse * 130))); g.draw(new Ellipse2D.Double(cx - pr, cy - pr, pr * 2, pr * 2)); }
            g.setColor(new Color(8, 15, 25, 225)); g.fillRoundRect(10, 7, Math.min(w - 20, signalLabel.isEmpty() ? 280 : 430), signalLabel.isEmpty() ? 26 : 48, 8, 8);
            g.setFont(MONO); g.setColor(MUTED); g.drawString(String.format(Locale.ROOT, "%03d NODES   /   %d RUNTIMES", nodes.size(), processes.size()), 18, 24);
            g.setFont(new Font("Segoe UI", Font.PLAIN, 10));
            String hint = processes.isEmpty() ? "Waiting for visible Java or Python runtimes" : processes.size() > 24 ? "Showing 24 active hubs / all " + processes.size() + " runtimes in the monitor" : "Live runtime hubs / select a process to focus";
            g.drawString(hint, 18, h - 19);
            if (!signalLabel.isEmpty()) { g.setColor(GREEN); g.drawString("SIGNAL  /  " + elide(g, signalLabel.replaceAll("\\s+", " "), w - 150), 18, 45); }
            g.dispose();
        }
        static void center(Graphics2D g, String s, int x, int y) { g.drawString(s, x - g.getFontMetrics().stringWidth(s) / 2, y); }
        static String elide(Graphics2D g, String s, int width) { if (g.getFontMetrics().stringWidth(s) <= width) return s; int n = s.length(); while (n > 0 && g.getFontMetrics().stringWidth(s.substring(0, n) + "\u2026") > width) n--; return s.substring(0, n) + "\u2026"; }
    }

    record RuntimeProcess(long pid, String started, String language, String label, double cpu, long rss, long cpuNanos) { String identity() { return pid + ":" + started; } }
    record Snapshot(double cpu, long usedMemory, long totalMemory, int cores, List<RuntimeProcess> processes, String source, boolean degraded) { }
    static class ProcessModel extends AbstractTableModel {
        List<RuntimeProcess> rows = List.of();
        public int getRowCount() { return rows.size(); } public int getColumnCount() { return 4; }
        public String getColumnName(int c) { return new String[]{"APPLICATION", "PID", "CPU", "RAM"}[c]; }
        public Class<?> getColumnClass(int c) { return c == 1 ? Long.class : c >= 2 ? Double.class : String.class; }
        public Object getValueAt(int r, int c) { RuntimeProcess p = rows.get(r); return switch (c) { case 0 -> p.label; case 1 -> p.pid; case 2 -> p.cpu; default -> (double)p.rss; }; }
    }

    static class Telemetry implements AutoCloseable {
        final com.sun.management.OperatingSystemMXBean os = ManagementFactory.getPlatformMXBean(com.sun.management.OperatingSystemMXBean.class);
        final int cores = Runtime.getRuntime().availableProcessors();
        final Map<String, long[]> previous = new HashMap<>();
        record NativeFrame(List<RuntimeProcess> rows, long at, double systemCpu) { }
        volatile NativeFrame windowsFrame;
        volatile Process helper;
        volatile boolean stopped;
        // All commands below are fixed. User input is never passed to a shell or runtime.
        static final String WINDOWS_SCRIPT = """
            $ErrorActionPreference = 'Stop'
            [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
            function B64([string]$value) { [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($value)) }
            $nativeCpu = $false
            try {
              Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class QMCSystemTimes { [DllImport("kernel32.dll")] public static extern bool GetSystemTimes(out long idle, out long kernel, out long user); }'
              $nativeCpu = $true
            } catch {}
            $lastTotal = 0L; $lastIdle = 0L
            $canCim = $true
            while ($true) {
              $rows = @()
              if ($canCim) {
                try {
                  $rows = @(Get-CimInstance Win32_Process -Filter "Name LIKE 'java%' OR Name LIKE 'python%' OR Name LIKE 'pypy%' OR Name = 'py.exe' OR Name = 'jython.exe'" | ForEach-Object {
                    $stamp = ''; if ($_.CreationDate) { $stamp = $_.CreationDate.ToUniversalTime().ToString('o') }
                    $cpu = -1; if ($null -ne $_.KernelModeTime -and $null -ne $_.UserModeTime) { $cpu = [long]$_.KernelModeTime + [long]$_.UserModeTime }
                    $mem = -1; if ($null -ne $_.WorkingSetSize) { $mem = [long]$_.WorkingSetSize }
                    "P`t$($_.ProcessId)`t$stamp`t$cpu`t$mem`t$(B64 $_.Name)`t$(B64 $_.CommandLine)"
                  })
                } catch { $canCim = $false }
              }
              if (-not $canCim) {
                $rows = @(Get-Process | Where-Object { $_.ProcessName -match '^(java|javaw|python[0-9.]*w?|pythonw[0-9.]*|pypy[0-9.]*|pypyw[0-9.]*|py|jython)$' } | ForEach-Object {
                  $stamp = ''; $cpu = -1; $mem = -1
                  try { $stamp = $_.StartTime.ToUniversalTime().ToString('o') } catch {}
                  try { $cpu = $_.TotalProcessorTime.Ticks } catch {}
                  try { $mem = $_.WorkingSet64 } catch {}
                  "P`t$($_.Id)`t$stamp`t$cpu`t$mem`t$(B64 $_.ProcessName)`t"
                })
              }
              [Console]::WriteLine('BEGIN')
              if ($nativeCpu) {
                $idle = 0L; $kernel = 0L; $user = 0L
                if ([QMCSystemTimes]::GetSystemTimes([ref]$idle, [ref]$kernel, [ref]$user)) {
                  $total = $kernel + $user
                  if ($lastTotal -gt 0 -and $total -gt $lastTotal) {
                    $load = 100.0 * (1.0 - ($idle - $lastIdle) / [double]($total - $lastTotal))
                    [Console]::WriteLine('S' + "`t" + $load.ToString([Globalization.CultureInfo]::InvariantCulture))
                  }
                  $lastTotal = $total; $lastIdle = $idle
                }
              }
              foreach ($row in $rows) { [Console]::WriteLine($row) }
              [Console]::WriteLine('END')
              [Console]::Out.Flush()
              Start-Sleep -Seconds 2
            }
            """;

        void start() {
            if (!System.getProperty("os.name", "").toLowerCase(Locale.ROOT).contains("windows")) return;
            Thread reader = new Thread(() -> {
                while (!stopped) {
                    try {
                        String systemRoot = System.getenv().getOrDefault("SystemRoot", "C:\\Windows");
                        String powershell = Path.of(systemRoot, "System32", "WindowsPowerShell", "v1.0", "powershell.exe").toString();
                        String encoded = Base64.getEncoder().encodeToString(WINDOWS_SCRIPT.getBytes(StandardCharsets.UTF_16LE));
                        Process launched = new ProcessBuilder(powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded).redirectError(ProcessBuilder.Redirect.DISCARD).start();
                        synchronized (this) { if (stopped) { launched.destroyForcibly(); return; } helper = launched; }
                        try (BufferedReader br = new BufferedReader(new InputStreamReader(launched.getInputStream(), StandardCharsets.UTF_8))) {
                            List<RuntimeProcess> frame = null; String line; double systemCpu = -1;
                            while (!stopped && (line = br.readLine()) != null) {
                                line = line.replace("\uFEFF", "");
                                if (line.equals("BEGIN")) { frame = new ArrayList<>(); systemCpu = -1; }
                                else if (line.equals("END") && frame != null) { windowsFrame = new NativeFrame(List.copyOf(frame), System.nanoTime(), systemCpu); frame = null; }
                                else if (line.startsWith("S\t")) { try { systemCpu = Math.max(0, Math.min(100, Double.parseDouble(line.substring(2)))); } catch (NumberFormatException ignored) { } }
                                else if (line.startsWith("P\t") && frame != null) { RuntimeProcess p = parseWindowsRow(line); if (p != null) frame.add(p); }
                            }
                        } finally { launched.destroy(); if (launched.isAlive()) launched.destroyForcibly(); }
                    } catch (Exception ignored) { /* ProcessHandle collection continues independently. */ }
                    if (!stopped) try { Thread.sleep(5000); } catch (InterruptedException ignored) { return; }
                }
            }, "windows-runtime-collector"); reader.setDaemon(true); reader.start();
        }

        static RuntimeProcess parseWindowsRow(String row) {
            try {
                String[] p = row.split("\t", -1); if (p.length != 7) return null;
                String name = new String(Base64.getDecoder().decode(p[5]), StandardCharsets.UTF_8);
                String lang = runtimeLanguage(name); if (lang == null) return null;
                String command = new String(Base64.getDecoder().decode(p[6]), StandardCharsets.UTF_8);
                long ticks = Long.parseLong(p[3]);
                return new RuntimeProcess(Long.parseLong(p[1]), p[2], lang, applicationLabel(name, tokenize(command)), -1, Long.parseLong(p[4]), ticks < 0 ? -1 : ticks * 100);
            } catch (RuntimeException ex) { return null; }
        }

        Snapshot sample() {
            long now = System.nanoTime();
            NativeFrame nativeFrame = windowsFrame;
            boolean windowsFresh = nativeFrame != null && now - nativeFrame.at < TimeUnit.SECONDS.toNanos(8);
            Set<Long> nativePids = new HashSet<>();
            Map<Long, RuntimeProcess> all = new TreeMap<>();
            boolean handleFailure = false;
            try (var handles = ProcessHandle.allProcesses()) {
                handles.forEach(h -> { try {
                    ProcessHandle.Info info = h.info(); String command = info.command().orElse(""); String lang = runtimeLanguage(command);
                    if (lang == null) return;
                    List<String> args = new ArrayList<>(); args.add(command); args.addAll(Arrays.asList(info.arguments().orElse(new String[0])));
                    all.put(h.pid(), new RuntimeProcess(h.pid(), info.startInstant().map(Instant::toString).orElse(""), lang, applicationLabel(command, args), -1, -1, info.totalCpuDuration().map(Duration::toNanos).orElse(-1L)));
                } catch (RuntimeException ignored) { } });
            } catch (RuntimeException ex) { handleFailure = true; }
            if (windowsFresh) for (RuntimeProcess p : nativeFrame.rows) {
                nativePids.add(p.pid);
                RuntimeProcess fromHandle = all.get(p.pid());
                String label = p.label;
                if (fromHandle != null && label.equals(p.language + " runtime")) label = fromHandle.label;
                all.put(p.pid, new RuntimeProcess(p.pid, p.started, p.language, label, -1, p.rss, p.cpuNanos));
            }
            List<RuntimeProcess> result = new ArrayList<>(); Set<String> seen = new HashSet<>();
            for (RuntimeProcess p : all.values()) {
                // Use the collection timestamp, not the UI refresh timestamp, for CPU deltas.
                long stamp = nativePids.contains(p.pid) ? nativeFrame.at : now;
                String key = p.identity(); seen.add(key); long[] before = previous.get(key);
                double cpu = cpuPercent(before, p.cpuNanos, stamp, cores);
                if (p.cpuNanos >= 0 && (before == null || stamp > before[1])) previous.put(key, new long[]{p.cpuNanos, stamp, Double.doubleToLongBits(cpu)});
                result.add(new RuntimeProcess(p.pid, p.started, p.language, p.label, cpu, p.rss, p.cpuNanos));
            }
            previous.keySet().retainAll(seen);
            result.sort(Comparator.comparing((RuntimeProcess p) -> p.language).thenComparing(p -> p.label, String.CASE_INSENSITIVE_ORDER).thenComparingLong(p -> p.pid));
            double cpu = os == null ? -1 : os.getCpuLoad();
            // GetSystemTimes includes idle in kernel time; the helper subtracts it.
            // Microsoft: https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes
            if (cpu < 0 && windowsFresh && cores <= 64 && nativeFrame.systemCpu >= 0) cpu = nativeFrame.systemCpu / 100;
            long total = os == null ? -1 : os.getTotalMemorySize(), free = os == null ? -1 : os.getFreeMemorySize();
            String source = windowsFresh ? "2s updates" : handleFailure ? "process access limited" : "basic process data";
            return new Snapshot(cpu < 0 ? -1 : cpu * 100, total > 0 && free >= 0 ? total - free : -1, total, cores, List.copyOf(result), source, handleFailure);
        }

        static double cpuPercent(long[] before, long cpu, long at, int cores) {
            if (cpu < 0 || before == null || before[0] < 0) return -1;
            if (at <= before[1]) return before.length > 2 ? Double.longBitsToDouble(before[2]) : -1;
            if (cpu < before[0]) return -1;
            return Math.max(0, Math.min(100, (cpu - before[0]) * 100.0 / (at - before[1]) / Math.max(1, cores)));
        }
        public synchronized void close() { stopped = true; if (helper != null) { helper.destroy(); if (helper.isAlive()) helper.destroyForcibly(); } }
    }

    static String runtimeLanguage(String command) {
        String name = baseName(command).toLowerCase(Locale.ROOT).replaceFirst("\\.exe$", "");
        if (name.matches("javaw?")) return "Java";
        if (name.matches("python(?:[0-9.]*w?|w[0-9.]*)|pypy(?:[0-9.]*w?|w[0-9.]*)|py|jython")) return "Python";
        return null;
    }
    static String baseName(String path) { return path.replace('\\', '/').substring(path.replace('\\', '/').lastIndexOf('/') + 1); }
    static List<String> tokenize(String line) {
        List<String> result = new ArrayList<>(); Matcher m = Pattern.compile("\"([^\"]*)\"|'([^']*)'|(\\S+)").matcher(line);
        while (m.find()) result.add(m.group(1) != null ? m.group(1) : m.group(2) != null ? m.group(2) : m.group(3)); return result;
    }
    static String applicationLabel(String executable, List<String> args) {
        String lang = runtimeLanguage(executable); if (lang == null) return baseName(executable);
        for (int i = 1; i < args.size(); i++) {
            String a = args.get(i);
            if (a.equals("-jar") || a.equals("-m") || a.equals("--module")) return i + 1 < args.size() ? baseName(args.get(i + 1)) : lang + " runtime";
            if (a.startsWith("--module=")) return a.substring(9);
            if (a.equals("-c") && lang.equals("Python")) return "Python inline script";
            if (Set.of("-cp", "-classpath", "--class-path", "-p", "--module-path", "--upgrade-module-path", "--add-modules", "--limit-modules", "--add-exports", "--add-opens", "--add-reads", "--patch-module", "--source", "--enable-native-access", "-W", "-X").contains(a)) { i++; continue; }
            if (a.startsWith("-")) continue;
            return baseName(a);
        }
        return lang + " runtime";
    }

    static void configureTheme() {
        UIManager.put("Panel.background", BG); UIManager.put("Label.foreground", TEXT);
        UIManager.put("ToggleButton.select", new Color(33, 130, 144)); UIManager.put("ToggleButton.focus", CYAN);
        UIManager.put("Button.focus", CYAN); UIManager.put("ComboBox.background", PANEL); UIManager.put("ComboBox.foreground", TEXT);
        UIManager.put("ComboBox.selectionBackground", new Color(30, 64, 81)); UIManager.put("ComboBox.selectionForeground", TEXT);
        UIManager.put("TableHeader.cellBorder", new EmptyBorder(8, 5, 8, 5));
        UIManager.put("ScrollBar.thumb", new Color(48, 68, 88)); UIManager.put("ScrollBar.track", PANEL);
        UIManager.put("ScrollBar.width", 10); UIManager.put("SplitPane.background", BG); UIManager.put("SplitPaneDivider.border", BorderFactory.createEmptyBorder());
    }

    public static void main(String[] args) throws Exception {
        configureTheme();
        if (args.length > 0 && args[0].equals("--self-test")) { selfTest(); return; }
        if (args.length > 0 && args[0].equals("--ui-test")) { uiTest(args.length > 1 ? args[1] : "preview.png"); return; }
        SwingUtilities.invokeLater(() -> { QuantumMindConsole console = new QuantumMindConsole(); console.setVisible(true); console.setExtendedState(SectionFrame.MAXIMIZED_BOTH); });
    }

    static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
    static void selfTest() throws Exception {
        require(bits("A").equals("01000001"), "UTF-8 ASCII signal"); require(bits("\u00e9").length() == 16, "UTF-8 multibyte signal");
        require("Java".equals(runtimeLanguage("C:\\jdk\\javaw.exe")), "javaw detection");
        require("Python".equals(runtimeLanguage("/usr/bin/python3.12")), "versioned Python detection"); require(runtimeLanguage("javac.exe") == null, "Compiler excluded");
        require(applicationLabel("java", tokenize("java -cp \"C:\\some path\\classes\" -Xmx2g com.example.App --test")).equals("com.example.App"), "Java class parser");
        require(applicationLabel("java", tokenize("java -jar \"C:\\apps\\Example App.jar\"")).equals("Example App.jar"), "Jar parser");
        require(applicationLabel("java", tokenize("java --source 17 Example.java")).equals("Example.java"), "Source launcher parser");
        require(applicationLabel("python", tokenize("python -u \"C:\\some path\\worker.py\" --secret ignored")).equals("worker.py"), "Python script parser");
        require(applicationLabel("python", tokenize("python -m http.server")).equals("http.server"), "Python module parser");
        require(applicationLabel("python", tokenize("python -c \"print('secret')\"")).equals("Python inline script"), "Inline content omitted");
        require(Telemetry.cpuPercent(null, 100, 1000, 8) == -1, "First CPU reading unavailable");
        require(Math.abs(Telemetry.cpuPercent(new long[]{0, 0}, 1_000_000_000, 1_000_000_000, 4) - 25) < .01, "CPU normalized to system");
        require(Telemetry.cpuPercent(new long[]{200, 0}, 100, 1000, 4) == -1, "Counter reset");
        String name = Base64.getEncoder().encodeToString("python.exe".getBytes(StandardCharsets.UTF_8));
        String command = Base64.getEncoder().encodeToString("python \"C:\\worker one.py\"".getBytes(StandardCharsets.UTF_8));
        RuntimeProcess parsed = Telemetry.parseWindowsRow("P\t123\tstarted\t900\t1048576\t" + name + "\t" + command);
        require(parsed != null && parsed.label.equals("worker one.py") && parsed.cpuNanos == 90000 && parsed.rss == 1048576, "Windows telemetry parsing");
        require(Telemetry.parseWindowsRow("bad") == null, "Malformed sample ignored");
        SimulationPanel f = new SimulationPanel();
        for (int i = 0; i < 10000; i++) f.advance(.04);
        require(f.nodes.stream().allMatch(n -> n.x >= .02 && n.x <= .98 && n.y >= .03 && n.y <= .97), "Normalized bounds survive resizing");
        f.mode = Mode.GROUNDED; double x = f.nodes.get(0).x; f.advance(.1); require(f.nodes.get(0).x == x, "Grounding holds");
        f.mode = Mode.FLOW; f.advance(.1); require(f.nodes.get(0).x != x, "Flow resumes after grounding");
        try (Telemetry t = new Telemetry()) { t.start(); Thread.sleep(3500); Snapshot s = t.sample(); Thread.sleep(2200); s = t.sample(); require(s.totalMemory > 0, "Physical RAM available"); require(s.cpu >= 0, "System CPU available"); require(s.processes.stream().anyMatch(p -> p.pid == ProcessHandle.current().pid()), "Current Java process detected"); System.out.println("Telemetry: " + s.processes.size() + " runtimes, source=" + s.source + ", CPU=" + s.cpu + ", RAM=" + memory(s.usedMemory)); }
        System.out.println("PASS: parser, Unicode input, process detection, CPU deltas, field bounds, grounding and live telemetry.");
    }

    static void uiTest(String destination) throws Exception {
        try (Telemetry t = new Telemetry()) {
            t.start(); Thread.sleep(3500); t.sample(); Thread.sleep(2200); Snapshot actual = t.sample();
            SwingUtilities.invokeAndWait(() -> {
                QuantumMindConsole app = new QuantumMindConsole(false);
                try {
                    app.setSize(1500, 960); app.setVisible(true); app.apply(actual);
                    app.zero.doClick(); app.align.doClick(); require(app.field.mode == Mode.ALIGNED && app.field.alignBit == 0, "Align 0 action");
                    app.one.doClick(); require(app.field.alignBit == 1, "Align 1 action");
                    app.input.setText("Quantum Mind / connected"); app.send.doClick(); require(!app.field.signal.isEmpty(), "Text input action");
                    app.ground.doClick(); require(app.field.mode == Mode.GROUNDED, "Ground button"); app.flow.doClick(); require(app.field.mode == Mode.FLOW, "Flow button");
                    app.search.setText("no-match-for-test"); require(app.processTable.getRowCount() == 0, "Search filtering"); app.search.setText("");
                    app.language.setSelectedItem("Python"); require(app.processTable.getRowCount() == actual.processes.stream().filter(p -> p.language.equals("Python")).count(), "Language filter"); app.language.setSelectedIndex(0);
                    app.validate(); for (int i = 0; i < 80; i++) app.field.advance(.025);
                    BufferedImage image = new BufferedImage(app.getContentPane().getWidth(), app.getContentPane().getHeight(), BufferedImage.TYPE_INT_RGB);
                    Graphics2D g = image.createGraphics(); app.getContentPane().paint(g); g.dispose(); ImageIO.write(image, "png", Path.of(destination).toFile());
                    app.setSize(1020, 720); app.validate(); require(app.input.getWidth() > 100 && app.field.getWidth() >= 400, "Small window controls remain usable");
                    require(app.processTable.getParent().getHeight() >= 50, "Compact runtime list remains visible");
                    BufferedImage small = new BufferedImage(app.getContentPane().getWidth(), app.getContentPane().getHeight(), BufferedImage.TYPE_INT_RGB); Graphics2D sg = small.createGraphics(); app.getContentPane().paint(sg); sg.dispose(); ImageIO.write(small, "png", Path.of(destination.replace(".png", "-compact.png")).toFile());
                    System.out.println("PASS: UI actions, filters, text input, expanded and compact window layouts.");
                } catch (IOException ex) { throw new UncheckedIOException(ex); } finally { app.dispose(); }
            });
        }
    }
}
