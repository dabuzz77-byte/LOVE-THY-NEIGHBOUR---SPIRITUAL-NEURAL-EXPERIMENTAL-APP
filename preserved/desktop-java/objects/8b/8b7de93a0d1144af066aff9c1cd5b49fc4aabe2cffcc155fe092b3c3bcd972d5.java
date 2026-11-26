package engine.ui;

import engine.model.TelemetryModel;
import java.awt.GridLayout;
import javax.swing.*;

public class TopBannerPanel extends JPanel {
    private final JLabel lblFlux = new JLabel("FLUX: 0.0000", SwingConstants.CENTER);
    private final JLabel lblFreq = new JLabel("FREQ: 7.8300 Hz", SwingConstants.CENTER);
    private final JLabel lblDebt = new JLabel("DEBT: 0.0000", SwingConstants.CENTER);
    private final JLabel lblParity = new JLabel("PARITY: 1=1 CONFIRMED", SwingConstants.CENTER);

    public TopBannerPanel() {
        this.setLayout(new GridLayout(1, 4, 10, 10));
        this.setBackground(AestheticTheme.BG_PANEL);
        this.setBorder(AestheticTheme.createBorder("SUBSTRATE CONTROL SYSTEM REGISTER", AestheticTheme.ACCENT_CYAN));
        
        setupLabel(lblFlux, AestheticTheme.ACCENT_CYAN);
        setupLabel(lblFreq, AestheticTheme.ACCENT_CYAN);
        setupLabel(lblDebt, AestheticTheme.ACCENT_ORANGE);
        setupLabel(lblParity, AestheticTheme.ACCENT_GREEN);
    }

    private void setupLabel(JLabel l, java.awt.Color c) {
        l.setFont(AestheticTheme.HEADER_FONT);
        l.setForeground(c);
        this.add(l);
    }

    public void synchronizeDisplay(TelemetryModel model) {
        lblFlux.setText(String.format("FLUX: %+.4f", model.getCurrentFlux()));
        lblFreq.setText(String.format("FREQ: %.4f Hz", model.getDynamicFrequency()));
        lblDebt.setText(String.format("DEBT: %.4f", model.getAlgorithmicDebtTar()));
    }
}
