package net.activeinference.beacon.translation;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;
import javax.swing.border.EmptyBorder;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridLayout;
import java.awt.Toolkit;
import java.awt.datatransfer.StringSelection;
import java.util.List;
import java.util.Locale;

/** Standalone, local-only UI for the binary -> ternary -> qutrit translator. */
public final class TranslationWorkbench extends JFrame {
    private static final Color BACKGROUND = new Color(13, 17, 25);
    private static final Color PANEL = new Color(22, 28, 39);
    private static final Color PANEL_DARK = new Color(16, 21, 31);
    private static final Color TEXT = new Color(226, 234, 245);
    private static final Color MUTED = new Color(145, 159, 180);
    private static final Color CYAN = new Color(82, 213, 226);
    private static final Color GREEN = new Color(123, 225, 169);
    private static final Color VIOLET = new Color(185, 151, 255);
    private static final Font MONO = new Font(Font.MONOSPACED, Font.PLAIN, 13);

    private final JTextField input = new JTextField("10101010101010");
    private final JTextArea binaryOutput = createOutputArea();
    private final JTextArea ternaryOutput = createOutputArea();
    private final JTextArea qutritOutput = createOutputArea();
    private final JLabel summary = new JLabel("Ready. Enter binary digits and select Translate.");
    private BinaryTernaryQutritTranslator.Translation lastTranslation;

    private TranslationWorkbench() {
        super("Binary -> Ternary -> Qutrit | Translation Workbench");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(1000, 680));
        setSize(1320, 820);
        setLocationRelativeTo(null);
        getContentPane().setBackground(BACKGROUND);
        setLayout(new BorderLayout(14, 14));

