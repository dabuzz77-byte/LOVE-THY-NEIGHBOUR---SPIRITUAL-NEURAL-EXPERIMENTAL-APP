package net.activeinference.beacon.translation;
import neural.studio.*;


import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.SwingWorker;
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
import java.awt.RenderingHints;
import java.awt.Toolkit;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.stream.Stream;

/**
 * Live animated view over real translated symbols. Process inspection is
 * limited to read-only PID, executable name, liveness, and CPU-time metadata.
 */
public final class LiveTranslationWorkbench extends SectionFrame {
    private static final Color BG = new Color(10, 14, 22);
    private static final Color PANEL = new Color(19, 26, 37);
    private static final Color PANEL_DARK = new Color(13, 19, 29);
    private static final Color TEXT = new Color(225, 235, 247);
    private static final Color MUTED = new Color(139, 157, 180);
    private static final Color CYAN = new Color(70, 214, 236);
    private static final Color GREEN = new Color(111, 227, 165);
    private static final Color VIOLET = new Color(183, 143, 255);
    private static final Font MONO = new Font(Font.MONOSPACED, Font.PLAIN, 13);
    private static final int MAX_TEXT_BYTES = BinaryTernaryQutritTranslator.MAX_INPUT_BITS / 8;

    private final JTextField binaryInput = new JTextField("10101010101010");
    private final JTextArea textInput = new JTextArea(2, 35);
    private final JComboBox<ProcessEntry> processChoices = new JComboBox<ProcessEntry>();
    private final JCheckBox watchSelected = new JCheckBox("Watch selected (1.2 s)");
    private final JLabel processStatus = new JLabel("Process list is local and read-only.");
    private final JLabel translationStatus = new JLabel("Ready.");
    private final MatrixGridPanel binaryGrid = new MatrixGridPanel(MatrixGridPanel.Kind.BINARY);
    private final MatrixGridPanel ternaryGrid = new MatrixGridPanel(MatrixGridPanel.Kind.TERNARY);
    private final MatrixGridPanel qutritGrid = new MatrixGridPanel(MatrixGridPanel.Kind.QUTRIT);

    private final SharedTimer animationTimer;
    private final SharedTimer processSampleTimer;
    private final SharedTimer processRefreshTimer;
    private boolean refreshInFlight;
    private BinaryTernaryQutritTranslator.Translation latest;
    private String latestSource = "Example";

    private LiveTranslationWorkbench() {
        super("Live Binary -> Ternary -> Qutrit Translation Grid");
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(1100, 760));
        setSize(1460, 920);
        setLocationRelativeTo(null);
        getContentPane().setBackground(BG);

