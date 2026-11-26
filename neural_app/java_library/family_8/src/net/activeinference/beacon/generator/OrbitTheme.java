package net.activeinference.beacon.orbit;
import neural.studio.*;


import java.awt.Color;
import java.awt.Font;

public final class OrbitTheme {
    public static final Color BG_MATRIX = new Color(5, 7, 9);
    public static final Color BG_PANEL = new Color(14, 18, 22);
    
    // Core Lattice Plasma Colors
    public static final Color ELEC_CORE = new Color(220, 245, 255);
    public static final Color ELEC_GLOW = new Color(0, 160, 255, 130);
    public static final Color BINARY_GLINT = new Color(50, 215, 120);
    public static final Color QUANTUM_PURPLE = new Color(190, 80, 255);
    public static final Color TERNARY_AMBER = new Color(255, 160, 0);
    
    // Fixed Font and Border Color Components
    public static final Color TEXT_LIGHT = new Color(230, 235, 245);
    public static final Color TEXT_MUTED = new Color(130, 145, 160);
    
    public static final Font MONO_SM = new Font("Monospaced", Font.PLAIN, 11);
    public static final Font SANS_MD = new Font("SansSerif", Font.BOLD, 12);
    
    private OrbitTheme() {}
}
