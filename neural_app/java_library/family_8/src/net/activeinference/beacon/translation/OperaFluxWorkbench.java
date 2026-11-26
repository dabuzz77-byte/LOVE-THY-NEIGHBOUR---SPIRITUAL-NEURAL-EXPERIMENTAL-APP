package net.activeinference.beacon.translation;
import neural.studio.*;


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
import java.awt.RenderingHints;
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
 * Local translation visualizer with read-only Opera process metadata sampling.
 * No process memory is opened or modified.
 */
public final class OperaFluxWorkbench extends SectionFrame {
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
    private final JTextArea textInput = new JTextArea(2, 30);
    private final JComboBox<OperaEntry> operaChoices = new JComboBox<OperaEntry>();
    private final JCheckBox watchOpera = new JCheckBox("Watch selected Opera");
    private final JLabel operaStatus = new JLabel("Looking for visible opera.exe processes...");
    private final JLabel translationStatus = new JLabel("Ready.");
    private final FluxGridPanel binaryGrid = new FluxGridPanel(FluxGridPanel.Kind.BINARY);
    private final FluxGridPanel balancedGrid = new FluxGridPanel(FluxGridPanel.Kind.BALANCED);
    private final FluxGridPanel qutritGrid = new FluxGridPanel(FluxGridPanel.Kind.QUTRIT);

    private final SharedTimer animationTimer;
    private final SharedTimer sampleTimer;
    private final SharedTimer refreshTimer;
    private boolean refreshInFlight;
    private long priorCpuMillis = -1L;

    private OperaFluxWorkbench() {
        super("Opera Read-Only Flux Translation Grid");
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(1100, 740));
        setSize(1450, 900);
        setLocationRelativeTo(null);
        getContentPane().setBackground(BG);