        JPanel root = new JPanel(new BorderLayout(12, 12));
        root.setBackground(BACKGROUND);
        root.setBorder(new EmptyBorder(18, 18, 16, 18));
        setContentPane(root);

        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildStages(), BorderLayout.CENTER);
        root.add(buildFooter(), BorderLayout.SOUTH);

        translateInput();
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout(0, 12));
        header.setBackground(BACKGROUND);

        JPanel titleBlock = new JPanel(new BorderLayout(0, 4));
        titleBlock.setBackground(BACKGROUND);
        JLabel title = new JLabel("Representation Translator");
        title.setForeground(TEXT);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 25));

        JLabel subtitle = new JLabel(
                "Deterministic integer conversion, followed by a normalized three-level state encoding.");
        subtitle.setForeground(MUTED);
        subtitle.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 13));
        titleBlock.add(title, BorderLayout.NORTH);
        titleBlock.add(subtitle, BorderLayout.SOUTH);
        header.add(titleBlock, BorderLayout.NORTH);

        JPanel entry = new JPanel(new BorderLayout(9, 0));
        entry.setBackground(PANEL);
        entry.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(43, 57, 75)),
                new EmptyBorder(12, 13, 12, 13)));

        JPanel prompt = new JPanel(new BorderLayout(0, 4));
        prompt.setBackground(PANEL);
        JLabel promptTitle = new JLabel("BINARY INPUT");
        promptTitle.setForeground(CYAN);
        promptTitle.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 11));
        JLabel promptHint = new JLabel("0 / 1 only | spaces and _ are allowed | up to 4096 bits");
        promptHint.setForeground(MUTED);
        promptHint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        prompt.add(promptTitle, BorderLayout.NORTH);
        prompt.add(promptHint, BorderLayout.SOUTH);

        input.setFont(MONO);
        input.setForeground(TEXT);
        input.setCaretColor(CYAN);
        input.setBackground(PANEL_DARK);
        input.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(53, 72, 93)),
                new EmptyBorder(9, 10, 9, 10)));

        JButton translate = makeButton("Translate", CYAN, new Color(12, 42, 51));
        translate.addActionListener(event -> translateInput());
        input.addActionListener(event -> translateInput());

        JButton copy = makeButton("Copy report", GREEN, new Color(18, 44, 35));
        copy.addActionListener(event -> copyReport());

        JButton clear = makeButton("Clear", MUTED, new Color(36, 42, 52));
        clear.addActionListener(event -> clearAll());

        JPanel actions = new JPanel(new GridLayout(1, 3, 7, 0));
        actions.setBackground(PANEL);
        actions.add(translate);
        actions.add(copy);
        actions.add(clear);

        JPanel inputAndActions = new JPanel(new BorderLayout(9, 0));
        inputAndActions.setBackground(PANEL);
        inputAndActions.add(input, BorderLayout.CENTER);
        inputAndActions.add(actions, BorderLayout.EAST);

        entry.add(prompt, BorderLayout.NORTH);
        entry.add(inputAndActions, BorderLayout.CENTER);
        header.add(entry, BorderLayout.SOUTH);
        return header;
    }

    private JPanel buildStages() {
        JPanel stages = new JPanel(new GridLayout(1, 3, 12, 0));
        stages.setBackground(BACKGROUND);
        stages.add(createStageCard("01  BINARY", "Unsigned integer | input width retained",
                binaryOutput, CYAN));
        stages.add(createStageCard("02  TERNARY", "Exact base-3 expansion | leading zeroes removed",
                ternaryOutput, GREEN));
        stages.add(createStageCard("03  QUTRIT REGISTER", "One normalized 3-level state per ternary digit",
                qutritOutput, VIOLET));
        return stages;
    }

    private JPanel createStageCard(String titleText, String description, JTextArea output, Color accent) {
        JPanel card = new JPanel(new BorderLayout(0, 9));
        card.setBackground(PANEL);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(43, 57, 75)),
                new EmptyBorder(12, 12, 12, 12)));

        JPanel heading = new JPanel(new BorderLayout(0, 4));
        heading.setBackground(PANEL);
        JLabel title = new JLabel(titleText);
        title.setForeground(accent);
        title.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 13));
        JLabel hint = new JLabel(description);
        hint.setForeground(MUTED);
        hint.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        heading.add(title, BorderLayout.NORTH);
        heading.add(hint, BorderLayout.SOUTH);

        JScrollPane scroll = new JScrollPane(output);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(39, 51, 67)));
        scroll.getViewport().setBackground(PANEL_DARK);
        card.add(heading, BorderLayout.NORTH);
        card.add(scroll, BorderLayout.CENTER);
        return card;
    }

    private JPanel buildFooter() {
        JPanel footer = new JPanel(new BorderLayout(0, 8));
        footer.setBackground(BACKGROUND);
        summary.setForeground(TEXT);
        summary.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));

        JTextArea explanation = new JTextArea(
                "Qutrit map: |psi_k> = 1/sqrt(3) sum_j omega^(k*j)|j>, where omega = exp(2*pi*i/3). "
                + "This is a classical calculation of a qutrit state vector; no quantum hardware is used.");
        explanation.setEditable(false);
        explanation.setFocusable(false);
        explanation.setLineWrap(true);
        explanation.setWrapStyleWord(true);
        explanation.setRows(2);
        explanation.setForeground(MUTED);
        explanation.setBackground(BACKGROUND);
        explanation.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 11));
        explanation.setBorder(new EmptyBorder(0, 0, 0, 0));

        footer.add(summary, BorderLayout.NORTH);
        footer.add(explanation, BorderLayout.CENTER);
        return footer;
    }

    private void translateInput() {
        try {
            lastTranslation = BinaryTernaryQutritTranslator.translate(input.getText());
            BinaryTernaryQutritTranslator.Translation result = lastTranslation;
            binaryOutput.setForeground(CYAN);
            ternaryOutput.setForeground(GREEN);
            qutritOutput.setForeground(VIOLET);
            binaryOutput.setText(group(result.getBinary(), 4));
            ternaryOutput.setText(group(result.getTernary(), 5));
            qutritOutput.setText(formatQutrits(result.getQutritStates()));

            summary.setForeground(TEXT);
            summary.setText(String.format(Locale.ROOT,
                    "Value: %s   |   %d input bits (%d leading zeroes)   |   %d ternary digits / qutrits"
                            + "   |   state norm ~= 1   |   width-aware round-trip: exact",
                    result.getValue().toString(), result.getBinary().length(),
                    result.getLeadingZeros(), result.getQutritCount()));
        } catch (IllegalArgumentException | IllegalStateException error) {
            lastTranslation = null;
            binaryOutput.setText("");
            ternaryOutput.setText("");
            qutritOutput.setText("");
            summary.setForeground(new Color(255, 139, 139));
            summary.setText(error.getMessage());
        }
    }

    private String formatQutrits(List<BinaryTernaryQutritTranslator.QutritState> states) {
        StringBuilder text = new StringBuilder();
        text.append("digit k -> (a0, a1, a2) ; P(0,1,2)\n");
        text.append("---------------------------------------------------------------\n");
        for (BinaryTernaryQutritTranslator.QutritState state : states) {
            text.append(String.format(Locale.ROOT, "q%-5d k=%d  ", state.getIndex() + 1, state.getTrit()));
            text.append('(');
            for (int basis = 0; basis < 3; basis++) {
                if (basis > 0) {
                    text.append(", ");
                }
                text.append(formatComplex(state.getAmplitude(basis)));
            }
            text.append(")  P=(");
            for (int basis = 0; basis < 3; basis++) {
                if (basis > 0) {
                    text.append(", ");
                }
                text.append(String.format(Locale.ROOT, "%.3f", state.getProbability(basis)));
            }
            text.append(")  norm^2=");
            text.append(String.format(Locale.ROOT, "%.6f", state.getNormSquared()));
            text.append('\n');
        }
        return text.toString();
    }

    private String formatComplex(BinaryTernaryQutritTranslator.ComplexAmplitude value) {
        return String.format(Locale.ROOT, "%+.3f%+.3fi",
                value.getReal(), value.getImaginary());
    }

    private String group(String value, int groupSize) {
        StringBuilder grouped = new StringBuilder(value.length() + value.length() / groupSize);
        for (int i = 0; i < value.length(); i++) {
            if (i > 0 && i % groupSize == 0) {
                grouped.append(' ');
            }
            grouped.append(value.charAt(i));
        }
        return grouped.toString();
    }

    private JTextArea createOutputArea() {
        JTextArea area = new JTextArea();
        area.setEditable(false);
        area.setFocusable(true);
        area.setLineWrap(true);
        area.setWrapStyleWord(true);
        area.setFont(MONO);
        area.setForeground(TEXT);
        area.setBackground(PANEL_DARK);
        area.setCaretColor(TEXT);
        area.setBorder(new EmptyBorder(10, 10, 10, 10));
        return area;
    }

    private JButton makeButton(String label, Color foreground, Color background) {
        JButton button = new JButton(label);
        button.setForeground(foreground);
        button.setBackground(background);
        button.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 12));
        button.setFocusPainted(false);
        button.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(58, 75, 96)),
                new EmptyBorder(8, 10, 8, 10)));
        return button;
    }

    private void copyReport() {
        if (lastTranslation == null) {
            return;
        }
        String report = "BINARY\n" + lastTranslation.getBinary()
                + "\n\nTERNARY (base 3)\n" + lastTranslation.getTernary()
                + "\n\nQUTRIT FOURIER STATES\n" + qutritOutput.getText()
                + "\nInput width: " + lastTranslation.getBinary().length()
                + "\nLeading binary zeroes: " + lastTranslation.getLeadingZeros()
                + "\nUnsigned integer value: " + lastTranslation.getValue()
                + "\nQuantum hardware: not used; amplitudes are simulated mathematically.";
        Toolkit.getDefaultToolkit().getSystemClipboard().setContents(new StringSelection(report), null);
        summary.setText("Translation report copied to the clipboard.");
    }

    private void clearAll() {
        input.setText("");
        binaryOutput.setText("");
        ternaryOutput.setText("");
        qutritOutput.setText("");
        lastTranslation = null;
        summary.setForeground(TEXT);
        summary.setText("Cleared. Enter binary digits and select Translate.");
    }

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
            // The default Swing look and feel is sufficient.
        }

        SwingUtilities.invokeLater(() -> {
            TranslationWorkbench workbench = new TranslationWorkbench();
            workbench.setVisible(true);
        });
    }
}