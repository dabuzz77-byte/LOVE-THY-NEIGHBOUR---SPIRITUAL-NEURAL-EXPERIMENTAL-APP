package net.activeinference.beacon.translation;
import neural.studio.*;


import com.sun.management.OperatingSystemMXBean;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import neural.studio.SectionFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingUtilities;
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
import java.math.BigInteger;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

/** Six-stage text round-trip across forward and reverse flux grids. */
public final class SixGridKernelFluxWorkbench extends SectionFrame {
    private static final Color BG = new Color(10, 14, 22);
    private static final Color PANEL = new Color(19, 26, 37);
    private static final Color PANEL_DARK = new Color(13, 19, 29);
    private static final Color TEXT = new Color(225, 235, 247);
    private static final Color MUTED = new Color(139, 157, 180);
    private static final Color CYAN = new Color(70, 214, 236);
    private static final Color GREEN = new Color(111, 227, 165);
    private static final Color VIOLET = new Color(183, 143, 255);
    private static final int MAX_TEXT_BYTES = BinaryTernaryQutritTranslator.MAX_INPUT_BITS / 8;
    private static final String RANDOM_ALPHABET = "0123456789ABCDEFGH";
    private static final int RANDOM_STRING_LENGTH = 32;

    private final JTextArea textInput = new JTextArea("ice", 2, 48);
    private final JTextArea randomOutput = new JTextArea(2, 48);
    private final JTextArea finalOutput = new JTextArea(3, 48);
    private final JLabel randomStatus = new JLabel("Random output will be sampled from the upper grids.");
    private final JLabel finalStatus = new JLabel("Enter text and pass it through the six grids.");
    private final JLabel cpuStatus = new JLabel("Waiting for operating system CPU telemetry...");
    private final JLabel flowStatus = new JLabel("Text flow: forward conversion, qutrit mapping, then reverse conversion.");

    private final FluxGridPanel forwardBinary = new FluxGridPanel(FluxGridPanel.Kind.BINARY);
    private final FluxGridPanel forwardTernary = new FluxGridPanel(FluxGridPanel.Kind.TERNARY);
    private final FluxGridPanel forwardQutrit = new FluxGridPanel(FluxGridPanel.Kind.QUTRIT);
    private final FluxGridPanel reverseQutrit = new FluxGridPanel(FluxGridPanel.Kind.QUTRIT);
    private final FluxGridPanel reverseTernary = new FluxGridPanel(FluxGridPanel.Kind.TERNARY);
    private final FluxGridPanel reverseBinary = new FluxGridPanel(FluxGridPanel.Kind.BINARY);
    private final SecureRandom random = new SecureRandom();
    private final SharedTimer animationTimer;
    private final SharedTimer cpuTimer;
    private double fluxRate = 0.15;

    private SixGridKernelFluxWorkbench() {
        super("Six-Grid Kernel Flux Translator");
        setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(1120, 820));
        setSize(1480, 1020);
        setLocationRelativeTo(null);

        JPanel root = new JPanel(new BorderLayout(10, 9));
        root.setBackground(BG);
        root.setBorder(new EmptyBorder(12, 14, 10, 14));
        setContentPane(root);
        root.add(buildTitle(), BorderLayout.NORTH);

        JPanel flow = new JPanel();
        flow.setLayout(new javax.swing.BoxLayout(flow, javax.swing.BoxLayout.Y_AXIS));
        flow.setBackground(BG);
        flow.add(buildTextInputCard());
        flow.add(stageRow("FORWARD FLOW  |  BINARY -> TERNARY -> QUTRIT",
                new String[] {"01  BINARY", "02  TERNARY", "03  QUTRIT"},
                new String[] {"UTF-8 input bits", "Balanced trits: -1 / 0 / +1", "Qutrit basis: |0> / |1> / |2>"},
                new FluxGridPanel[] {forwardBinary, forwardTernary, forwardQutrit},
                new Color[] {CYAN, GREEN, VIOLET}));
        flow.add(buildRandomOutputCard());
        flow.add(stageRow("REVERSE FLOW  |  QUTRIT -> TERNARY -> BINARY",
                new String[] {"04  QUTRIT", "05  TERNARY", "06  BINARY"},
                new String[] {"Decode qutrit basis", "Recover balanced trits", "Recover original UTF-8 bits"},
                new FluxGridPanel[] {reverseQutrit, reverseTernary, reverseBinary},
                new Color[] {VIOLET, GREEN, CYAN}));
        flow.add(buildFinalOutputCard());

