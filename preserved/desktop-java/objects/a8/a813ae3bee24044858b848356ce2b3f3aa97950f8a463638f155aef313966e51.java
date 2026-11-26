package engine.ui;

import java.awt.Color;
import java.awt.Font;
import javax.swing.BorderFactory;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

public final class AestheticTheme {
    public static final Color BG_MATRIX = new Color(10, 14, 20);
    public static final Color BG_PANEL = new Color(18, 24, 35);
    public static final Color ACCENT_CYAN = new Color(0, 240, 255);
    public static final Color ACCENT_GREEN = new Color(50, 255, 130);
    public static final Color ACCENT_ORANGE = new Color(255, 150, 0);
    public static final Color ACCENT_MAGENTA = new Color(240, 0, 255);
    
    public static final Font MONO_FONT = new Font("Monospaced", Font.PLAIN, 12);
    public static final Font HEADER_FONT = new Font("Monospaced", Font.BOLD, 14);

    public static Border createBorder(String heading, Color alertColor) {
        return BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(alertColor, 1),
            heading, TitledBorder.LEFT, TitledBorder.TOP, HEADER_FONT, alertColor
        );
    }
}
