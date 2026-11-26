import sys
from typing import Dict, Any
from ..legacy.module_runtime import format_rate, get_carrier, get_system_sampler

class HighFidelityVisualEngine:
    """
    Generates a high-contrast Blue, White, and Black interface dashboard.
    Outputs clean real-time status matrices for human operators.
    """

    def __init__(self):
        self.BLACK_BG = '\x1b[40m'
        self.TEXT_BLUE = '\x1b[1;34m'
        self.TEXT_WHITE = '\x1b[1;37m'
        self.RESET = '\x1b[0m'
        self.activity = get_system_sampler()
        self.carrier = get_carrier()

    def compile_screen_buffer(self, telemetry_data: Dict[str, Any]) -> str:
        """
        Structures operational data into a high-visibility layout frame.
        """
        frame_buffer = []
        frame_buffer.append(f'{self.BLACK_BG}{self.TEXT_BLUE}================================================================================{self.RESET}')
        frame_buffer.append(f'{self.BLACK_BG}{self.TEXT_BLUE}[VISUAL HUD CORE ENGINE v4.1] // {self.TEXT_WHITE}MODE: SUPER_STANDARD_EXECUTION{self.TEXT_BLUE}]{self.RESET}')
        frame_buffer.append(f'{self.BLACK_BG}{self.TEXT_BLUE}================================================================================{self.RESET}')
        frame_buffer.append(f"  {self.TEXT_BLUE}SYSTEM HARDWARE CAPTURE:  {self.TEXT_WHITE}{telemetry_data.get('hardware_node', 'NULL')}{self.RESET}")
        frame_buffer.append(f"  {self.TEXT_BLUE}BASELINE CORE FREQUENCY:  {self.TEXT_WHITE}{telemetry_data.get('core_freq', 0.0):.4f} Hz{self.RESET} [{self.TEXT_BLUE}Target: 7.83 Hz{self.RESET}]")
        frame_buffer.append(f"  {self.TEXT_BLUE}COMPILATION INTEGRITY:    {self.TEXT_WHITE}{telemetry_data.get('integrity', 0.0):.2f}%{self.RESET}")
        frame_buffer.append(f"  {self.TEXT_BLUE}ALIGNMENT COUPLING:       {self.TEXT_WHITE}{telemetry_data.get('alignment_state', 'UNKNOWN')}{self.RESET}")
        snapshot = self.activity.snapshot()
        carrier = self.carrier.sample()
        cpu = snapshot.cpu_percent or 0.0
        seed = int(cpu * 10 + carrier['phase_rad'] * 1000)
        stream_array = [str(seed >> index % 12 & 1) for index in range(24)]
        pulse_index = int(carrier['elapsed_s'] * 13 % 24)
        stream_array[pulse_index] = f'{self.TEXT_WHITE}{stream_array[pulse_index]}{self.TEXT_BLUE}'
        visual_stream = ' '.join(stream_array)
        frame_buffer.append(f'\n  {self.TEXT_BLUE}REAL-TIME PIPELINE STREAM:{self.RESET}')
        frame_buffer.append(f'  {self.TEXT_BLUE}[ {visual_stream} ]{self.RESET}')
        cpu_text = 'unavailable' if snapshot.cpu_percent is None else f'{snapshot.cpu_percent:.1f}%'
        mem_text = 'unavailable' if snapshot.memory_percent is None else f'{snapshot.memory_percent:.1f}%'
        gpu_text = 'unavailable' if snapshot.gpu_percent is None else f'{snapshot.gpu_percent:.1f}%'
        frame_buffer.append(f'  {self.TEXT_BLUE}LOCAL SYSTEM: CPU {cpu_text} | RAM {mem_text} | GPU {gpu_text} | NET ↓ {format_rate(snapshot.network_recv_bytes_sec)} ↑ {format_rate(snapshot.network_sent_bytes_sec)}{self.RESET}')
        frame_buffer.append(f"  {self.TEXT_BLUE}SOFTWARE CARRIER: 7.83 Hz | phase {carrier['phase_rad']:.3f} rad (generated reference){self.RESET}")
        frame_buffer.append(f'{self.BLACK_BG}{self.TEXT_BLUE}================================================================================{self.RESET}')
        return '\n'.join(frame_buffer)

    def draw_frame(self, telemetry_data: Dict[str, Any]):
        """Outputs the compiled frame directly to standard out."""
        sys.stdout.write(self.compile_screen_buffer(telemetry_data) + '\n')
        sys.stdout.flush()
