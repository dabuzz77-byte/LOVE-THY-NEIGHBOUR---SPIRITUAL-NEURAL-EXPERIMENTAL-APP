# Optional NVIDIA GPU backend

Install into this app only, using the Python runtime selected by Start Neural App:

python -m pip install --target vendor-gpu "cupy-cuda12x[ctk]"

The adaptive numeric rail discovers this folder on startup and verifies CUDA device access. CPU fallback remains available. The source release does not bundle the downloaded NVIDIA libraries. Their own licences apply. No display-driver modification is performed.

Reference: https://docs.cupy.dev/en/stable/install.html
