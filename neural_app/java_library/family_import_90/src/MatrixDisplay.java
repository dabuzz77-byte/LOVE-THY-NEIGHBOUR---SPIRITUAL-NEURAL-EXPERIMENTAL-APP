import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class MatrixDisplay extends JPanel {

    // The precise matrix configuration string preserved from your input
    private final String[] matrixLines = {
        "   1   0 0   1      0   1 1    0",
        "   1                0",
        "   0   1 1   0      1   0 0    1",
        "   0   1 1   0      1   0 0    1",
        "   1                0",
        "   1         1      0          0",
        "",
        "   1         1      0          0",
        "",
        "   0         0      1          1"
    };

    private boolean invertColors = false;

    public MatrixDisplay() {
        // Background color of the display canvas (Deep dark slate)
        setBackground(new Color(10, 15, 20));

        // Setting a high-frequency swing timer to generate the loop state shift (approx every 128ms)
        SharedTimer loopTimer = new SharedTimer(128, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                // Alternates the state of the colors in the loop loop
                invertColors = !invertColors;
                repaint(); // Forces the window to refresh its graphics state
            }
        });
        loopTimer.start();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2d = (Graphics2D) g;
        
        // Enabling anti-aliasing for cleaner, sharper text rendering
        g2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        // Setting up a crisp monospaced font to maintain absolute column spacing alignments
        g2d.setFont(new Font("Monospaced", Font.BOLD, 22));

        int startX = 40;
        int startY = 60;
        int lineHeight = 30;

        // Iterate through each character of every single enplaced line
        for (int row = 0; row < matrixLines.length; row++) {
            String currentLine = matrixLines[row];
            int currentX = startX;

            for (int col = 0; col < currentLine.length(); col++) {
                char ch = currentLine.charAt(col);

                if (ch == '1') {
                    // Set primary high-signal color (Dynamic neon blue / teal shift)
                    g2d.setColor(invertColors ? new Color(0, 255, 200) : new Color(0, 180, 255));
                    g2d.drawString(String.valueOf(ch), currentX, startY + (row * lineHeight));
                } else if (ch == '0') {
                    // Set secondary complementary balance color (Dynamic amber / slate shift)
                    g2d.setColor(invertColors ? new Color(255, 140, 0) : new Color(130, 140, 150));
                    g2d.drawString(String.valueOf(ch), currentX, startY + (row * lineHeight));
                } else {
                    // Maintain blank grid spacing variables exactly as provided
                    g2d.drawString(String.valueOf(ch), currentX, startY + (row * lineHeight));
                }
                
                // Advanced advance column space pointer based on character width
                currentX += g2d.getFontMetrics().charWidth(ch);
            }
        }
    }

    public static void main(String[] args) {
        // Enforce safe event-dispatch thread GUI loading initialization
        SwingUtilities.invokeLater(() -> {
            SectionFrame frame = new SectionFrame("Substrate State Alignment Dashboard");
            MatrixDisplay panel = new MatrixDisplay();
            
            frame.add(panel);
            frame.setSize(620, 440);
            frame.setDefaultCloseOperation(SectionFrame.EXIT_ON_CLOSE);
            frame.setLocationRelativeTo(null); // Center window layout exactly on terminal launch
            frame.setVisible(true);
        });
    }
}
