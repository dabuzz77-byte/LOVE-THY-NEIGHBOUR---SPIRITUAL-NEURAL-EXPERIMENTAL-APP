package net.activeinference.beacon.core;
import neural.studio.*;


import javax.swing.JTextArea;
import javax.swing.SwingUtilities;
import java.awt.Color;

public class ControlMatrixConsole extends JTextArea {
    public ControlMatrixConsole() {
        setEditable(false);
        setBackground(new Color(10, 14, 18));
        setForeground(DashboardTheme.GRID_HEX_1);
        setFont(DashboardTheme.MONO_SM);
    }

    public void pushLog(String message) {
        SwingUtilities.invokeLater(() -> {
            append(message + "\n");
            setCaretPosition(getDocument().getLength());
            if (getLineCount() > 250) {
                try {
                    int end = getLineEndOffset(20);
                    replaceRange("", 0, end);
                } catch (Exception ignored) {}
            }
        });
    }
}
