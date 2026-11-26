package net.activeinference.beacon.core;
import neural.studio.*;


import javax.swing.JPanel;
import java.awt.Graphics;
import java.util.Random;

public class QuantumGridPanel extends JPanel {
    private final int matrixSize = 8;
    private final double[][] amplitudes = new double[matrixSize][matrixSize];
    private final Random rand = new Random();

    public QuantumGridPanel() {
        setBackground(DashboardTheme.BG_CONTAINER);
    }

    public void spinQuantumStates() {
        for (int i = 0; i < matrixSize; i++) {
            for (int j = 0; j < matrixSize; j++) {
                amplitudes[i][j] = rand.nextDouble();
            }
        }
        repaint();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        int w = getWidth() / matrixSize;
        int h = getHeight() / matrixSize;
        g.setFont(DashboardTheme.MONO_SM);
        
        for (int i = 0; i < matrixSize; i++) {
            for (int j = 0; j < matrixSize; j++) {
                double amp = amplitudes[i][j];
                g.setColor(DashboardTheme.QUANTUM_PHASE);
                String stateString = String.format("ψ|%.2f⟩", amp);
                g.drawString(stateString, j * w + 4, i * h + (h/2 + 3));
            }
        }
    }
}
