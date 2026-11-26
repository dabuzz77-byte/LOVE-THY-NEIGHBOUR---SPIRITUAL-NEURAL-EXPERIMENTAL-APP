package engine.ui;
import neural.studio.*;





import java.awt.BorderLayout;

import java.awt.Color;

import javax.swing.JPanel;

import javax.swing.JScrollPane;

import javax.swing.JTextArea;



public class LogTerminalCanvas extends JPanel {

    private final JTextArea logArea = new JTextArea();



    public LogTerminalCanvas() {

        this.setLayout(new BorderLayout());

        this.setBackground(AestheticTheme.BG_MATRIX);

        this.setBorder(AestheticTheme.createBorder("GHOST MULTIPLEXER THROUGHPUT CHANNEL", AestheticTheme.ACCENT_GREEN));



        logArea.setEditable(false);

        logArea.setBackground(Color.BLACK);

        logArea.setForeground(AestheticTheme.ACCENT_GREEN);

        logArea.setFont(AestheticTheme.MONO_FONT);

        

        this.add(new JScrollPane(logArea), BorderLayout.CENTER);

    }



    public void logPacketStream(double ts, String details) {

        logArea.append(String.format("[T+%.2fs] [VIRTUE_PASS] %s\n", ts, details));

        if (logArea.getLineCount() > 40) {

            logArea.setText("[...] Substrate Logging Memory Recycled Clean\n");

        }

    }

}

