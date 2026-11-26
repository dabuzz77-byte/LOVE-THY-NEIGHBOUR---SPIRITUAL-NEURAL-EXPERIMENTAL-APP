import pygame
import random
import math
from ..legacy.module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class HyperFidelityQuantumEngine:

    def __init__(self):
        self.CLR_BLACK = (0, 0, 0)
        self.CLR_DEEP_BLUE = (0, 30, 80)
        self.CLR_NEON_BLUE = (26, 117, 255)
        self.CLR_CYAN = (0, 213, 255)
        self.CLR_WHITE = (255, 255, 255)
        pygame.init()
        pygame.font.init()
        self.WIDTH, self.HEIGHT = (1024, 768)
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption('QUANTUM MATRIX ENGINE v6.0 // SUPER_STANDARD_GRAPHICS')
        self.clock = pygame.time.Clock()
        self.font_mono = pygame.font.SysFont('Courier', 13, bold=True)
        self.base_frequency = CARRIER_HZ
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        self.frame_id = 0
        self.num_particles = 120
        self.electron_cloud = []
        for _ in range(self.num_particles):
            self.electron_cloud.append({'angle': random.uniform(0, math.pi * 2), 'speed': random.uniform(0.02, 0.05), 'distance_orbit': random.uniform(140, 180), 'pulse_phase': random.uniform(0, 100)})

    def draw_higgs_field_grid(self):
        """Renders an interactive, glowing vector grid representing the background Higgs field."""
        grid_spacing = 48
        carrier = self.carrier.sample()
        activity = self.activity_sampler.snapshot()
        cpu = activity.cpu_percent or 0.0
        for x in range(0, self.WIDTH, grid_spacing):
            for y in range(0, self.HEIGHT, grid_spacing):
                dx = x - self.WIDTH // 2
                dy = y - self.HEIGHT // 2
                dist = math.sqrt(dx * dx + dy * dy) + 1.0
                wave_offset = math.sin(dist * 0.015 + carrier['phase_rad']) * (4 + min(1.0, cpu / 100.0) * 5)
                px = x + dx / dist * wave_offset
                py = y + dy / dist * wave_offset
                alpha = max(10, int(45 - dist / 12))
                grid_color = (int(self.CLR_DEEP_BLUE[0] * (alpha / 50)), int(self.CLR_DEEP_BLUE[1] * (alpha / 50)), int(self.CLR_DEEP_BLUE[2] * (alpha / 50)))
                pygame.draw.circle(self.screen, grid_color, (int(px), int(py)), 1)

    def render_hud_telemetry(self, current_freq, activity):
        """Compiles clean, crisp technical vector logs directly onto the display screen."""
        hud_logs = [f'================================================================================', f'[SYSTEM COGNITION RUNALL // CONFIG SPECIFICATION: SUPER_STANDARD_GRAPHICS]', f'================================================================================', f'  CORE HARDWARE NODE : 0x7F_SILICON_SPU_ACTIVE', f'  SOFTWARE CARRIER   : {current_freq:.4f} Hz   [generated reference, not a sensor]', f"  SYSTEM ACTIVITY    : CPU {(activity.cpu_percent if activity.cpu_percent is not None else 'n/a')}% | RAM {(activity.memory_percent if activity.memory_percent is not None else 'n/a')}%", f'  IDENTITY STATE     : 1 = 1 (VALID) // 1 = 0 (REJECTED_FALSE)', f'  VALENCE STRUCTURE  : HYDROGEN CORRELATION DEPLOYED (1p, 1e)', f'  PHASE VISUALIZATION: COMPLEX-VALUED PROJECTION (ILLUSTRATIVE)', f'  ACTIVITY RESPONSE  : PARTICLE SPEED AND GRID AMPLITUDE FOLLOW CPU LOAD', f'================================================================================']
        y_offset = 20
        for line in hud_logs:
            color = self.CLR_WHITE if 'VALID' in line or 'TRUE' in line or 'SPECIFICATION' in line else self.CLR_NEON_BLUE
            text_surface = self.font_mono.render(line, True, color)
            self.screen.blit(text_surface, (20, y_offset))
            y_offset += 18

    def execute_render_loop(self):
        """Launches the full hardware-accelerated desktop visualization app."""
        running = True
        while running:
            self.frame_id += 1
            carrier = self.carrier.sample()
            activity = self.activity_sampler.snapshot()
            cpu = activity.cpu_percent or 0.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
            self.screen.fill(self.CLR_BLACK)
            self.draw_higgs_field_grid()
            center_x = self.WIDTH // 2
            center_y = self.HEIGHT // 2 + 60
            pulse_radius = 22 + carrier['sin'] * (2.0 + cpu / 100.0)
            pygame.draw.circle(self.screen, self.CLR_DEEP_BLUE, (center_x, center_y), int(pulse_radius + 15), 1)
            pygame.draw.circle(self.screen, self.CLR_NEON_BLUE, (center_x, center_y), int(pulse_radius), 2)
            pygame.draw.circle(self.screen, self.CLR_WHITE, (center_x, center_y), 8)
            for p in self.electron_cloud:
                p['angle'] += p['speed'] * (0.65 + cpu / 100.0)
                p['pulse_phase'] += 0.015 + cpu / 4000.0 + carrier['sin'] * 0.001
                dynamic_distance = p['distance_orbit'] + math.sin(p['pulse_phase']) * 12
                ex = center_x + math.cos(p['angle']) * dynamic_distance
                ey = center_y + math.sin(p['angle']) * dynamic_distance
                if random.random() > 0.985:
                    p_color = self.CLR_WHITE
                    p_size = 3
                else:
                    p_color = self.CLR_CYAN if random.random() > 0.3 else self.CLR_NEON_BLUE
                    p_size = 2
                pygame.draw.circle(self.screen, p_color, (int(ex), int(ey)), p_size)
                if random.random() > 0.993:
                    pygame.draw.line(self.screen, self.CLR_DEEP_BLUE, (center_x, center_y), (int(ex), int(ey)), 1)
            current_frequency = carrier['frequency_hz']
            self.render_hud_telemetry(current_frequency, activity)
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