        JScrollPane flowScroll = new JScrollPane(flow);
        flowScroll.setBorder(BorderFactory.createEmptyBorder());
        flowScroll.getViewport().setBackground(BG);
        flowScroll.getVerticalScrollBar().setUnitIncrement(28);
        root.add(flowScroll, BorderLayout.CENTER);
        root.add(buildStatusFooter(), BorderLayout.SOUTH);

        animationTimer = new SharedTimer(80, event -> advanceGrids());
        cpuTimer = new SharedTimer(1000, event -> sampleSystemCpu());
        animationTimer.start();
        cpuTimer.start();
        translateText();
    }

    private JPanel buildTitle() {
        JPanel title = new JPanel(new BorderLayout(0, 3));
        title.setBackground(BG);
        JLabel heading = new JLabel("Six-Grid Text Flux");
        heading.setForeground(TEXT);
        heading.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 22));
        JLabel subtitle = new JLabel(
                "Text travels through binary, ternary, and qutrit grids, then returns through the reverse sequence.");
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        title.add(heading, BorderLayout.NORTH);
        title.add(subtitle, BorderLayout.SOUTH);
        return title;
    }

    private JPanel cardPanel() {
        JPanel panel = new JPanel(new BorderLayout(8, 6));
        panel.setBackground(PANEL);
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(37, 52, 70)),
                new EmptyBorder(8, 9, 8, 9)));
        panel.setAlignmentX(LEFT_ALIGNMENT);
        return panel;
    }

    private JLabel sectionTitle(String text, Color color) {
        JLabel label = new JLabel(text);
        label.setForeground(color);
        label.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        return label;
    }

    private void styleTextArea(JTextArea area, boolean editable) {
        area.setEditable(editable);
        area.setLineWrap(true);
        area.setWrapStyleWord(true);
        area.setForeground(TEXT);
        area.setCaretColor(CYAN);
        area.setBackground(PANEL_DARK);
        area.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        area.setBorder(new EmptyBorder(5, 7, 5, 7));
    }

    private JPanel buildTextInputCard() {
        JPanel panel = cardPanel();
        panel.add(sectionTitle("TEXT INPUT  |  UTF-8, UP TO " + MAX_TEXT_BYTES + " BYTES", CYAN),
                BorderLayout.NORTH);
        styleTextArea(textInput, true);
        JScrollPane editor = new JScrollPane(textInput);
        editor.setBorder(BorderFactory.createLineBorder(new Color(47, 67, 89)));
        editor.setPreferredSize(new Dimension(950, 58));
        JButton pass = button("Pass through all six grids", GREEN);
        pass.addActionListener(event -> translateText());
        textInput.setToolTipText("The text is encoded as UTF-8 bytes before entering the first grid.");
        JPanel body = new JPanel(new BorderLayout(8, 0));
        body.setBackground(PANEL);
        body.add(editor, BorderLayout.CENTER);
        body.add(pass, BorderLayout.EAST);
        panel.add(body, BorderLayout.CENTER);
        return panel;
    }

    private JPanel stageRow(String title, String[] names, String[] hints,
                            FluxGridPanel[] grids, Color[] accents) {
        JPanel section = new JPanel(new BorderLayout(0, 6));
        section.setBackground(BG);
        section.setAlignmentX(LEFT_ALIGNMENT);
        section.setBorder(new EmptyBorder(8, 0, 2, 0));
        section.add(sectionTitle(title, CYAN), BorderLayout.NORTH);
        JPanel row = new JPanel(new GridLayout(1, 3, 8, 0));
        row.setBackground(BG);
        for (int i = 0; i < grids.length; i++) {
            row.add(stageCard(names[i], hints[i], grids[i], accents[i]));
        }
        section.add(row, BorderLayout.CENTER);
        section.setPreferredSize(new Dimension(1360, 315));
        return section;
    }

    private JPanel stageCard(String titleText, String hintText,
                             FluxGridPanel grid, Color accent) {
        JPanel card = new JPanel(new BorderLayout(0, 5));
        card.setBackground(PANEL);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(38, 54, 73)),
                new EmptyBorder(6, 7, 6, 7)));
        JLabel title = sectionTitle(titleText, accent);
        JLabel hint = new JLabel(hintText);
        hint.setForeground(MUTED);
        hint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        JPanel heading = new JPanel(new BorderLayout(0, 3));
        heading.setBackground(PANEL);
        heading.add(title, BorderLayout.NORTH);
        heading.add(hint, BorderLayout.SOUTH);
        JScrollPane gridScroll = new JScrollPane(grid);
        gridScroll.setBorder(BorderFactory.createLineBorder(new Color(34, 47, 65)));
        gridScroll.getViewport().setBackground(PANEL_DARK);
        gridScroll.getVerticalScrollBar().setUnitIncrement(24);
        gridScroll.setPreferredSize(new Dimension(410, 250));
        card.add(heading, BorderLayout.NORTH);
        card.add(gridScroll, BorderLayout.CENTER);
        return card;
    }

    private JPanel buildRandomOutputCard() {
        JPanel panel = cardPanel();
        panel.add(sectionTitle("RANDOM STRING FROM THE UPPER THREE GRIDS", VIOLET),
                BorderLayout.NORTH);
        styleTextArea(randomOutput, false);
        randomOutput.setFont(new Font(Font.MONOSPACED, Font.BOLD, 13));
        JScrollPane outputScroll = new JScrollPane(randomOutput);
        outputScroll.setBorder(BorderFactory.createLineBorder(new Color(47, 67, 89)));
        outputScroll.setPreferredSize(new Dimension(850, 48));
        JButton regenerate = button("Sample current grid states", VIOLET);
        regenerate.addActionListener(event -> generateRandomOutput());
        JPanel body = new JPanel(new BorderLayout(8, 0));
        body.setBackground(PANEL);
        body.add(outputScroll, BorderLayout.CENTER);
        body.add(regenerate, BorderLayout.EAST);
        panel.add(body, BorderLayout.CENTER);
        randomStatus.setForeground(MUTED);
        randomStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        panel.add(randomStatus, BorderLayout.SOUTH);
        panel.setPreferredSize(new Dimension(1360, 108));
        return panel;
    }

    private JPanel buildFinalOutputCard() {
        JPanel panel = cardPanel();
        panel.add(sectionTitle("FINAL OUTPUT  |  TEXT RECOVERED AFTER GRID 06", GREEN),
                BorderLayout.NORTH);
        styleTextArea(finalOutput, false);
        JScrollPane outputScroll = new JScrollPane(finalOutput);
        outputScroll.setBorder(BorderFactory.createLineBorder(new Color(47, 67, 89)));
        outputScroll.setPreferredSize(new Dimension(950, 76));
        panel.add(outputScroll, BorderLayout.CENTER);
        finalStatus.setForeground(TEXT);
        finalStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        panel.add(finalStatus, BorderLayout.SOUTH);
        panel.setPreferredSize(new Dimension(1360, 142));
        return panel;
    }

    private JPanel buildStatusFooter() {
        JPanel footer = new JPanel(new GridLayout(2, 1, 0, 2));
        footer.setBackground(BG);
        cpuStatus.setForeground(CYAN);
        cpuStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        flowStatus.setForeground(MUTED);
        flowStatus.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 10));
        footer.add(cpuStatus);
        footer.add(flowStatus);
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

    private void translateText() {
        byte[] inputBytes = textInput.getText().getBytes(StandardCharsets.UTF_8);
        if (inputBytes.length == 0) {
            finalStatus.setText("Enter text before starting the grid flow.");
            return;
        }
        if (inputBytes.length > MAX_TEXT_BYTES) {
            finalStatus.setText("Input is " + inputBytes.length + " UTF-8 bytes; limit is "
                    + MAX_TEXT_BYTES + " bytes.");
            return;
        }

        try {
            String inputBits = bytesToBits(inputBytes);
            BinaryTernaryQutritTranslator.Translation translation =
                    BinaryTernaryQutritTranslator.translate(inputBits);
            int[] upperTrits = toBalancedTernary(translation.getValue());
            int[] upperQutritStates = toQutritStates(upperTrits);

            // Forward flow: text bytes -> binary -> balanced ternary -> qutrit basis.
            forwardBinary.setBinary(inputBits);
            forwardTernary.setBalancedTrits(upperTrits);
            forwardQutrit.setQutritStates(upperQutritStates);
            generateRandomOutput();

            // Reverse flow carries the same payload through qutrit -> trit -> bits.
            reverseQutrit.setQutritStates(upperQutritStates);
            int[] lowerTrits = fromQutritStates(upperQutritStates);
            reverseTernary.setBalancedTrits(lowerTrits);
            BigInteger recoveredValue = fromBalancedTernary(lowerTrits);
            String recoveredBits = toFixedWidthBinary(recoveredValue, inputBits.length());
            reverseBinary.setBinary(recoveredBits);
            byte[] recoveredBytes = bitsToBytes(recoveredBits);

            boolean bitsMatch = inputBits.equals(recoveredBits);
            boolean bytesMatch = Arrays.equals(inputBytes, recoveredBytes);
            String decodedText = new String(recoveredBytes, StandardCharsets.UTF_8);
            finalOutput.setText(decodedText);
            finalStatus.setText(String.format(Locale.ROOT,
                    "%d UTF-8 bytes -> %d bits -> %d trits -> %d qutrits -> %d trits -> %d bits | bit round-trip: %s | byte round-trip: %s",
                    inputBytes.length, inputBits.length(), upperTrits.length,
                    upperQutritStates.length, lowerTrits.length, recoveredBits.length(),
                    bitsMatch ? "exact" : "mismatch", bytesMatch ? "exact" : "mismatch"));
            flowStatus.setText("Payload passed in order through all six grid stages. The animated cells visualize the carried values; the random string samples the upper grids' live states.");
        } catch (IllegalArgumentException | IllegalStateException error) {
            finalStatus.setText(error.getMessage());
        }
    }

    private void generateRandomOutput() {
        if (forwardBinary.nodeCount() == 0 || forwardTernary.nodeCount() == 0
                || forwardQutrit.nodeCount() == 0) {
            randomOutput.setText("");
            randomStatus.setText("Translate text first to seed the upper grids.");
            return;
        }
        StringBuilder result = new StringBuilder(RANDOM_STRING_LENGTH);
        for (int i = 0; i < RANDOM_STRING_LENGTH; i++) {
            int bit = forwardBinary.currentStateAt(random.nextInt(forwardBinary.nodeCount()));
            int tritState = forwardTernary.currentStateAt(
                    random.nextInt(forwardTernary.nodeCount()));
            int qutritState = forwardQutrit.currentStateAt(
                    random.nextInt(forwardQutrit.nodeCount()));
            int symbolIndex = (bit * 3 + tritState) * 3 + qutritState;
            result.append(RANDOM_ALPHABET.charAt(symbolIndex));
        }
        randomOutput.setText(result.toString());
        randomStatus.setText("32 symbols sampled from the upper grids' current animated nodes (base-18 alphabet 0-9, A-H). This side output does not replace the text payload flowing to the lower row.");
    }

    private void advanceGrids() {
        forwardBinary.advance(fluxRate);
        forwardTernary.advance(fluxRate);
        forwardQutrit.advance(fluxRate);
        reverseQutrit.advance(fluxRate);
        reverseTernary.advance(fluxRate);
        reverseBinary.advance(fluxRate);
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
            // CPU telemetry is optional; the grid can keep animating at its base rate.
        }
        fluxRate = load >= 0.0 ? 0.12 + load * 0.72 : 0.20;
        cpuStatus.setText(load >= 0.0
                ? String.format(Locale.ROOT,
                        "OS-reported CPU load: %.1f%% | six-grid flux rate: %.2f | local visualization",
                        load * 100.0, fluxRate)
                : "OS CPU-load value unavailable | using steady grid visualization rate");
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

    private byte[] bitsToBytes(String bits) {
        if ((bits.length() & 7) != 0) {
            throw new IllegalArgumentException("The final binary payload must contain whole bytes.");
        }
        byte[] bytes = new byte[bits.length() / 8];
        for (int i = 0; i < bytes.length; i++) {
            int value = 0;
            for (int j = 0; j < 8; j++) {
                value = (value << 1) | (bits.charAt(i * 8 + j) == '1' ? 1 : 0);
            }
            bytes[i] = (byte) value;
        }
        return bytes;
    }

    private int[] toBalancedTernary(BigInteger value) {
        if (value.signum() == 0) return new int[] {0};
        BigInteger three = BigInteger.valueOf(3L);
        BigInteger remaining = value;
        List<Integer> reversed = new ArrayList<Integer>();
        while (remaining.signum() > 0) {
            BigInteger[] division = remaining.divideAndRemainder(three);
            int digit = division[1].intValue();
            remaining = division[0];
            if (digit == 2) {
                digit = -1;
                remaining = remaining.add(BigInteger.ONE);
            }
            reversed.add(digit);
        }
        int[] digits = new int[reversed.size()];
        for (int i = 0; i < digits.length; i++) {
            digits[i] = reversed.get(digits.length - 1 - i);
        }
        return digits;
    }

    private BigInteger fromBalancedTernary(int[] digits) {
        BigInteger value = BigInteger.ZERO;
        BigInteger three = BigInteger.valueOf(3L);
        for (int digit : digits) {
            if (digit < -1 || digit > 1) {
                throw new IllegalArgumentException("Balanced ternary digits must be -1, 0, or +1.");
            }
            value = value.multiply(three).add(BigInteger.valueOf(digit));
        }
        if (value.signum() < 0) {
            throw new IllegalStateException("The recovered unsigned text payload became negative.");
        }
        return value;
    }

    private int[] toQutritStates(int[] trits) {
        int[] states = new int[trits.length];
        for (int i = 0; i < trits.length; i++) {
            if (trits[i] < -1 || trits[i] > 1) {
                throw new IllegalArgumentException("Balanced ternary digits must be -1, 0, or +1.");
            }
            states[i] = trits[i] + 1;
        }
        return states;
    }

    private int[] fromQutritStates(int[] states) {
        int[] trits = new int[states.length];
        for (int i = 0; i < states.length; i++) {
            if (states[i] < 0 || states[i] > 2) {
                throw new IllegalArgumentException("Qutrit basis indexes must be 0, 1, or 2.");
            }
            trits[i] = states[i] - 1;
        }
        return trits;
    }

    private String toFixedWidthBinary(BigInteger value, int width) {
        if (width < 1 || width > BinaryTernaryQutritTranslator.MAX_INPUT_BITS) {
            throw new IllegalArgumentException("The recovered binary width is outside the supported range.");
        }
        String bits = value.toString(2);
        if (bits.length() > width) {
            throw new IllegalArgumentException("The reverse-flow value does not fit the original bit width.");
        }
        StringBuilder padded = new StringBuilder(width);
        for (int i = bits.length(); i < width; i++) padded.append('0');
        padded.append(bits);
        return padded.toString();
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
        }

        private void setBinary(String bits) {
            seeds = new int[bits.length()];
            for (int i = 0; i < bits.length(); i++) {
                if (bits.charAt(i) != '0' && bits.charAt(i) != '1') {
                    throw new IllegalArgumentException("Binary grid input may contain only 0 and 1.");
                }
                seeds[i] = bits.charAt(i) - '0';
            }
            reset();
        }

        private void setBalancedTrits(int[] digits) {
            seeds = new int[digits.length];
            for (int i = 0; i < digits.length; i++) {
                if (digits[i] < -1 || digits[i] > 1) {
                    throw new IllegalArgumentException("Balanced trits must be -1, 0, or +1.");
                }
                seeds[i] = digits[i] + 1;
            }
            reset();
        }

        private void setQutritStates(int[] states) {
            seeds = new int[states.length];
            for (int i = 0; i < states.length; i++) {
                if (states[i] < 0 || states[i] > 2) {
                    throw new IllegalArgumentException("Qutrit basis states must be 0, 1, or 2.");
                }
                seeds[i] = states[i];
            }
            reset();
        }

        private int nodeCount() {
            return seeds.length;
        }

        private int currentStateAt(int index) {
            if (index < 0 || index >= seeds.length) {
                throw new IndexOutOfBoundsException("Grid node index is outside the grid.");
            }
            int stateCount = kind == Kind.BINARY ? 2 : 3;
            double nodeRate = 0.60 + (index % 9) * 0.045;
            int advance = (int) Math.floor(phase * nodeRate);
            return Math.floorMod(seeds[index] + advance, stateCount);
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
            return new Dimension(420, Math.max(260, 34 + rows * 28));
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
                    int state = currentStateAt(i);
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
            SixGridKernelFluxWorkbench app = new SixGridKernelFluxWorkbench();
            app.setVisible(true);
        });
    }
}
