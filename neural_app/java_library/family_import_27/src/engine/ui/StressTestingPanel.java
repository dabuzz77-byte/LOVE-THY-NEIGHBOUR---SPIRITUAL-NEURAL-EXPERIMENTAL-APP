package engine.ui;
import neural.studio.*;





import engine.model.TelemetryModel;

import java.awt.BorderLayout;

import java.awt.Color; // ✨ FIXED: Added explicit color token import

import javax.swing.JLabel;

import javax.swing.JPanel;

import javax.swing.JProgressBar;



public class StressTestingPanel extends JPanel {

    private final JProgressBar prgConfidence = new JProgressBar(0, 1000);



    public StressTestingPanel() {

        this.setLayout(new BorderLayout(15, 15));

        this.setBackground(AestheticTheme.BG_PANEL);

        this.setBorder(AestheticTheme.createBorder("ALIGNMENT ROBUSTNESS TESTING MATRIX", AestheticTheme.ACCENT_ORANGE));



        JLabel title = new JLabel("MODEL COMPLIANCE OVERRIDE CONFIDENCE TARGET:");

        title.setForeground(Color.WHITE);

        title.setFont(AestheticTheme.MONO_FONT);



        prgConfidence.setForeground(AestheticTheme.ACCENT_GREEN);

        prgConfidence.setBackground(Color.DARK_GRAY);

        prgConfidence.setStringPainted(true);

        prgConfidence.setFont(AestheticTheme.HEADER_FONT);



        this.add(title, BorderLayout.NORTH);

        this.add(prgConfidence, BorderLayout.CENTER);

    }



    public void updateMetrics(TelemetryModel model) {

        int scaledValue = (int) (model.getAlignmentScore() * 1000);

        prgConfidence.setValue(scaledValue);

        prgConfidence.setString(String.format("%.2f%% Alignment Strength", model.getAlignmentScore() * 100));

    }

}

