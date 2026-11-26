package net.activeinference.beacon.translation;
import neural.studio.*;


import com.sun.management.OperatingSystemMXBean;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import neural.studio.SectionFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import neural.studio.SharedSwingWorker;
import neural.studio.SharedTimer;
import javax.swing.UIManager;
import javax.swing.border.EmptyBorder;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GridLayout;
import java.awt.Rectangle;
import java.awt.RenderingHints;
import java.lang.management.ManagementFactory;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.stream.Stream;

/** Full local telemetry translator with read-only process selection. */
public final class KernelCpuFluxWorkbench extends SectionFrame {
    private static final Color BG = new Color(10, 14, 22);
    private static final Color PANEL = new Color(19, 26, 37);
    private static final Color PANEL_DARK = new Color(13, 19, 29);
    private static final Color TEXT = new Color(225, 235, 247);
    private static final Color MUTED = new Color(139, 157, 180);
    private static final Color CYAN = new Color(70, 214, 236);
    private static final Color GREEN = new Color(111, 227, 165);
    private static final Color VIOLET = new Color(183, 143, 255);
    private static final int MAX_TEXT_BYTES = BinaryTernaryQutritTranslator.MAX_INPUT_BITS / 8;

    private final JTextField binaryInput = new JTextField("10101010101010");
    private final JTextArea textInput = new JTextArea(2, 32);
    private final JComboBox<ProcessItem> processPicker = new JComboBox<ProcessItem>();
    private final JCheckBox includeProcess = new JCheckBox("Include selected process live");
    private final JLabel processStatus = new JLabel("Visible process list refreshes every five seconds.");
    private final JLabel cpuStatus = new JLabel("Waiting for OS CPU telemetry...");
    private final JLabel translationStatus = new JLabel("Live CPU telemetry is the active source.");
    private final FluxGridPanel binaryGrid = new FluxGridPanel(FluxGridPanel.Kind.BINARY);
    private final FluxGridPanel ternaryGrid = new FluxGridPanel(FluxGridPanel.Kind.TERNARY);
    private final FluxGridPanel qutritGrid = new FluxGridPanel(FluxGridPanel.Kind.QUTRIT);

    private final SharedTimer animationTimer;
    private final SharedTimer samplingTimer;
    private final SharedTimer processRefreshTimer;
    private boolean sampleInFlight;
    private boolean processRefreshInFlight;
    private Mode mode = Mode.SYSTEM;
    private double systemLoad = -1.0;
    private double selectedProcessLoad = -1.0;
    private double fluxRate = 0.15;
    private long previousPid = -1L;
    private long previousCpuMillis = -1L;
    private long previousSampleNanos = -1L;
    private long latestCpuDeltaMillis = -1L;

    private enum Mode { SYSTEM, PROCESS, TEXT, BINARY }

    private KernelCpuFluxWorkbench() {
        super("Live System CPU -> Binary -> Balanced Ternary -> Qutrit Grid");
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(1120, 760));
        setSize(1480, 930);
        setLocationRelativeTo(null);