        JPanel root = new JPanel(new BorderLayout(12, 12));
        root.setBackground(BG);
        root.setBorder(new EmptyBorder(17, 18, 14, 18));
        setContentPane(root);
        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildGridArea(), BorderLayout.CENTER);
        root.add(buildFooter(), BorderLayout.SOUTH);

        animationTimer = new SharedTimer(90, event -> {
            binaryGrid.advance();
            ternaryGrid.advance();
            qutritGrid.advance();
        });
        processSampleTimer = new SharedTimer(1200, event -> sampleWatchedProcess());
        processRefreshTimer = new SharedTimer(5000, event -> refreshProcesses());
        animationTimer.start();
        processRefreshTimer.start();

        translateBinary();
        refreshProcesses();
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout(0, 10));
        header.setBackground(BG);

        JPanel titleBlock = new JPanel(new BorderLayout(0, 3));
        titleBlock.setBackground(BG);
        JLabel title = new JLabel("Live Translation Grid");
        title.setForeground(TEXT);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 24));
        JLabel sub = new JLabel(
                "One input, three linked representations. The cell values remain exact while the grid pulses.");
        sub.setForeground(MUTED);
        sub.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        titleBlock.add(title, BorderLayout.NORTH);
        titleBlock.add(sub, BorderLayout.SOUTH);
        header.add(titleBlock, BorderLayout.NORTH);

        JPanel sources = new JPanel(new GridLayout(3, 1, 0, 7));
        sources.setBackground(BG);
        sources.add(buildBinaryRow());
        sources.add(buildTextRow());
        sources.add(buildProcessRow());
        header.add(sources, BorderLayout.SOUTH);
        return header;
    }

    private JPanel buildBinaryRow() {
        JPanel row = sourceRow();
        JLabel label = sourceLabel("BINARY");
        binaryInput.setFont(MONO);
        binaryInput.setForeground(TEXT);
        binaryInput.setCaretColor(CYAN);
        binaryInput.setBackground(PANEL_DARK);
        binaryInput.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(47, 67, 89)),
                new EmptyBorder(7, 9, 7, 9)));
        JButton translate = button("Translate bits", CYAN);
        translate.addActionListener(event -> translateBinary());
        binaryInput.addActionListener(event -> translateBinary());
        row.add(label, BorderLayout.WEST);
        row.add(binaryInput, BorderLayout.CENTER);
        row.add(translate, BorderLayout.EAST);
        return row;
    }

    private JPanel buildTextRow() {
        JPanel row = sourceRow();
        JPanel labelBlock = new JPanel(new BorderLayout(0, 3));
        labelBlock.setBackground(PANEL);
        JLabel label = sourceLabel("TEXT -> UTF-8 BITS");
        JLabel hint = new JLabel("Up to 512 bytes");
        hint.setForeground(MUTED);
        hint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labelBlock.add(label, BorderLayout.NORTH);
        labelBlock.add(hint, BorderLayout.SOUTH);

        textInput.setLineWrap(true);
        textInput.setWrapStyleWord(true);
        textInput.setFont(MONO);
        textInput.setForeground(TEXT);
        textInput.setCaretColor(CYAN);
        textInput.setBackground(PANEL_DARK);
        textInput.setBorder(new EmptyBorder(6, 8, 6, 8));
        JScrollPane textScroll = new JScrollPane(textInput);
        textScroll.setBorder(BorderFactory.createLineBorder(new Color(47, 67, 89)));
        JButton translate = button("Encode text", GREEN);
        translate.addActionListener(event -> translateText());

        row.add(labelBlock, BorderLayout.WEST);
        row.add(textScroll, BorderLayout.CENTER);
        row.add(translate, BorderLayout.EAST);
        return row;
    }

    private JPanel buildProcessRow() {
        JPanel row = sourceRow();
        JPanel labelBlock = new JPanel(new BorderLayout(0, 3));
        labelBlock.setBackground(PANEL);
        labelBlock.add(sourceLabel("RUNNING PROCESSES"), BorderLayout.NORTH);
        processStatus.setForeground(MUTED);
        processStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labelBlock.add(processStatus, BorderLayout.SOUTH);

        processChoices.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        processChoices.setBackground(PANEL_DARK);
        processChoices.setForeground(TEXT);
        JButton refresh = button("Refresh", MUTED);
        refresh.addActionListener(event -> refreshProcesses());

        watchSelected.setOpaque(false);
        watchSelected.setForeground(TEXT);
        watchSelected.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        watchSelected.addActionListener(event -> {
            if (watchSelected.isSelected()) {
                if (processChoices.getSelectedItem() == null) {
                    watchSelected.setSelected(false);
                    processStatus.setText("Choose a process first.");
                } else {
                    processSampleTimer.start();
                    sampleWatchedProcess();
                }
            } else {
                processSampleTimer.stop();
                processStatus.setText("Watch stopped.");
            }
        });

        JButton translate = button("Translate selected", VIOLET);
        translate.addActionListener(event -> translateSelectedProcess());

        JPanel actions = new JPanel(new GridLayout(1, 4, 6, 0));
        actions.setBackground(PANEL);
        actions.add(refresh);
        actions.add(watchSelected);
        actions.add(translate);
        row.add(labelBlock, BorderLayout.WEST);
        row.add(processChoices, BorderLayout.CENTER);
        row.add(actions, BorderLayout.EAST);
        return row;
    }

    private JPanel sourceRow() {
        JPanel row = new JPanel(new BorderLayout(9, 0));
        row.setBackground(PANEL);
        row.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(37, 52, 70)),
                new EmptyBorder(8, 10, 8, 10)));
        return row;
    }

    private JLabel sourceLabel(String value) {
        JLabel label = new JLabel(value);
        label.setPreferredSize(new Dimension(145, 28));
        label.setForeground(CYAN);
        label.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        return label;
    }

    private JPanel buildGridArea() {
        JPanel grids = new JPanel(new GridLayout(1, 3, 11, 0));
        grids.setBackground(BG);
        grids.add(stageCard("01  BINARY", "Two symbols: 0 / 1", binaryGrid, CYAN));
        grids.add(stageCard("02  TERNARY", "Three symbols: 0 / 1 / 2", ternaryGrid, GREEN));
        grids.add(stageCard("03  QUTRIT", "Fourier states: |psi0> / |psi1> / |psi2>", qutritGrid, VIOLET));
        return grids;
    }

    private JPanel stageCard(String titleText, String detail, MatrixGridPanel grid, Color accent) {
        JPanel card = new JPanel(new BorderLayout(0, 9));
        card.setBackground(PANEL);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(38, 54, 73)),
                new EmptyBorder(11, 11, 11, 11)));
        JPanel heading = new JPanel(new BorderLayout(0, 4));
        heading.setBackground(PANEL);
        JLabel title = new JLabel(titleText);
        title.setForeground(accent);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 13));
        JLabel subtitle = new JLabel(detail);
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        heading.add(title, BorderLayout.NORTH);
        heading.add(subtitle, BorderLayout.SOUTH);

        JScrollPane scroll = new JScrollPane(grid);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(34, 47, 65)));
        scroll.getViewport().setBackground(PANEL_DARK);
        scroll.getVerticalScrollBar().setUnitIncrement(24);
        card.add(heading, BorderLayout.NORTH);
        card.add(scroll, BorderLayout.CENTER);
        return card;
    }

    private JPanel buildFooter() {
        JPanel footer = new JPanel(new BorderLayout(0, 4));
        footer.setBackground(BG);
        translationStatus.setForeground(TEXT);
        translationStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        JLabel note = new JLabel(
                "Local software model. Process view reads PID, executable name, liveness, and CPU time only; it does not inspect memory or control processes.");
        note.setForeground(MUTED);
        note.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        footer.add(translationStatus, BorderLayout.NORTH);
        footer.add(note, BorderLayout.SOUTH);
        return footer;
    }

    private JButton button(String text, Color color) {
        JButton button = new JButton(text);
        button.setForeground(color);
        button.setBackground(new Color(26, 35, 49));
        button.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        button.setFocusPainted(false);
        button.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(48, 65, 86)),
                new EmptyBorder(7, 10, 7, 10)));
        return button;
    }

    private void translateBinary() {
        runTranslation(binaryInput.getText(), "Binary input");
    }

    private void translateText() {
        String source = textInput.getText();
        byte[] bytes = source.getBytes(StandardCharsets.UTF_8);
        if (bytes.length == 0) {
            showError("Enter some text first.");
            return;
        }
        if (bytes.length > MAX_TEXT_BYTES) {
            showError("Text encodes to " + bytes.length + " UTF-8 bytes; the limit is "
                    + MAX_TEXT_BYTES + " bytes.");
            return;
        }
        runTranslation(bytesToBits(bytes), "Text input (" + bytes.length + " UTF-8 bytes)");
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

    private void translateSelectedProcess() {
        ProcessEntry selected = (ProcessEntry) processChoices.getSelectedItem();
        if (selected == null) {
            showError("No process is selected. Refresh the process list first.");
            return;
        }
        sampleProcess(selected);
    }

    private void sampleWatchedProcess() {
        if (!watchSelected.isSelected()) {
            return;
        }
        ProcessEntry selected = (ProcessEntry) processChoices.getSelectedItem();
        if (selected == null) {
            processSampleTimer.stop();
            watchSelected.setSelected(false);
            processStatus.setText("Selected process is no longer available.");
            return;
        }
        sampleProcess(selected);
    }

    private void sampleProcess(ProcessEntry entry) {
        Optional<ProcessHandle> found;
        try {
            found = ProcessHandle.of(entry.pid);
        } catch (SecurityException error) {
            showError("The operating system denied access to process metadata.");
            return;
        }

        if (!found.isPresent() || !found.get().isAlive()) {
            processStatus.setText("PID " + entry.pid + " has exited.");
            if (watchSelected.isSelected()) {
                watchSelected.setSelected(false);
                processSampleTimer.stop();
            }
            return;
        }

        ProcessHandle process = found.get();
        String currentName = executableName(process, entry.name);
        Optional<Duration> cpu = process.info().totalCpuDuration();
        String cpuText = cpu.isPresent() ? Long.toString(cpu.get().toMillis()) : "unavailable";
        String payload = "PID=" + entry.pid + "\nEXE=" + currentName
                + "\nCPU_MS=" + cpuText + "\nALIVE=true";
        byte[] bytes = payload.getBytes(StandardCharsets.UTF_8);
        processStatus.setText("Sampled metadata only: " + currentName);
        runTranslation(bytesToBits(bytes), "Process metadata (PID " + entry.pid + ")");
    }

    private String executableName(ProcessHandle handle, String fallback) {
        Optional<String> command = handle.info().command();
        if (!command.isPresent() || command.get().length() == 0) {
            return fallback;
        }
        try {
            String name = Paths.get(command.get()).getFileName().toString();
            return name.length() == 0 ? fallback : name;
        } catch (RuntimeException ignored) {
            return fallback;
        }
    }

    private void refreshProcesses() {
        if (refreshInFlight) {
            return;
        }
        refreshInFlight = true;
        processStatus.setText("Refreshing local process list...");
        new SharedSwingWorker<List<ProcessEntry>, Void>() {
            @Override
            protected List<ProcessEntry> doInBackground() {
                List<ProcessEntry> entries = new ArrayList<ProcessEntry>();
                try (Stream<ProcessHandle> processes = ProcessHandle.allProcesses()) {
                    processes.forEach(handle -> {
                        String name = executableName(handle, "process");
                        entries.add(new ProcessEntry(handle.pid(), name));
                    });
                } catch (SecurityException error) {
                    throw error;
                }
                entries.sort(Comparator.comparingLong(entry -> entry.pid));
                return entries;
            }

            @Override
            protected void done() {
                refreshInFlight = false;
                try {
                    List<ProcessEntry> entries = get();
                    ProcessEntry previous = (ProcessEntry) processChoices.getSelectedItem();
                    long previousPid = previous == null ? -1 : previous.pid;
                    processChoices.removeAllItems();
                    ProcessEntry restore = null;
                    for (ProcessEntry entry : entries) {
                        processChoices.addItem(entry);
                        if (entry.pid == previousPid) {
                            restore = entry;
                        }
                    }
                    if (restore != null) {
                        processChoices.setSelectedItem(restore);
                    }
                    processStatus.setText(entries.size() + " processes visible to this user.");
                } catch (Exception error) {
                    processStatus.setText("Unable to read process list: " + safeMessage(error));
                }
            }
        }.execute();
    }

    private String safeMessage(Exception error) {
        Throwable cause = error.getCause() == null ? error : error.getCause();
        String message = cause.getMessage();
        return message == null ? cause.getClass().getSimpleName() : message;
    }

    private void runTranslation(String bits, String source) {
        try {
            latest = BinaryTernaryQutritTranslator.translate(bits);
            latestSource = source;
            BinaryTernaryQutritTranslator.Translation result = latest;
            binaryGrid.setSymbols(result.getBinary(), "binary");
            ternaryGrid.setSymbols(result.getTernary(), "ternary");
            StringBuilder qutritSymbols = new StringBuilder();
            for (BinaryTernaryQutritTranslator.QutritState state : result.getQutritStates()) {
                if (qutritSymbols.length() > 0) {
                    qutritSymbols.append(',');
                }
                qutritSymbols.append(state.getTrit());
            }
            qutritGrid.setSymbols(qutritSymbols.toString(), "qutrit");
            translationStatus.setForeground(TEXT);
            translationStatus.setText(String.format(Locale.ROOT,
                    "%s -> %d bits -> %d ternary digits / qutrits | value %s | "
                            + "%d leading zeroes retained for exact binary round-trip",
                    source, result.getBinary().length(), result.getQutritCount(),
                    result.getValue().toString(), result.getLeadingZeros()));
        } catch (IllegalArgumentException | IllegalStateException error) {
            showError(error.getMessage());
        }
    }

    private void showError(String message) {
        translationStatus.setForeground(new Color(255, 137, 145));
        translationStatus.setText(message);
    }

    private static final class ProcessEntry {
        private final long pid;
        private final String name;

        private ProcessEntry(long pid, String name) {
            this.pid = pid;
            this.name = name;
        }

        @Override
        public String toString() {
            return pid + "  |  " + name;
        }
    }

    private static final class MatrixGridPanel extends JPanel {
        private enum Kind {
            BINARY, TERNARY, QUTRIT
        }

        private final Kind kind;
        private String[] symbols = new String[0];
        private String countLabel = "No data";
        private double phase;

        private MatrixGridPanel(Kind kind) {
            this.kind = kind;
            setBackground(PANEL_DARK);
            setOpaque(true);
            setPreferredSize(new Dimension(410, 460));
        }

        private void setSymbols(String data, String label) {
            if ("qutrit".equals(label)) {
                if (data.length() == 0) {
                    symbols = new String[0];
                } else {
                    String[] trits = data.split(",");
                    symbols = new String[trits.length];
                    for (int i = 0; i < trits.length; i++) {
                        symbols[i] = "|psi" + trits[i] + ">";
                    }
                }
            } else {
                symbols = new String[data.length()];
                for (int i = 0; i < data.length(); i++) {
                    symbols[i] = Character.toString(data.charAt(i));
                }
            }
            countLabel = symbols.length + " symbols";
            int tileWidth = kind == Kind.QUTRIT ? 61 : 34;
            int columns = Math.max(1, (410 - 16) / (tileWidth + 5));
            int rows = (Math.min(symbols.length, 240) + columns - 1) / columns;
            setPreferredSize(new Dimension(410, Math.max(460, 70 + rows * 30)));
            revalidate();
            repaint();
        }

        private void advance() {
            phase += 0.14;
            if (phase > Math.PI * 2.0) {
                phase -= Math.PI * 2.0;
            }
            repaint();
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 11));

            g.setColor(MUTED);
            g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
            g.drawString(countLabel + " | animated intensity, fixed values", 10, 17);

            int visible = Math.min(symbols.length, 240);
            int tileWidth = kind == Kind.QUTRIT ? 61 : 34;
            int tileHeight = 25;
            int gap = 5;
            int availableWidth = Math.max(1, getWidth() - 16);
            int columns = Math.max(1, availableWidth / (tileWidth + gap));
            int actualTileWidth = Math.max(tileWidth, (availableWidth - (columns - 1) * gap) / columns);

            for (int i = 0; i < visible; i++) {
                int row = i / columns;
                int column = i % columns;
                int x = 8 + column * (actualTileWidth + gap);
                int y = 27 + row * (tileHeight + gap);
                int value = symbolValue(symbols[i]);
                double pulse = 0.5 + 0.5 * Math.sin(phase + i * 0.41 + value * 0.73);
                Color base = baseColor(value);
                Color fill = blend(PANEL, base, 0.25 + pulse * 0.48);
                Color edge = blend(base, Color.WHITE, 0.12 + pulse * 0.25);
                g.setColor(fill);
                g.fillRoundRect(x, y, actualTileWidth, tileHeight, 6, 6);
                g.setColor(edge);
                g.drawRoundRect(x, y, actualTileWidth, tileHeight, 6, 6);
                g.setColor(TEXT);
                String symbol = symbols[i];
                int width = g.getFontMetrics().stringWidth(symbol);
                g.drawString(symbol, x + Math.max(3, (actualTileWidth - width) / 2),
                        y + 17);
            }

            if (symbols.length > visible) {
                g.setColor(MUTED);
                g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
                g.drawString("Showing " + visible + " of " + symbols.length
                        + " symbols; scroll or use the summary for full count.",
                        10, getHeight() - 8);
            }
            g.dispose();
        }

        private int symbolValue(String symbol) {
            if (kind == Kind.QUTRIT) {
                int start = symbol.indexOf("psi") + 3;
                if (start >= 3 && start < symbol.length()) {
                    return symbol.charAt(start) - '0';
                }
            }
            return symbol.length() == 0 ? 0 : symbol.charAt(0) - '0';
        }

        private Color baseColor(int value) {
            if (kind == Kind.BINARY) {
                return value == 0 ? new Color(48, 109, 167) : CYAN;
            }
            if (kind == Kind.TERNARY) {
                if (value == 0) return new Color(47, 150, 131);
                if (value == 1) return GREEN;
                return new Color(236, 184, 92);
            }
            if (value == 0) return VIOLET;
            if (value == 1) return new Color(250, 132, 197);
            return new Color(93, 163, 255);
        }

        private Color blend(Color first, Color second, double amount) {
            double t = Math.max(0.0, Math.min(1.0, amount));
            return new Color(
                    (int) (first.getRed() * (1.0 - t) + second.getRed() * t),
                    (int) (first.getGreen() * (1.0 - t) + second.getGreen() * t),
                    (int) (first.getBlue() * (1.0 - t) + second.getBlue() * t));
        }
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
            // The standard Swing look and feel is enough for the workbench.
        }
        SwingUtilities.invokeLater(() -> {
            LiveTranslationWorkbench workbench = new LiveTranslationWorkbench();
            workbench.setVisible(true);
        });
    }
}