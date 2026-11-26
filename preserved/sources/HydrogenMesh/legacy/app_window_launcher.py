# ==============================================================================
# Compatibility launcher for the unified Tk interface.
# ==============================================================================
def execute_native_canvas():
    """Compatibility entry point for the unified sovereign window."""
    from sovereign_engine import main
    main()

if __name__ == "__main__":
    execute_native_canvas()
