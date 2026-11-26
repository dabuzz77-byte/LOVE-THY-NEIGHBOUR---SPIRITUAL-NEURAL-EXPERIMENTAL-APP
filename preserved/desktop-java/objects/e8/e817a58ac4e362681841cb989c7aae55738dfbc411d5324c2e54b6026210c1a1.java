package net.activeinference.beacon.carrier;

import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.Random;
import java.util.concurrent.atomic.AtomicLong;

public class UnmodulatedQuantumPanel extends JPanel {
    private static final int Q_SIZE = 8;
    private final AtomicLong combinedHeapAllocationMb;
    private final Random rawRandom = new Random();

    public UnmodulatedQuantumPanel(AtomicLong heapAllocation) {
        this.combinedHeapAllocationMb = heapAllocation;
        setBackground(CarrierTheme.BG_PANEL);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int cellW = getWidth() / Q_SIZE;
        int cellH = getHeight() / Q_SIZE;
        g.setFont(CarrierTheme.MONO_SM);

        long heapLoad = combinedHeapAllocationMb.get();

        for (int i = 0; i < Q_SIZE; i++) {
            for (int j = 0; j < Q_SIZE; j++) {
                double rawAmp = ((i * j + heapLoad) % 100) / 100.0 + (rawRandom.nextDouble() * 0.05);
                rawAmp = Math.min(1.0, Math.max(0.0, rawAmp));
                
                String stateLabel = String.format("ψ|%.2f⟩", rawAmp);
                g.setColor(CarrierTheme.QUANTUM_MAGENTA);
                g.drawString(stateLabel, j * cellW + 6, i * cellH + (cellH / 2 + 3));
            }
        }
    }
}
