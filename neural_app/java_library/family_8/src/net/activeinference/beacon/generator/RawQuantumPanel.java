package net.activeinference.beacon.generator;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.Random;
import java.util.concurrent.atomic.AtomicLong;

public class RawQuantumPanel extends JPanel {
    private static final int Q_SIZE = 8;
    private final AtomicLong heapAllocationMb;
    private final Random rawRandom = new Random();

    public RawQuantumPanel(AtomicLong heapAllocation) {
        this.heapAllocationMb = heapAllocation;
        setBackground(GeneratorTheme.BG_PANEL);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / Q_SIZE;
        int cellH = getHeight() / Q_SIZE;
        g.setFont(GeneratorTheme.MONO_SM);

        long heapLoad = heapAllocationMb.get();

        for (int i = 0; i < Q_SIZE; i++) {
            for (int j = 0; j < Q_SIZE; j++) {
                double rawAmp = ((i * j + heapLoad) % 100) / 100.0 + (rawRandom.nextDouble() * 0.05);
                rawAmp = Math.min(1.0, Math.max(0.0, rawAmp));
                
                String stateLabel = String.format("ψ|%.2f⟩", rawAmp);
                g.setColor(GeneratorTheme.QUANTUM_MAGENTA);
                g.drawString(stateLabel, j * cellW + 6, i * cellH + (cellH / 2 + 3));
            }
        }
    }
}
