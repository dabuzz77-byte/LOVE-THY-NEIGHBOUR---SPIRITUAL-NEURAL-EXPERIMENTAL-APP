package net.activeinference.beacon.system;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.concurrent.atomic.AtomicLong;

public class SystemQuantumPanel extends JPanel {
    private static final int Q_SIZE = 8;
    private final AtomicLong combinedHeapAllocationMb;
    private double waveTimeDelta = 0.0;

    public SystemQuantumPanel(AtomicLong heapAllocation) {
        this.combinedHeapAllocationMb = heapAllocation;
        setBackground(DashboardTheme.BG_PANEL);
    }

    public void setWaveTimeDelta(double timeDelta) {
        this.waveTimeDelta = timeDelta;
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / Q_SIZE;
        int cellH = getHeight() / Q_SIZE;
        g.setFont(DashboardTheme.MONO_SM);

        double memoryModifier = (combinedHeapAllocationMb.get() / 1024.0) * 0.05;

        for (int i = 0; i < Q_SIZE; i++) {
            for (int j = 0; j < Q_SIZE; j++) {
                double baseAmplitude = Math.abs(Math.cos(waveTimeDelta + (i * (0.5 + memoryModifier)) - (j * 0.2)));
                String stateLabel = String.format("ψ|%.2f⟩", baseAmplitude);

                g.setColor(DashboardTheme.QUANTUM_MAGENTA);
                g.drawString(stateLabel, j * cellW + 6, i * cellH + (cellH / 2 + 3));
            }
        }
    }
}
