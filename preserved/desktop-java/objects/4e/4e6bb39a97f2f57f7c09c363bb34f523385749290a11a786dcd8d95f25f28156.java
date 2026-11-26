package net.activeinference.beacon.translation;

import com.sun.management.OperatingSystemMXBean;
import javax.swing.BorderFactory;
import javax.swing.DefaultListModel;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingUtilities;
import javax.swing.SwingWorker;
import javax.swing.Timer;
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
import java.io.InputStream;
import java.lang.management.ManagementFactory;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

public final class ScriptFluxBusWorkbench extends JFrame {
    private static final Color BG = new Color(10, 14, 22);
    private static final Color PANEL = new Color(19, 26, 37);
    private static final Color PANEL_DARK = new Color(13, 19, 29);
    private static final Color TEXT = new Color(225, 235, 247);
    private static final Color MUTED = new Color(139, 157, 180);
    private static final Color CYAN = new Color(70, 214, 236);
    private static final Color GREEN = new Color(111, 227, 165);
    private static final Color VIOLET = new Color(183, 143, 255);
    private static final int CHUNK_SIZE = 512;
    private static final long MAX_SCRIPT_SIZE = 1024L * 1024L;

    private final JTextArea textInput = new JTextArea(2, 40);
    private final JComboBox<ProcessItem> processPicker = new JComboBox<ProcessItem>();
    private final JCheckBox monitorAll = new JCheckBox("Monitor all visible processes");
    private final DefaultListModel<ScriptItem> scriptModel = new DefaultListModel<ScriptItem>();
    private final JList<ScriptItem> scriptList = new JList<ScriptItem>(scriptModel);
    private final JLabel scanStatus = new JLabel("Starting local script scan...");
    private final JLabel cpuStatus = new JLabel("Waiting for OS CPU telemetry...");
    private final JLabel busStatus = new JLabel("Bus queue is empty.");
    private final FluxGridPanel binaryGrid = new FluxGridPanel(FluxGridPanel.Kind.BINARY);
    private final FluxGridPanel ternaryGrid = new FluxGridPanel(FluxGridPanel.Kind.TERNARY);
    private final FluxGridPanel qutritGrid = new FluxGridPanel(FluxGridPanel.Kind.QUTRIT);
    private final ArrayBlockingQueue<BusFrame> busQueue = new ArrayBlockingQueue<BusFrame>(256);
    private final Map<Path, FileStamp> readVersions = new HashMap<Path, FileStamp>();

    private final Timer discoveryTimer;
    private final Timer processRefreshTimer;
    private final Timer busTimer;
    private final Timer animationTimer;
    private final Timer cpuTimer;
    private boolean scanInFlight;
    private boolean processRefreshInFlight;
    private double systemCpuLoad = -1.0;
    private double fluxRate = 0.15;

    private ScriptFluxBusWorkbench() {
        super("Running Script Bus -> Binary / Balanced Ternary / Qutrit Flux");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(1120, 760));
        setSize(1480, 940);
        setLocationRelativeTo(null);

