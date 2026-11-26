import neural.studio.*;
// ============================================================================
// BLOCK 1: FUNCTIONAL INTERFACE FOR STATE CALLBACKS
// ============================================================================


/**
 * Functional callback mapping interface used to route decoupled graphics states
 * and system telemetry between underlying kernels and presentation panels.
 */
@FunctionalInterface
public interface GraphicsStateCallback {
    /**
     * Dispatches runtime changes to registered graphical listeners.
     * 
     * @param statusMessage System status log detail text
     * @param waveAlignment Scaled wave positioning index (value range: -1.0 to 1.0)
     * @param coherencePct  Calculated parity alignment stability percentage (0 to 100)
     */
    void onStateUpdate(String statusMessage, double waveAlignment, double coherencePct);
}