        JPanel root = new JPanel(new BorderLayout(12, 12));
        root.setBackground(BG);
        root.setBorder(new EmptyBorder(16, 18, 14, 18));
        setContentPane(root);
        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildGrids(), BorderLayout.CENTER);
        root.add(buildFooter(), BorderLayout.SOUTH);

        animationTimer = new SharedTimer(80, event -> {
            double fluxRate = currentFluxRate();
            binaryGrid.advance(fluxRate);
            balancedGrid.advance(fluxRate);
            qutritGrid.advance(fluxRate);
        });
        sampleTimer = new SharedTimer(1200, event -> sampleSelectedOpera());
        refreshTimer = new SharedTimer(4000, event -> refreshOperaProcesses());
        animationTimer.start();
        refreshTimer.start();

        translateBinary();
        refreshOperaProcesses();
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout(0, 10));
        header.setBackground(BG);

        JPanel titleBlock = new JPanel(new BorderLayout(0, 3));
        titleBlock.setBackground(BG);
        JLabel title = new JLabel("Binary / Balanced Ternary / Qutrit Flux");
        title.setForeground(TEXT);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 24));
        JLabel subtitle = new JLabel(
                "Input values seed each grid. Nodes cycle through valid states; observed Opera CPU activity adjusts the animation rate.");
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        titleBlock.add(title, BorderLayout.NORTH);
        titleBlock.add(subtitle, BorderLayout.SOUTH);
        header.add(titleBlock, BorderLayout.NORTH);

        JPanel inputs = new JPanel(new GridLayout(3, 1, 0, 7));
        inputs.setBackground(BG);
        inputs.add(buildBinaryRow());
        inputs.add(buildTextRow());
        inputs.add(buildOperaRow());
        header.add(inputs, BorderLayout.SOUTH);
        return header;
    }

    private JPanel sourceRow() {
        JPanel panel = new JPanel(new BorderLayout(9, 0));
        panel.setBackground(PANEL);
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(37, 52, 70)),
                new EmptyBorder(8, 10, 8, 10)));
        return panel;
    }

    private JLabel label(String text) {
        JLabel label = new JLabel(text);
        label.setPreferredSize(new Dimension(150, 28));
        label.setForeground(CYAN);
        label.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        return label;
    }

    private JPanel buildBinaryRow() {
        JPanel row = sourceRow();
        binaryInput.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        binaryInput.setForeground(TEXT);
        binaryInput.setCaretColor(CYAN);
        binaryInput.setBackground(PANEL_DARK);
        binaryInput.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(47, 67, 89)),
                new EmptyBorder(7, 9, 7, 9)));
        JButton run = button("Translate bits", CYAN);
        run.addActionListener(event -> translateBinary());
        binaryInput.addActionListener(event -> translateBinary());
        row.add(label("BINARY INPUT"), BorderLayout.WEST);
        row.add(binaryInput, BorderLayout.CENTER);
        row.add(run, BorderLayout.EAST);
        return row;
    }

    private JPanel buildTextRow() {
        JPanel row = sourceRow();
        JPanel labelBlock = new JPanel(new BorderLayout(0, 3));
        labelBlock.setBackground(PANEL);
        labelBlock.add(label("TEXT -> UTF-8 BITS"), BorderLayout.NORTH);
        JLabel hint = new JLabel("Up to 512 UTF-8 bytes");
        hint.setForeground(MUTED);
        hint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labelBlock.add(hint, BorderLayout.SOUTH);

        textInput.setLineWrap(true);
        textInput.setWrapStyleWord(true);
        textInput.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        textInput.setForeground(TEXT);
        textInput.setCaretColor(CYAN);
        textInput.setBackground(PANEL_DARK);
        textInput.setBorder(new EmptyBorder(6, 8, 6, 8));
        JScrollPane scroll = new JScrollPane(textInput);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(47, 67, 89)));

        JButton run = button("Encode and flux", GREEN);
        run.addActionListener(event -> translateText());
        row.add(labelBlock, BorderLayout.WEST);
        row.add(scroll, BorderLayout.CENTER);
        row.add(run, BorderLayout.EAST);
        return row;
    }

    private JPanel buildOperaRow() {
        JPanel row = sourceRow();
        JPanel labelBlock = new JPanel(new BorderLayout(0, 3));
        labelBlock.setBackground(PANEL);
        labelBlock.add(label("OPERA PROCESS"), BorderLayout.NORTH);
        operaStatus.setForeground(MUTED);
        operaStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        labelBlock.add(operaStatus, BorderLayout.SOUTH);

        operaChoices.setBackground(PANEL_DARK);
        operaChoices.setForeground(TEXT);
        JButton refresh = button("Refresh", MUTED);
        refresh.addActionListener(event -> refreshOperaProcesses());

        watchOpera.setOpaque(false);
        watchOpera.setForeground(TEXT);
        watchOpera.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        watchOpera.addActionListener(event -> {
            if (watchOpera.isSelected()) {
                if (operaChoices.getSelectedItem() == null) {
                    watchOpera.setSelected(false);
                    operaStatus.setText("No visible Opera process selected.");
                } else {
                    priorCpuMillis = -1L;
                    sampleTimer.start();
                    sampleSelectedOpera();
                }
            } else {
                sampleTimer.stop();
                priorCpuMillis = -1L;
                operaStatus.setText("Opera watch stopped.");
            }
        });

        JButton pass = button("Pass process metadata", VIOLET);
        pass.addActionListener(event -> sampleSelectedOpera());

        JPanel actions = new JPanel(new GridLayout(1, 3, 6, 0));
        actions.setBackground(PANEL);
        actions.add(refresh);
        actions.add(watchOpera);
        actions.add(pass);
        row.add(labelBlock, BorderLayout.WEST);
        row.add(operaChoices, BorderLayout.CENTER);
        row.add(actions, BorderLayout.EAST);
        return row;
    }

    private JPanel buildGrids() {
        JPanel grids = new JPanel(new GridLayout(1, 3, 11, 0));
        grids.setBackground(BG);
        grids.add(stageCard("01  BINARY", "0 / 1 | source bit string", binaryGrid, CYAN));
        grids.add(stageCard("02  BALANCED TERNARY", "-1 / 0 / +1 | exact signed base-3", balancedGrid, GREEN));
        grids.add(stageCard("03  QUTRIT", "|0> / |1> / |2> | simulated X3 state cycle", qutritGrid, VIOLET));
        return grids;
    }

    private JPanel stageCard(String titleText, String hintText, FluxGridPanel grid, Color accent) {
        JPanel card = new JPanel(new BorderLayout(0, 8));
        card.setBackground(PANEL);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(38, 54, 73)),
                new EmptyBorder(10, 10, 10, 10)));
        JPanel heading = new JPanel(new BorderLayout(0, 4));
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
        JPanel footer = new JPanel(new BorderLayout(0, 4));
        footer.setBackground(BG);
        translationStatus.setForeground(TEXT);
        translationStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        JLabel note = new JLabel(
                "Opera access is read-only (PID, executable name, liveness, CPU time). Grid flux is a visualization, not a stream of Opera memory bits or quantum hardware.");
        note.setForeground(MUTED);
        note.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        footer.add(translationStatus, BorderLayout.NORTH);
        footer.add(note, BorderLayout.SOUTH);
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
                new EmptyBorder(7, 10, 7, 10)));
        return button;
    }

    private void translateBinary() {
        passThrough(binaryInput.getText(), "Binary input");
    }

    private void translateText() {
        byte[] bytes = textInput.getText().getBytes(StandardCharsets.UTF_8);
        if (bytes.length == 0) {
            showError("Enter text before translating.");
            return;
        }
        if (bytes.length > MAX_TEXT_BYTES) {
            showError("Text is " + bytes.length + " UTF-8 bytes; limit is " + MAX_TEXT_BYTES + ".");
            return;
        }
        passThrough(bytesToBits(bytes), "Text (" + bytes.length + " UTF-8 bytes)");
    }

    private void passThrough(String bits, String source) {
        try {
            BinaryTernaryQutritTranslator.Translation result =
                    BinaryTernaryQutritTranslator.translate(bits);
            int[] balancedDigits = toBalancedTernary(result.getValue());
            binaryGrid.setSeedsFromBits(result.getBinary());
            balancedGrid.setBalancedSeeds(balancedDigits);
            qutritGrid.setQutritSeeds(balancedDigits);

            int previewCount = Math.min(24, balancedDigits.length);
            StringBuilder balancedPreview = new StringBuilder();
            for (int i = 0; i < previewCount; i++) {
                if (i > 0) balancedPreview.append(' ');
                int digit = balancedDigits[i];
                balancedPreview.append(digit > 0 ? "+1" : Integer.toString(digit));
            }
            String ellipsis = balancedDigits.length > previewCount ? " ..." : "";
            showStatus(String.format(Locale.ROOT,
                    "%s | %d bits -> value %s -> balanced ternary [%s%s] (%d digits) -> %d qutrit nodes | exact numeric conversion",
                    source, result.getBinary().length(), result.getValue().toString(),
                    balancedPreview.toString(), ellipsis, balancedDigits.length, balancedDigits.length));
        } catch (IllegalArgumentException | IllegalStateException error) {
            showError(error.getMessage());
        }
    }

    private int[] toBalancedTernary(java.math.BigInteger value) {
        if (value.signum() == 0) {
            return new int[] {0};
        }
        List<Integer> reversed = new ArrayList<Integer>();
        java.math.BigInteger three = java.math.BigInteger.valueOf(3);
        java.math.BigInteger remaining = value;
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

    private void translateSelectedOpera() {
        sampleSelectedOpera();
    }

    private void sampleSelectedOpera() {
        OperaEntry selected = (OperaEntry) operaChoices.getSelectedItem();
        if (selected == null) {
            showError("No visible opera.exe process is selected.");
            return;
        }

        Optional<ProcessHandle> maybeProcess;
        try {
            maybeProcess = ProcessHandle.of(selected.pid);
        } catch (SecurityException error) {
            showError("The operating system denied access to process metadata.");
            return;
        }

        if (!maybeProcess.isPresent() || !maybeProcess.get().isAlive()) {
            operaStatus.setText("Opera PID " + selected.pid + " has exited.");
            if (watchOpera.isSelected()) {
                watchOpera.setSelected(false);
                sampleTimer.stop();
            }
            return;
        }

        ProcessHandle process = maybeProcess.get();
        Optional<Duration> cpu;
        try {
            cpu = process.info().totalCpuDuration();
        } catch (SecurityException error) {
            cpu = Optional.empty();
        }
        long cpuMillis = cpu.isPresent() ? cpu.get().toMillis() : -1L;
        long delta = priorCpuMillis < 0L || cpuMillis < 0L ? 0L
                : Math.max(0L, cpuMillis - priorCpuMillis);
        priorCpuMillis = cpuMillis;

        String payload = "OPERA_PID=" + selected.pid
                + "\nEXE=opera.exe\nALIVE=true\nCPU_TOTAL_MS="
                + (cpuMillis < 0L ? "unavailable" : Long.toString(cpuMillis))
                + "\nCPU_DELTA_MS=" + (cpuMillis < 0L ? "unavailable" : Long.toString(delta));
        byte[] bytes = payload.getBytes(StandardCharsets.UTF_8);
        operaStatus.setText(cpuMillis < 0L
                ? "PID " + selected.pid + " | CPU time unavailable"
                : "PID " + selected.pid + " | CPU +" + delta + " ms / sample");
        passThrough(bytesToBits(bytes), "Opera metadata (PID " + selected.pid + ")");
    }

    private double currentFluxRate() {
        String text = operaStatus.getText();
        int marker = text.indexOf("CPU +");
        if (marker < 0) {
            return 0.8;
        }
        int start = marker + 5;
        int end = text.indexOf(" ms", start);
        if (end < 0) {
            return 0.8;
        }
        try {
            double cpuDelta = Double.parseDouble(text.substring(start, end));
            return Math.max(0.35, Math.min(4.0, 0.35 + cpuDelta / 80.0));
        } catch (NumberFormatException ignored) {
            return 0.8;
        }
    }

    private void refreshOperaProcesses() {
        if (refreshInFlight) return;
        refreshInFlight = true;
        operaStatus.setText("Searching visible processes for opera.exe...");
        new SharedSwingWorker<List<OperaEntry>, Void>() {
            @Override
            protected List<OperaEntry> doInBackground() {
                List<OperaEntry> matches = new ArrayList<OperaEntry>();
                try (Stream<ProcessHandle> processes = ProcessHandle.allProcesses()) {
                    processes.forEach(process -> {
                        String name = executableName(process);
                        if ("opera.exe".equalsIgnoreCase(name)) {
                            matches.add(new OperaEntry(process.pid()));
                        }
                    });
                }
                matches.sort(Comparator.comparingLong(entry -> entry.pid));
                return matches;
            }

            @Override
            protected void done() {
                refreshInFlight = false;
                try {
                    List<OperaEntry> matches = get();
                    OperaEntry previous = (OperaEntry) operaChoices.getSelectedItem();
                    long previousPid = previous == null ? -1L : previous.pid;
                    operaChoices.removeAllItems();
                    OperaEntry restore = null;
                    for (OperaEntry entry : matches) {
                        operaChoices.addItem(entry);
                        if (entry.pid == previousPid) restore = entry;
                    }
                    if (restore != null) operaChoices.setSelectedItem(restore);
                    if (matches.isEmpty()) {
                        operaStatus.setText("No visible opera.exe process found.");
                        if (watchOpera.isSelected()) {
                            watchOpera.setSelected(false);
                            sampleTimer.stop();
                        }
                    } else {
                        operaStatus.setText(matches.size() + " visible Opera process(es).");
                    }
                } catch (Exception error) {
                    Throwable cause = error.getCause() == null ? error : error.getCause();
                    String message = cause.getMessage();
                    operaStatus.setText("Process list unavailable: "
                            + (message == null ? cause.getClass().getSimpleName() : message));
                }
            }
        }.execute();
    }

    private String executableName(ProcessHandle process) {
        try {
            Optional<String> command = process.info().command();
            if (!command.isPresent() || command.get().length() == 0) return "";
            return Paths.get(command.get()).getFileName().toString();
        } catch (RuntimeException ignored) {
            return "";
        }
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

    private void showStatus(String message) {
        translationStatus.setForeground(TEXT);
        translationStatus.setText(message);
    }

    private void showError(String message) {
        translationStatus.setForeground(new Color(255, 137, 145));
        translationStatus.setText(message);
    }

    private static final class OperaEntry {
        private final long pid;

        private OperaEntry(long pid) {
            this.pid = pid;
        }

        @Override
        public String toString() {
            return "PID " + pid + " | opera.exe";
        }
    }

    private static final class FluxGridPanel extends JPanel {
        private enum Kind { BINARY, BALANCED, QUTRIT }

        private final Kind kind;
        private int[] seeds = new int[0];
        private double phase;
        private double rate = 0.8;

        private FluxGridPanel(Kind kind) {
            this.kind = kind;
            setBackground(PANEL_DARK);
            setOpaque(true);
            setPreferredSize(new Dimension(410, 480));
        }

        private void setSeedsFromBits(String bits) {
            seeds = new int[bits.length()];
            for (int i = 0; i < bits.length(); i++) {
                seeds[i] = bits.charAt(i) - '0';
            }
            reset();
        }

        private void setBalancedSeeds(int[] digits) {
            seeds = new int[digits.length];
            for (int i = 0; i < digits.length; i++) {
                seeds[i] = digits[i] + 1;
            }
            reset();
        }

        private void setQutritSeeds(int[] digits) {
            seeds = new int[digits.length];
            for (int i = 0; i < digits.length; i++) {
                seeds[i] = digits[i] + 1;
            }
            reset();
        }

        private void reset() {
            phase = 0.0;
            revalidate();
            repaint();
        }

        private void advance(double fluxRate) {
            rate = fluxRate;
            phase = (phase + rate) % 10000.0;
            repaint();
        }

        @Override
        public Dimension getPreferredSize() {
            int count = Math.min(seeds.length, 240);
            int tileWidth = kind == Kind.QUTRIT ? 56 : 42;
            int columns = Math.max(1, (410 - 16) / (tileWidth + 5));
            int rows = (count + columns - 1) / columns;
            return new Dimension(410, Math.max(480, 56 + rows * 34));
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g = (Graphics2D) graphics.create();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
            g.setColor(MUTED);
            String title = kind == Kind.BINARY ? "binary nodes | 0 <-> 1"
                    : kind == Kind.BALANCED ? "balanced trits | -1 <-> 0 <-> +1"
                    : "qutrit basis |0> <-> |1> <-> |2>";
            g.drawString(title + " | flux x" + String.format(Locale.ROOT, "%.2f", rate), 10, 17);

            int tileWidth = kind == Kind.QUTRIT ? 56 : 42;
            int tileHeight = 26;
            int gap = 5;
            int availableWidth = Math.max(1, getWidth() - 16);
            int columns = Math.max(1, availableWidth / (tileWidth + gap));
            int actualWidth = Math.max(tileWidth, (availableWidth - (columns - 1) * gap) / columns);
            int visible = Math.min(seeds.length, 240);

            for (int i = 0; i < visible; i++) {
                int x = 8 + (i % columns) * (actualWidth + gap);
                int y = 27 + (i / columns) * (tileHeight + gap);
                int cycle = (int) Math.floor(phase * (0.55 + (i % 7) * 0.11));
                int states = kind == Kind.BINARY ? 2 : 3;
                int state = Math.floorMod(seeds[i] + cycle, states);
                Color base = cellColor(state);
                double pulse = 0.5 + 0.5 * Math.sin(phase + i * 0.51);
                g.setColor(blend(PANEL, base, 0.25 + pulse * 0.50));
                g.fillRoundRect(x, y, actualWidth, tileHeight, 6, 6);
                g.setColor(blend(base, Color.WHITE, 0.15 + pulse * 0.25));
                g.drawRoundRect(x, y, actualWidth, tileHeight, 6, 6);
                g.setColor(TEXT);
                g.setFont(new Font(Font.MONOSPACED, Font.BOLD, 11));
                String symbol = symbolFor(state);
                int symbolWidth = g.getFontMetrics().stringWidth(symbol);
                g.drawString(symbol, x + Math.max(3, (actualWidth - symbolWidth) / 2), y + 17);
            }

            if (seeds.length > visible) {
                g.setColor(MUTED);
                g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
                g.drawString("Showing " + visible + " of " + seeds.length + " nodes.",
                        10, getHeight() - 8);
            }
            g.dispose();
        }

        private String symbolFor(int state) {
            if (kind == Kind.BINARY) return state == 0 ? "0" : "1";
            if (kind == Kind.BALANCED) return state == 0 ? "-1" : state == 1 ? "0" : "+1";
            return state == 0 ? "|0>" : state == 1 ? "|1>" : "|2>";
        }

        private Color cellColor(int state) {
            if (kind == Kind.BINARY) return state == 0 ? new Color(57, 117, 177) : CYAN;
            if (kind == Kind.BALANCED) {
                return state == 0 ? new Color(238, 157, 98)
                        : state == 1 ? GREEN : new Color(84, 193, 164);
            }
            return state == 0 ? VIOLET : state == 1
                    ? new Color(241, 131, 196) : new Color(93, 163, 255);
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
            // Swing's default look and feel is sufficient.
        }
        SwingUtilities.invokeLater(() -> {
            OperaFluxWorkbench app = new OperaFluxWorkbench();
            app.setVisible(true);
        });
    }
}