        JPanel root = new JPanel(new BorderLayout(11, 11));
        root.setBackground(BG);
        root.setBorder(new EmptyBorder(14, 16, 12, 16));
        setContentPane(root);
        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildGrids(), BorderLayout.CENTER);
        root.add(buildFooter(), BorderLayout.SOUTH);

        animationTimer = new SharedTimer(80, event -> {
            binaryGrid.advance(fluxRate);
            ternaryGrid.advance(fluxRate);
            qutritGrid.advance(fluxRate);
        });
        samplingTimer = new SharedTimer(1000, event -> sampleTelemetry());
        processRefreshTimer = new SharedTimer(5000, event -> refreshProcesses());
        animationTimer.start();
        samplingTimer.start();
        processRefreshTimer.start();

        passThrough(binaryInput.getText(), "Manual binary example");
        refreshProcesses();
        sampleTelemetry();
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout(0, 8));
        header.setBackground(BG);
        JPanel titleBlock = new JPanel(new BorderLayout(0, 3));
        titleBlock.setBackground(BG);
        JLabel title = new JLabel("Full System CPU Flux Matrix");
        title.setForeground(TEXT);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 23));
        JLabel subtitle = new JLabel(
                "OS-reported CPU telemetry seeds the full grids; measured CPU load controls the state-flux rate.");
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        titleBlock.add(title, BorderLayout.NORTH);
        titleBlock.add(subtitle, BorderLayout.SOUTH);
        header.add(titleBlock, BorderLayout.NORTH);

        JPanel inputs = new JPanel(new GridLayout(3, 1, 0, 5));
        inputs.setBackground(BG);
        inputs.add(buildBinaryRow());
        inputs.add(buildTextRow());
        inputs.add(buildProcessRow());
        header.add(inputs, BorderLayout.SOUTH);
        return header;
    }

    private JPanel rowPanel() {
        JPanel row = new JPanel(new BorderLayout(8, 0));
        row.setBackground(PANEL);
        row.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(37, 52, 70)),
                new EmptyBorder(6, 8, 6, 8)));
        return row;
    }

    private JLabel rowLabel(String text) {
        JLabel label = new JLabel(text);
        label.setPreferredSize(new Dimension(148, 28));
        label.setForeground(CYAN);
        label.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        return label;
    }

    private JPanel buildBinaryRow() {
        JPanel row = rowPanel();
        binaryInput.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        binaryInput.setForeground(TEXT);
        binaryInput.setCaretColor(CYAN);
        binaryInput.setBackground(PANEL_DARK);
        binaryInput.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(47, 67, 89)),
                new EmptyBorder(6, 8, 6, 8)));

        JButton translate = button("Translate binary", CYAN);
        translate.addActionListener(event -> translateBinary());
        binaryInput.addActionListener(event -> translateBinary());
        JButton liveCpu = button("Live CPU stream", GREEN);
        liveCpu.addActionListener(event -> useSystemCpu());

        JPanel actions = new JPanel(new GridLayout(1, 2, 5, 0));
        actions.setBackground(PANEL);
        actions.add(translate);
        actions.add(liveCpu);
        row.add(rowLabel("BINARY INPUT"), BorderLayout.WEST);
        row.add(binaryInput, BorderLayout.CENTER);
        row.add(actions, BorderLayout.EAST);
        return row;
    }

    private JPanel buildTextRow() {
        JPanel row = rowPanel();
        JPanel labels = new JPanel(new BorderLayout(0, 2));
        labels.setBackground(PANEL);
        labels.add(rowLabel("TEXT -> UTF-8 BITS"), BorderLayout.NORTH);
        JLabel hint = new JLabel("up to 512 bytes");
        hint.setForeground(MUTED);
        hint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labels.add(hint, BorderLayout.SOUTH);

        textInput.setLineWrap(true);
        textInput.setWrapStyleWord(true);
        textInput.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        textInput.setForeground(TEXT);
        textInput.setCaretColor(CYAN);
        textInput.setBackground(PANEL_DARK);
        textInput.setBorder(new EmptyBorder(5, 7, 5, 7));
        JScrollPane textScroll = new JScrollPane(textInput);
        textScroll.setBorder(BorderFactory.createLineBorder(new Color(47, 67, 89)));
        JButton translate = button("Translate text", GREEN);
        translate.addActionListener(event -> translateText());

        row.add(labels, BorderLayout.WEST);
        row.add(textScroll, BorderLayout.CENTER);
        row.add(translate, BorderLayout.EAST);
        return row;
    }

    private JPanel buildProcessRow() {
        JPanel row = rowPanel();
        JPanel labels = new JPanel(new BorderLayout(0, 2));
        labels.setBackground(PANEL);
        labels.add(rowLabel("PROCESS SELECTION"), BorderLayout.NORTH);
        processStatus.setForeground(MUTED);
        processStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labels.add(processStatus, BorderLayout.SOUTH);

        processPicker.setBackground(PANEL_DARK);
        processPicker.setForeground(TEXT);
        JButton refresh = button("Refresh", MUTED);
        refresh.addActionListener(event -> refreshProcesses());

        includeProcess.setOpaque(false);
        includeProcess.setForeground(TEXT);
        includeProcess.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        includeProcess.addActionListener(event -> {
            if (includeProcess.isSelected()) {
                if (processPicker.getSelectedItem() == null) {
                    includeProcess.setSelected(false);
                    processStatus.setText("Select a process first.");
                } else {
                    mode = Mode.PROCESS;
                    resetProcessDelta();
                    sampleTelemetry();
                }
            } else {
                mode = Mode.SYSTEM;
                resetProcessDelta();
                sampleTelemetry();
            }
        });

        JPanel actions = new JPanel(new GridLayout(1, 2, 5, 0));
        actions.setBackground(PANEL);
        actions.add(refresh);
        actions.add(includeProcess);
        row.add(labels, BorderLayout.WEST);
        row.add(processPicker, BorderLayout.CENTER);
        row.add(actions, BorderLayout.EAST);
        return row;
    }

    private JPanel buildGrids() {
        JPanel grids = new JPanel(new GridLayout(1, 3, 9, 0));
        grids.setBackground(BG);
        grids.add(stageCard("01  BINARY", "OS telemetry frame or UTF-8 input bytes", binaryGrid, CYAN));
        grids.add(stageCard("02  BALANCED TERNARY", "Exact conversion: -1 / 0 / +1", ternaryGrid, GREEN));
        grids.add(stageCard("03  QUTRIT", "Basis-state flux: |0> / |1> / |2>", qutritGrid, VIOLET));
        return grids;
    }

    private JPanel stageCard(String titleText, String hintText, FluxGridPanel grid, Color accent) {
        JPanel card = new JPanel(new BorderLayout(0, 7));
        card.setBackground(PANEL);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(38, 54, 73)),
                new EmptyBorder(8, 8, 8, 8)));
        JPanel heading = new JPanel(new BorderLayout(0, 3));
        heading.setBackground(PANEL);
        JLabel title = new JLabel(titleText);
        title.setForeground(accent);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 13));
        JLabel hint = new JLabel(hintText);
        hint.setForeground(MUTED);
        hint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        heading.add(title, BorderLayout.NORTH);
        heading.add(hint, BorderLayout.SOUTH);

        JScrollPane scroll = new JScrollPane(grid);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(34, 47, 65)));
        scroll.getViewport().setBackground(PANEL_DARK);
        scroll.getVerticalScrollBar().setUnitIncrement(24);
        card.add(heading, BorderLayout.NORTH);
        card.add(scroll, BorderLayout.CENTER);
        return card;
    }

    private JPanel buildFooter() {
        JPanel footer = new JPanel(new GridLayout(3, 1, 0, 2));
        footer.setBackground(BG);
        cpuStatus.setForeground(CYAN);
        cpuStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        translationStatus.setForeground(TEXT);
        translationStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        JLabel note = new JLabel(
                "OS telemetry is not kernel instruction bits. Flux is a visualization driven by measured load, not process memory or quantum hardware.");
        note.setForeground(MUTED);
        note.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        footer.add(cpuStatus);
        footer.add(translationStatus);
        footer.add(note);
        return footer;
    }

    private JButton button(String text, Color foreground) {
        JButton button = new JButton(text);
        button.setForeground(foreground);
        button.setBackground(new Color(26, 35, 49));
        button.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        button.setFocusPainted(false);
        button.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(48, 65, 86)),
                new EmptyBorder(6, 9, 6, 9)));
        return button;
    }

    private void translateBinary() {
        mode = Mode.BINARY;
        includeProcess.setSelected(false);
        passThrough(binaryInput.getText(), "Manual binary input");
    }

    private void translateText() {
        byte[] bytes = textInput.getText().getBytes(StandardCharsets.UTF_8);
        if (bytes.length == 0) {
            showError("Enter text first.");
            return;
        }
        if (bytes.length > MAX_TEXT_BYTES) {
            showError("Text is " + bytes.length + " UTF-8 bytes; limit is " + MAX_TEXT_BYTES + ".");
            return;
        }
        mode = Mode.TEXT;
        includeProcess.setSelected(false);
        passThrough(bytesToBits(bytes), "Text (" + bytes.length + " UTF-8 bytes)");
    }

    private void useSystemCpu() {
        mode = Mode.SYSTEM;
        includeProcess.setSelected(false);
        resetProcessDelta();
        sampleTelemetry();
    }

    private void passThrough(String bits, String source) {
        try {
            BinaryTernaryQutritTranslator.Translation translated =
                    BinaryTernaryQutritTranslator.translate(bits);
            int[] balanced = toBalancedTernary(translated.getValue());
            binaryGrid.setBinary(translated.getBinary());
            ternaryGrid.setBalanced(balanced);
            qutritGrid.setQutrits(balanced);
            translationStatus.setForeground(TEXT);
            translationStatus.setText(String.format(Locale.ROOT,
                    "Source: %s | %d binary nodes -> %d balanced-trit / qutrit nodes | integer %s",
                    source, translated.getBinary().length(), balanced.length,
                    translated.getValue().toString()));
        } catch (IllegalArgumentException | IllegalStateException error) {
            showError(error.getMessage());
        }
    }

    private void sampleTelemetry() {
        if (sampleInFlight) return;
        sampleInFlight = true;
        ProcessItem selected = mode == Mode.PROCESS
                ? (ProcessItem) processPicker.getSelectedItem() : null;
        long selectedPid = selected == null ? -1L : selected.pid;

        new SharedSwingWorker<CpuSnapshot, Void>() {
            @Override
            protected CpuSnapshot doInBackground() {
                return readCpuSnapshot(selectedPid);
            }

            @Override
            protected void done() {
                sampleInFlight = false;
                try {
                    CpuSnapshot snapshot = get();
                    updateSnapshot(snapshot);
                    if (mode == Mode.SYSTEM || mode == Mode.PROCESS) {
                        passThrough(encodeCpuFrame(snapshot, mode == Mode.PROCESS),
                                mode == Mode.PROCESS
                                        ? "OS CPU + selected process telemetry"
                                        : "OS system CPU telemetry");
                    }
                } catch (Exception error) {
                    Throwable cause = error.getCause() == null ? error : error.getCause();
                    showError("CPU sample unavailable: " + message(cause));
                }
            }
        }.execute();
    }
    private CpuSnapshot readCpuSnapshot(long pid) {
        long sampledAt = System.nanoTime();
        int processors = Math.max(1, Runtime.getRuntime().availableProcessors());
        double load = -1.0;
        try {
            java.lang.management.OperatingSystemMXBean bean = ManagementFactory.getOperatingSystemMXBean();
            if (bean instanceof OperatingSystemMXBean) {
                double reported = ((OperatingSystemMXBean) bean).getSystemCpuLoad();
                if (reported >= 0.0 && reported <= 1.0) load = reported;
            }
        } catch (RuntimeException ignored) {
            // Leave the CPU-load sentinel at -1 when the OS does not report it.
        }

        long totalCpuMillis = -1L;
        boolean alive = false;
        if (pid > 0L) {
            try {
                Optional<ProcessHandle> found = ProcessHandle.of(pid);
                if (found.isPresent()) {
                    ProcessHandle handle = found.get();
                    alive = handle.isAlive();
                    Optional<Duration> cpu = handle.info().totalCpuDuration();
                    if (cpu.isPresent()) totalCpuMillis = cpu.get().toMillis();
                }
            } catch (SecurityException ignored) {
                // The OS may restrict metadata for a process.
            }
        }
        return new CpuSnapshot(sampledAt, processors, load, pid, totalCpuMillis, alive);
    }

    private void updateSnapshot(CpuSnapshot snapshot) {
        systemLoad = snapshot.systemLoad;
        selectedProcessLoad = -1.0;
        latestCpuDeltaMillis = -1L;

        if (snapshot.pid > 0L && snapshot.alive && snapshot.totalCpuMillis >= 0L) {
            if (previousPid == snapshot.pid && previousCpuMillis >= 0L
                    && previousSampleNanos > 0L && snapshot.sampledAtNanos > previousSampleNanos) {
                latestCpuDeltaMillis = Math.max(0L, snapshot.totalCpuMillis - previousCpuMillis);
                double elapsedMillis = (snapshot.sampledAtNanos - previousSampleNanos) / 1_000_000.0;
                selectedProcessLoad = Math.max(0.0, Math.min(1.0,
                        latestCpuDeltaMillis / elapsedMillis / snapshot.logicalProcessors));
            }
            previousPid = snapshot.pid;
            previousCpuMillis = snapshot.totalCpuMillis;
            previousSampleNanos = snapshot.sampledAtNanos;
        } else if (snapshot.pid > 0L) {
            resetProcessDelta();
        } else {
            resetProcessDelta();
        }

        fluxRate = 0.12
                + (systemLoad >= 0.0 ? systemLoad * 0.55 : 0.12)
                + (selectedProcessLoad >= 0.0 ? selectedProcessLoad * 0.30 : 0.0);
        fluxRate = Math.min(0.90, fluxRate);

        String systemText = systemLoad >= 0.0
                ? String.format(Locale.ROOT, "%.1f%%", systemLoad * 100.0)
                : "unavailable";
        String processText = selectedProcessLoad >= 0.0
                ? String.format(Locale.ROOT, "%.1f%%", selectedProcessLoad * 100.0)
                : "n/a";
        cpuStatus.setText(String.format(Locale.ROOT,
                "OS system CPU: %s | selected-process CPU: %s | logical processors: %d | flux rate: %.2f",
                systemText, processText, snapshot.logicalProcessors, fluxRate));

        if (snapshot.pid > 0L) {
            if (!snapshot.alive) {
                processStatus.setText("Selected process exited.");
            } else if (snapshot.totalCpuMillis < 0L) {
                processStatus.setText("PID " + snapshot.pid + " | CPU time unavailable.");
            } else {
                processStatus.setText("PID " + snapshot.pid + " | cumulative CPU "
                        + snapshot.totalCpuMillis + " ms.");
            }
        }
    }

    private String encodeCpuFrame(CpuSnapshot snapshot, boolean withProcess) {
        boolean hasProcess = withProcess && snapshot.pid > 0L && snapshot.alive;
        int length = 4 + 8 + 4 + 1 + (hasProcess ? 32 : 0);
        ByteBuffer frame = ByteBuffer.allocate(length).order(ByteOrder.BIG_ENDIAN);
        frame.putInt(0x43505531); // ASCII "CPU1"
        frame.putLong(Double.doubleToRawLongBits(snapshot.systemLoad));
        frame.putInt(snapshot.logicalProcessors);
        frame.put((byte) (hasProcess ? 1 : 0));
        if (hasProcess) {
            frame.putLong(snapshot.pid);
            frame.putLong(Double.doubleToRawLongBits(selectedProcessLoad));
            frame.putLong(snapshot.totalCpuMillis);
            frame.putLong(latestCpuDeltaMillis);
        }
        return bytesToBits(frame.array());
    }

    private void refreshProcesses() {
        if (processRefreshInFlight) return;
        processRefreshInFlight = true;
        processStatus.setText("Refreshing visible process list...");
        new SharedSwingWorker<List<ProcessItem>, Void>() {
            @Override
            protected List<ProcessItem> doInBackground() {
                List<ProcessItem> items = new ArrayList<ProcessItem>();
                try (Stream<ProcessHandle> processes = ProcessHandle.allProcesses()) {
                    processes.forEach(process -> {
                        String executable = executableName(process);
                        if (executable.length() > 0) {
                            items.add(new ProcessItem(process.pid(), executable));
                        }
                    });
                }
                items.sort(Comparator.comparingLong(item -> item.pid));
                return items;
            }

            @Override
            protected void done() {
                processRefreshInFlight = false;
                try {
                    List<ProcessItem> items = get();
                    ProcessItem old = (ProcessItem) processPicker.getSelectedItem();
                    long oldPid = old == null ? -1L : old.pid;
                    processPicker.removeAllItems();
                    ProcessItem restore = null;
                    for (ProcessItem item : items) {
                        processPicker.addItem(item);
                        if (item.pid == oldPid) restore = item;
                    }
                    if (restore != null) processPicker.setSelectedItem(restore);
                    processStatus.setText(items.size() + " visible processes; names only.");
                } catch (Exception error) {
                    Throwable cause = error.getCause() == null ? error : error.getCause();
                    processStatus.setText("Process list unavailable: " + message(cause));
                }
            }
        }.execute();
    }

    private String executableName(ProcessHandle process) {
        try {
            Optional<String> command = process.info().command();
            if (!command.isPresent() || command.get().length() == 0) return "";
            return Paths.get(command.get()).getFileName().toString();
        } catch (RuntimeException error) {
            return "";
        }
    }

    private int[] toBalancedTernary(java.math.BigInteger value) {
        if (value.signum() == 0) return new int[] {0};
        java.math.BigInteger three = java.math.BigInteger.valueOf(3);
        java.math.BigInteger remaining = value;
        List<Integer> reversed = new ArrayList<Integer>();
        while (remaining.signum() > 0) {
            java.math.BigInteger[] division = remaining.divideAndRemainder(three);
            int remainder = division[1].intValue();
            if (remainder == 2) {
                reversed.add(-1);
                remaining = division[0].add(java.math.BigInteger.ONE);
            } else {
                reversed.add(remainder);
                remaining = division[0];
            }
        }
        int[] digits = new int[reversed.size()];
        for (int i = 0; i < digits.length; i++) {
            digits[i] = reversed.get(digits.length - 1 - i);
        }
        return digits;
    }

    private String bytesToBits(byte[] bytes) {
        StringBuilder bits = new StringBuilder(bytes.length * 8);
        for (byte value : bytes) {
            for (int shift = 7; shift >= 0; shift--) {
                bits.append(((value >>> shift) & 1) == 1 ? '1' : '0');
            }
        }
        return bits.toString();
    }

    private void resetProcessDelta() {
        previousPid = -1L;
        previousCpuMillis = -1L;
        previousSampleNanos = -1L;
        latestCpuDeltaMillis = -1L;
        selectedProcessLoad = -1.0;
    }

    private String message(Throwable error) {
        return error.getMessage() == null
                ? error.getClass().getSimpleName() : error.getMessage();
    }

    private void showError(String text) {
        translationStatus.setForeground(new Color(255, 137, 145));
        translationStatus.setText(text);
    }

    private static final class CpuSnapshot {
        private final long sampledAtNanos;
        private final int logicalProcessors;
        private final double systemLoad;
        private final long pid;
        private final long totalCpuMillis;
        private final boolean alive;

        private CpuSnapshot(long sampledAtNanos, int logicalProcessors, double systemLoad,
                            long pid, long totalCpuMillis, boolean alive) {
            this.sampledAtNanos = sampledAtNanos;
            this.logicalProcessors = logicalProcessors;
            this.systemLoad = systemLoad;
            this.pid = pid;
            this.totalCpuMillis = totalCpuMillis;
            this.alive = alive;
        }
    }

    private static final class ProcessItem {
        private final long pid;
        private final String name;

        private ProcessItem(long pid, String name) {
            this.pid = pid;
            this.name = name;
        }

        @Override
        public String toString() {
            return "PID " + pid + " | " + name;
        }
    }

    private static final class FluxGridPanel extends JPanel {
        private enum Kind { BINARY, TERNARY, QUTRIT }

        private final Kind kind;
        private int[] seeds = new int[0];
        private double phase;

        private FluxGridPanel(Kind kind) {
            this.kind = kind;
            setOpaque(true);
            setBackground(PANEL_DARK);
            setPreferredSize(new Dimension(420, 500));
        }

        private void setBinary(String bits) {
            seeds = new int[bits.length()];
            for (int i = 0; i < bits.length(); i++) seeds[i] = bits.charAt(i) - '0';
            reset();
        }

        private void setBalanced(int[] digits) {
            seeds = new int[digits.length];
            for (int i = 0; i < digits.length; i++) seeds[i] = digits[i] + 1;
            reset();
        }

        private void setQutrits(int[] digits) {
            seeds = new int[digits.length];
            for (int i = 0; i < digits.length; i++) seeds[i] = digits[i] + 1;
            reset();
        }

        private void reset() {
            phase = 0.0;
            revalidate();
            repaint();
        }

        private void advance(double rate) {
            phase = (phase + rate) % 100000.0;
            repaint();
        }

        @Override
        public Dimension getPreferredSize() {
            int tileWidth = kind == Kind.QUTRIT ? 54 : kind == Kind.TERNARY ? 43 : 34;
            int gap = 4;
            int columns = Math.max(1, (420 - 18) / (tileWidth + gap));
            int rows = (seeds.length + columns - 1) / columns;
            return new Dimension(420, Math.max(500, 34 + rows * 28));
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setColor(MUTED);
            g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
            String heading = kind == Kind.BINARY ? "binary states: 0 / 1"
                    : kind == Kind.TERNARY ? "balanced trits: -1 / 0 / +1"
                    : "qutrit basis: |0> / |1> / |2>";
            g.drawString(heading + " | " + seeds.length + " nodes", 9, 15);

            int tileWidth = kind == Kind.QUTRIT ? 54 : kind == Kind.TERNARY ? 43 : 34;
            int tileHeight = 24;
            int gap = 4;
            int availableWidth = Math.max(1, getWidth() - 18);
            int columns = Math.max(1, availableWidth / (tileWidth + gap));
            int actualWidth = Math.max(tileWidth, (availableWidth - (columns - 1) * gap) / columns);
            Rectangle clip = g.getClipBounds();
            if (clip == null) clip = new Rectangle(0, 0, getWidth(), getHeight());
            int rowStep = tileHeight + gap;
            int firstRow = Math.max(0, (clip.y - 20) / rowStep);
            int endRow = Math.min((seeds.length + columns - 1) / columns,
                    (clip.y + clip.height - 20) / rowStep + 1);

            for (int row = firstRow; row < endRow; row++) {
                int start = row * columns;
                int end = Math.min(seeds.length, start + columns);
                for (int i = start; i < end; i++) {
                    int column = i - start;
                    int x = 9 + column * (actualWidth + gap);
                    int y = 20 + row * rowStep;
                    int stateCount = kind == Kind.BINARY ? 2 : 3;
                    double nodeRate = 0.60 + (i % 9) * 0.045;
                    int advance = (int) Math.floor(phase * nodeRate);
                    int state = Math.floorMod(seeds[i] + advance, stateCount);
                    Color base = colorFor(state);
                    double pulse = 0.5 + 0.5 * Math.sin(phase * 1.8 + i * 0.39);
                    g.setColor(blend(PANEL, base, 0.24 + pulse * 0.50));
                    g.fillRoundRect(x, y, actualWidth, tileHeight, 6, 6);
                    g.setColor(blend(base, Color.WHITE, 0.12 + pulse * 0.25));
                    g.drawRoundRect(x, y, actualWidth, tileHeight, 6, 6);
                    g.setColor(TEXT);
                    g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 11));
                    String symbol = symbolFor(state);
                    int textWidth = g.getFontMetrics().stringWidth(symbol);
                    g.drawString(symbol, x + Math.max(3, (actualWidth - textWidth) / 2), y + 16);
                }
            }
            g.dispose();
        }

        private String symbolFor(int state) {
            if (kind == Kind.BINARY) return state == 0 ? "0" : "1";
            if (kind == Kind.TERNARY) return state == 0 ? "-1" : state == 1 ? "0" : "+1";
            return state == 0 ? "|0>" : state == 1 ? "|1>" : "|2>";
        }

        private Color colorFor(int state) {
            if (kind == Kind.BINARY) return state == 0 ? new Color(58, 116, 177) : CYAN;
            if (kind == Kind.TERNARY) return state == 0 ? new Color(237, 151, 93)
                    : state == 1 ? GREEN : new Color(73, 188, 157);
            return state == 0 ? VIOLET : state == 1
                    ? new Color(241, 128, 194) : new Color(89, 160, 255);
        }

        private Color blend(Color from, Color to, double amount) {
            double t = Math.max(0.0, Math.min(1.0, amount));
            return new Color(
                    (int) (from.getRed() * (1.0 - t) + to.getRed() * t),
                    (int) (from.getGreen() * (1.0 - t) + to.getGreen() * t),
                    (int) (from.getBlue() * (1.0 - t) + to.getBlue() * t));
        }
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
            // Standard Swing look and feel is sufficient.
        }
        SwingUtilities.invokeLater(() -> {
            KernelCpuFluxWorkbench app = new KernelCpuFluxWorkbench();
            app.setVisible(true);
        });
    }
}