        JPanel root = new JPanel(new BorderLayout(10, 10));
        root.setBackground(BG);
        root.setBorder(new EmptyBorder(13, 15, 11, 15));
        setContentPane(root);
        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildGrids(), BorderLayout.CENTER);
        root.add(buildFooter(), BorderLayout.SOUTH);

        discoveryTimer = new Timer(8000, event -> {
            if (monitorAll.isSelected()) scanScripts(-1L);
        });
        processRefreshTimer = new Timer(12000, event -> refreshProcesses());
        busTimer = new Timer(60, event -> forwardNextFrame());
        animationTimer = new Timer(80, event -> {
            binaryGrid.advance(fluxRate);
            ternaryGrid.advance(fluxRate);
            qutritGrid.advance(fluxRate);
        });
        cpuTimer = new Timer(1000, event -> sampleSystemCpu());
        discoveryTimer.start();
        processRefreshTimer.start();
        busTimer.start();
        animationTimer.start();
        cpuTimer.start();

        refreshProcesses();
        scanScripts(-1L);
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout(0, 8));
        header.setBackground(BG);
        JPanel titleBlock = new JPanel(new BorderLayout(0, 3));
        titleBlock.setBackground(BG);
        JLabel title = new JLabel("Running Script Flux Bus");
        title.setForeground(TEXT);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 22));
        JLabel subtitle = new JLabel(
                "Read-only discovery of running script paths; source bytes are streamed through the three full grids.");
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        titleBlock.add(title, BorderLayout.NORTH);
        titleBlock.add(subtitle, BorderLayout.SOUTH);
        header.add(titleBlock, BorderLayout.NORTH);

        JPanel controls = new JPanel(new GridLayout(2, 1, 0, 5));
        controls.setBackground(BG);
        controls.add(buildTextRow());
        controls.add(buildProcessRow());

        JPanel files = new JPanel(new BorderLayout(0, 4));
        files.setBackground(PANEL);
        files.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(37, 52, 70)),
                new EmptyBorder(5, 8, 5, 8)));
        JLabel fileTitle = new JLabel("DISCOVERED RUNNING .JAVA / .PY / .BAT FILES");
        fileTitle.setForeground(CYAN);
        fileTitle.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 10));
        scriptList.setBackground(PANEL_DARK);
        scriptList.setForeground(TEXT);
        scriptList.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 10));
        scriptList.setVisibleRowCount(3);
        JScrollPane scriptScroll = new JScrollPane(scriptList);
        scriptScroll.setBorder(BorderFactory.createLineBorder(new Color(39, 53, 71)));
        scriptScroll.setPreferredSize(new Dimension(400, 70));
        files.add(fileTitle, BorderLayout.NORTH);
        files.add(scriptScroll, BorderLayout.CENTER);

        JPanel lower = new JPanel(new BorderLayout(0, 5));
        lower.setBackground(BG);
        lower.add(controls, BorderLayout.NORTH);
        lower.add(files, BorderLayout.CENTER);
        header.add(lower, BorderLayout.SOUTH);
        return header;
    }

    private JPanel rowPanel() {
        JPanel row = new JPanel(new BorderLayout(8, 0));
        row.setBackground(PANEL);
        row.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(37, 52, 70)),
                new EmptyBorder(5, 8, 5, 8)));
        return row;
    }

    private JLabel rowLabel(String value) {
        JLabel label = new JLabel(value);
        label.setPreferredSize(new Dimension(145, 27));
        label.setForeground(CYAN);
        label.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 10));
        return label;
    }

    private JPanel buildTextRow() {
        JPanel row = rowPanel();
        JPanel labels = new JPanel(new BorderLayout(0, 2));
        labels.setBackground(PANEL);
        labels.add(rowLabel("TEXT INPUT"), BorderLayout.NORTH);
        JLabel hint = new JLabel("UTF-8, max 512 bytes");
        hint.setForeground(MUTED);
        hint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labels.add(hint, BorderLayout.SOUTH);
        textInput.setLineWrap(true);
        textInput.setWrapStyleWord(true);
        textInput.setForeground(TEXT);
        textInput.setCaretColor(CYAN);
        textInput.setBackground(PANEL_DARK);
        textInput.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 11));
        textInput.setBorder(new EmptyBorder(5, 7, 5, 7));
        JScrollPane textScroll = new JScrollPane(textInput);
        textScroll.setBorder(BorderFactory.createLineBorder(new Color(47, 67, 89)));
        JButton send = button("Queue text", GREEN);
        send.addActionListener(event -> queueText());
        row.add(labels, BorderLayout.WEST);
        row.add(textScroll, BorderLayout.CENTER);
        row.add(send, BorderLayout.EAST);
        return row;
    }

    private JPanel buildProcessRow() {
        JPanel row = rowPanel();
        JPanel labels = new JPanel(new BorderLayout(0, 2));
        labels.setBackground(PANEL);
        labels.add(rowLabel("PROCESS SELECTION"), BorderLayout.NORTH);
        scanStatus.setForeground(MUTED);
        scanStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labels.add(scanStatus, BorderLayout.SOUTH);
        processPicker.setBackground(PANEL_DARK);
        processPicker.setForeground(TEXT);

        JButton refresh = button("Refresh", MUTED);
        refresh.addActionListener(event -> refreshProcesses());
        JButton scan = button("Scan now", CYAN);
        scan.addActionListener(event -> {
            ProcessItem item = (ProcessItem) processPicker.getSelectedItem();
            if (monitorAll.isSelected()) {
                scanScripts(-1L);
            } else if (item != null) {
                scanScripts(item.pid);
            } else {
                scanStatus.setText("Select a process or enable monitor all.");
            }
        });
        monitorAll.setSelected(true);
        monitorAll.setOpaque(false);
        monitorAll.setForeground(TEXT);
        monitorAll.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));

        JPanel actions = new JPanel(new GridLayout(1, 3, 4, 0));
        actions.setBackground(PANEL);
        actions.add(refresh);
        actions.add(monitorAll);
        actions.add(scan);
        row.add(labels, BorderLayout.WEST);
        row.add(processPicker, BorderLayout.CENTER);
        row.add(actions, BorderLayout.EAST);
        return row;
    }

    private JPanel buildGrids() {
        JPanel grids = new JPanel(new GridLayout(1, 3, 9, 0));
        grids.setBackground(BG);
        grids.add(stageCard("01  BINARY", "512-byte bus frames | every bit node shown", binaryGrid, CYAN));
        grids.add(stageCard("02  BALANCED TERNARY", "Exact signed base-3 digits: -1 / 0 / +1", ternaryGrid, GREEN));
        grids.add(stageCard("03  QUTRIT", "One-hot qutrit basis states: |0> / |1> / |2>", qutritGrid, VIOLET));
        return grids;
    }

    private JPanel stageCard(String titleText, String hint, FluxGridPanel grid, Color accent) {
        JPanel card = new JPanel(new BorderLayout(0, 6));
        card.setBackground(PANEL);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(38, 54, 73)),
                new EmptyBorder(7, 7, 7, 7)));
        JPanel heading = new JPanel(new BorderLayout(0, 3));
        heading.setBackground(PANEL);
        JLabel title = new JLabel(titleText);
        title.setForeground(accent);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 12));
        JLabel detail = new JLabel(hint);
        detail.setForeground(MUTED);
        detail.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        heading.add(title, BorderLayout.NORTH);
        heading.add(detail, BorderLayout.SOUTH);
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
        cpuStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        busStatus.setForeground(TEXT);
        busStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        JLabel note = new JLabel(
                "Discovery uses process arguments to find absolute script paths, but does not retain other arguments, inject code, or inspect process memory.");
        note.setForeground(MUTED);
        note.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        footer.add(cpuStatus);
        footer.add(busStatus);
        footer.add(note);
        return footer;
    }

    private JButton button(String text, Color color) {
        JButton button = new JButton(text);
        button.setForeground(color);
        button.setBackground(new Color(26, 35, 49));
        button.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 10));
        button.setFocusPainted(false);
        button.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(48, 65, 86)),
                new EmptyBorder(5, 8, 5, 8)));
        return button;
    }
    private void queueText() {
        byte[] bytes = textInput.getText().getBytes(StandardCharsets.UTF_8);
        if (bytes.length == 0) {
            busStatus.setText("Enter text before queuing it.");
            return;
        }
        if (bytes.length > CHUNK_SIZE) {
            busStatus.setText("Text input exceeds one bus frame (512 UTF-8 bytes).");
            return;
        }
        if (!busQueue.offer(new BusFrame("TEXT INPUT", -1L, 1, 1, bytes))) {
            busStatus.setText("Bus queue is full; wait for queued frames to pass through.");
            return;
        }
        busStatus.setText("Queued text as " + (bytes.length * 8) + " UTF-8 binary nodes.");
    }

    private void forwardNextFrame() {
        BusFrame frame = busQueue.poll();
        if (frame == null) return;
        String bits = bytesToBits(frame.bytes);
        passThrough(bits, frame.source + " | chunk " + frame.chunk + "/" + frame.totalChunks);
        busStatus.setText("Fluxing " + frame.source + " | frame "
                + frame.chunk + "/" + frame.totalChunks
                + " | " + frame.bytes.length + " bytes | " + busQueue.size() + " queued");
    }

    private void passThrough(String bits, String source) {
        try {
            BinaryTernaryQutritTranslator.Translation translated =
                    BinaryTernaryQutritTranslator.translate(bits);
            int[] balanced = toBalancedTernary(translated.getValue());
            binaryGrid.setBinary(translated.getBinary());
            ternaryGrid.setBalanced(balanced);
            qutritGrid.setQutrits(balanced);
            busStatus.setText("Fluxing " + source + " | " + translated.getBinary().length()
                    + " bits -> " + balanced.length + " balanced-trit / qutrit nodes");
        } catch (IllegalArgumentException | IllegalStateException error) {
            busStatus.setText(error.getMessage());
        }
    }

    private void scanScripts(long onlyPid) {
        if (scanInFlight) {
            scanStatus.setText("A scan is already running.");
            return;
        }
        scanInFlight = true;
        scanStatus.setText(onlyPid > 0L ? "Scanning selected process..." : "Scanning all visible processes...");
        new SwingWorker<ScanSummary, Void>() {
            @Override
            protected ScanSummary doInBackground() throws Exception {
                Map<Path, Set<Long>> found = discoverScripts(onlyPid);
                List<ScriptItem> rows = new ArrayList<ScriptItem>();
                for (Map.Entry<Path, Set<Long>> entry : found.entrySet()) {
                    rows.add(new ScriptItem(entry.getKey(), entry.getValue()));
                }
                rows.sort(Comparator.comparing(item -> item.path.toString().toLowerCase(Locale.ROOT)));
                SwingUtilities.invokeLater(() -> replaceScriptList(rows));

                int streamedFiles = 0;
                int chunks = 0;
                int skipped = 0;
                for (Map.Entry<Path, Set<Long>> entry : found.entrySet()) {
                    Path path = entry.getKey();
                    try {
                        BasicFileAttributes attrs = Files.readAttributes(path, BasicFileAttributes.class);
                        if (!attrs.isRegularFile() || attrs.size() > MAX_SCRIPT_SIZE) {
                            skipped++;
                            continue;
                        }
                        FileStamp stamp = new FileStamp(attrs.size(), attrs.lastModifiedTime().toMillis());
                        FileStamp prior = readVersions.get(path);
                        if (stamp.equals(prior)) continue;

                        long owner = entry.getValue().isEmpty() ? -1L : entry.getValue().iterator().next();
                        int fileChunks = streamScript(path, owner, attrs.size());
                        readVersions.put(path, stamp);
                        if (fileChunks > 0) {
                            streamedFiles++;
                            chunks += fileChunks;
                        }
                    } catch (Exception ignored) {
                        skipped++;
                    }
                }
                return new ScanSummary(found.size(), streamedFiles, chunks, skipped);
            }

            @Override
            protected void done() {
                scanInFlight = false;
                try {
                    ScanSummary result = get();
                    scanStatus.setText(result.scriptPaths + " script paths | "
                            + result.streamedFiles + " new/changed files streamed | "
                            + result.chunks + " chunks queued | " + result.skipped + " skipped");
                } catch (Exception error) {
                    Throwable cause = error.getCause() == null ? error : error.getCause();
                    scanStatus.setText("Script scan failed: " + safeMessage(cause));
                }
            }
        }.execute();
    }

    private Map<Path, Set<Long>> discoverScripts(long onlyPid) {
        Map<Path, Set<Long>> found = new LinkedHashMap<Path, Set<Long>>();
        Stream<ProcessHandle> processStream;
        if (onlyPid > 0L) {
            Optional<ProcessHandle> selected = ProcessHandle.of(onlyPid);
            processStream = selected.isPresent()
                    ? Stream.of(selected.get()) : Stream.<ProcessHandle>empty();
        } else {
            processStream = ProcessHandle.allProcesses();
        }
        try (Stream<ProcessHandle> processes = processStream) {
            processes.forEach(process -> {
                try {
                    String expectedExtension = extensionFor(executableName(process));
                    if (expectedExtension.length() == 0) return;
                    String[] args = process.info().arguments().orElse(new String[0]);
                    for (String arg : args) {
                        for (String candidate : scriptPathCandidates(arg)) {
                            try {
                                Path path = Paths.get(candidate).normalize();
                                if (!path.isAbsolute() || !hasExtension(path, expectedExtension)) continue;
                                if (!Files.isRegularFile(path) || !Files.isReadable(path)) continue;
                                Set<Long> owners = found.get(path);
                                if (owners == null) {
                                    owners = new TreeSet<Long>();
                                    found.put(path, owners);
                                }
                                owners.add(process.pid());
                            } catch (RuntimeException ignored) {
                                // Ignore non-path arguments and malformed path fragments.
                            }
                        }
                    }
                } catch (SecurityException ignored) {
                    // Continue scanning other processes when one process is not visible.
                }
            });
        } catch (SecurityException ignored) {
            // Continue with the processes visible to this user.
        }
        return found;
    }

    private List<String> scriptPathCandidates(String argument) {
        List<String> candidates = new ArrayList<String>();
        if (argument == null) return candidates;
        String value = argument.trim();
        if (value.length() == 0) return candidates;
        addCandidate(candidates, value);
        int equals = value.indexOf('=');
        if (equals >= 0 && equals + 1 < value.length()) {
            addCandidate(candidates, value.substring(equals + 1));
        }

        String lower = value.toLowerCase(Locale.ROOT);
        String[] extensions = {".java", ".py", ".bat"};
        for (String extension : extensions) {
            int end = lower.indexOf(extension);
            if (end < 0) continue;
            end += extension.length();
            int drive = value.indexOf(":\\");
            int start = drive > 0 ? drive - 1 : -1;
            int unc = value.indexOf("\\\\");
            if (start < 0 && unc >= 0) start = unc;
            if (start >= 0 && start < end) {
                addCandidate(candidates, value.substring(start, end));
            }
        }
        return candidates;
    }

    private void addCandidate(List<String> candidates, String raw) {
        String value = raw.trim();
        while (value.length() > 0 && (value.charAt(0) == '"' || value.charAt(0) == '\'')) {
            value = value.substring(1).trim();
        }
        while (value.length() > 0 && (value.charAt(value.length() - 1) == '"'
                || value.charAt(value.length() - 1) == '\'')) {
            value = value.substring(0, value.length() - 1).trim();
        }
        if (value.length() > 0 && !candidates.contains(value)) candidates.add(value);
    }

    private String extensionFor(String executable) {
        String name = executable.toLowerCase(Locale.ROOT);
        if (name.equals("java.exe") || name.equals("javaw.exe") || name.equals("java")) return ".java";
        if (name.equals("python.exe") || name.equals("pythonw.exe")
                || name.startsWith("python3") || name.equals("py.exe")) return ".py";
        if (name.equals("cmd.exe") || name.equals("cmd")) return ".bat";
        return "";
    }

    private boolean hasExtension(Path path, String extension) {
        return path.getFileName().toString().toLowerCase(Locale.ROOT).endsWith(extension);
    }

    private int streamScript(Path path, long pid, long fileSize) throws Exception {
        int expectedChunks = (int) Math.max(1L, (fileSize + CHUNK_SIZE - 1L) / CHUNK_SIZE);
        int chunkIndex = 0;
        try (InputStream input = Files.newInputStream(path)) {
            byte[] buffer = new byte[CHUNK_SIZE];
            while (true) {
                int length = 0;
                while (length < buffer.length) {
                    int count = input.read(buffer, length, buffer.length - length);
                    if (count < 0) break;
                    length += count;
                }
                if (length == 0) break;
                byte[] bytes = Arrays.copyOf(buffer, length);
                BusFrame frame = new BusFrame(path.toString(), pid, ++chunkIndex,
                        expectedChunks, bytes);
                busQueue.put(frame);
                if (length < buffer.length) break;
            }
        }
        return chunkIndex;
    }
    private void refreshProcesses() {
        if (processRefreshInFlight) return;
        processRefreshInFlight = true;
        new SwingWorker<List<ProcessItem>, Void>() {
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
                    scanStatus.setText(items.size() + " visible processes; executable names only.");
                } catch (Exception error) {
                    Throwable cause = error.getCause() == null ? error : error.getCause();
                    scanStatus.setText("Process list unavailable: " + safeMessage(cause));
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

    private void replaceScriptList(List<ScriptItem> items) {
        scriptModel.clear();
        for (ScriptItem item : items) scriptModel.addElement(item);
    }

    private void sampleSystemCpu() {
        double load = -1.0;
        try {
            java.lang.management.OperatingSystemMXBean bean =
                    ManagementFactory.getOperatingSystemMXBean();
            if (bean instanceof OperatingSystemMXBean) {
                double reading = ((OperatingSystemMXBean) bean).getSystemCpuLoad();
                if (reading >= 0.0 && reading <= 1.0) load = reading;
            }
        } catch (RuntimeException ignored) {
            // The OS may not expose a CPU-load value.
        }
        systemCpuLoad = load;
        fluxRate = load >= 0.0 ? 0.12 + load * 0.72 : 0.20;
        cpuStatus.setText(load >= 0.0
                ? String.format(Locale.ROOT,
                        "OS-reported system CPU load: %.1f%% | grid flux rate: %.2f | local sampling",
                        load * 100.0, fluxRate)
                : "OS CPU-load value unavailable | grid uses a steady visualization rate");
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

    private String safeMessage(Throwable error) {
        return error.getMessage() == null
                ? error.getClass().getSimpleName() : error.getMessage();
    }

    private static final class ProcessItem {
        private final long pid;
        private final String executable;

        private ProcessItem(long pid, String executable) {
            this.pid = pid;
            this.executable = executable;
        }

        @Override
        public String toString() {
            return "PID " + pid + " | " + executable;
        }
    }

    private static final class ScriptItem {
        private final Path path;
        private final Set<Long> ownerPids;

        private ScriptItem(Path path, Set<Long> ownerPids) {
            this.path = path;
            this.ownerPids = new TreeSet<Long>(ownerPids);
        }

        @Override
        public String toString() {
            return path.toString() + "  [PID " + ownerPids.toString() + "]";
        }
    }

    private static final class FileStamp {
        private final long size;
        private final long modifiedMillis;

        private FileStamp(long size, long modifiedMillis) {
            this.size = size;
            this.modifiedMillis = modifiedMillis;
        }

        @Override
        public boolean equals(Object other) {
            if (!(other instanceof FileStamp)) return false;
            FileStamp stamp = (FileStamp) other;
            return size == stamp.size && modifiedMillis == stamp.modifiedMillis;
        }

        @Override
        public int hashCode() {
            return (int) (size ^ (size >>> 32) ^ modifiedMillis ^ (modifiedMillis >>> 32));
        }
    }

    private static final class BusFrame {
        private final String source;
        private final long pid;
        private final int chunk;
        private final int totalChunks;
        private final byte[] bytes;

        private BusFrame(String source, long pid, int chunk, int totalChunks, byte[] bytes) {
            this.source = source;
            this.pid = pid;
            this.chunk = chunk;
            this.totalChunks = totalChunks;
            this.bytes = bytes;
        }
    }

    private static final class ScanSummary {
        private final int scriptPaths;
        private final int streamedFiles;
        private final int chunks;
        private final int skipped;

        private ScanSummary(int scriptPaths, int streamedFiles, int chunks, int skipped) {
            this.scriptPaths = scriptPaths;
            this.streamedFiles = streamedFiles;
            this.chunks = chunks;
            this.skipped = skipped;
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
            setPreferredSize(new Dimension(420, 430));
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
            int tileWidth = kind == Kind.QUTRIT ? 55 : kind == Kind.TERNARY ? 43 : 34;
            int gap = 4;
            int columns = Math.max(1, (420 - 18) / (tileWidth + gap));
            int rows = (seeds.length + columns - 1) / columns;
            return new Dimension(420, Math.max(430, 28 + rows * 28));
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setColor(MUTED);
            g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
            String heading = kind == Kind.BINARY ? "binary: 0 / 1"
                    : kind == Kind.TERNARY ? "balanced ternary: -1 / 0 / +1"
                    : "qutrit basis: |0> / |1> / |2>";
            g.drawString(heading + " | " + seeds.length + " nodes", 8, 14);

            int tileWidth = kind == Kind.QUTRIT ? 55 : kind == Kind.TERNARY ? 43 : 34;
            int tileHeight = 23;
            int gap = 4;
            int availableWidth = Math.max(1, getWidth() - 16);
            int columns = Math.max(1, availableWidth / (tileWidth + gap));
            int actualWidth = Math.max(tileWidth, (availableWidth - (columns - 1) * gap) / columns);
            Rectangle clip = g.getClipBounds();
            if (clip == null) clip = new Rectangle(0, 0, getWidth(), getHeight());
            int rowStep = tileHeight + gap;
            int firstRow = Math.max(0, (clip.y - 19) / rowStep);
            int endRow = Math.min((seeds.length + columns - 1) / columns,
                    (clip.y + clip.height - 19) / rowStep + 1);

            for (int row = firstRow; row < endRow; row++) {
                int first = row * columns;
                int end = Math.min(seeds.length, first + columns);
                for (int i = first; i < end; i++) {
                    int col = i - first;
                    int x = 8 + col * (actualWidth + gap);
                    int y = 19 + row * rowStep;
                    int stateCount = kind == Kind.BINARY ? 2 : 3;
                    double nodeRate = 0.62 + (i % 11) * 0.035;
                    int step = (int) Math.floor(phase * nodeRate);
                    int state = Math.floorMod(seeds[i] + step, stateCount);
                    Color base = colorFor(state);
                    double pulse = 0.5 + 0.5 * Math.sin(phase * 1.7 + i * 0.43);
                    g.setColor(blend(PANEL, base, 0.25 + pulse * 0.48));
                    g.fillRoundRect(x, y, actualWidth, tileHeight, 6, 6);
                    g.setColor(blend(base, Color.WHITE, 0.10 + pulse * 0.25));
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
            // Swing's default look and feel is sufficient.
        }
        SwingUtilities.invokeLater(() -> {
            ScriptFluxBusWorkbench app = new ScriptFluxBusWorkbench();
            app.setVisible(true);
        });
    }
}
