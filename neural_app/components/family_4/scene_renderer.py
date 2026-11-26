"""Bounded, CPU-rendered signal scenes. Stochastic effects are visual simulations.

Static stars, glyphs, sphere shading and data cells are cached. Frames use one
bitmap transfer to Tk rather than thousands of canvas commands.
"""
from collections import deque
import math
from pathlib import Path
import random
import time
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
TAU = math.tau
CYAN = (76, 244, 214)
BLUE = (66, 143, 255)
GOLD = (255, 192, 96)
LAND = [[(-17, 37), (10, 36), (34, 31), (51, 11), (42, -12), (30, -34), (18, -35), (10, -18), (-4, 5), (-17, 15)], [(-10, 36), (-9, 58), (9, 72), (35, 70), (45, 55), (80, 75), (145, 66), (179, 52), (154, 42), (130, 33), (122, 7), (106, -5), (96, 5), (80, 8), (76, 24), (58, 27), (44, 12), (36, 32)], [(-168, 65), (-140, 70), (-110, 75), (-80, 65), (-52, 48), (-82, 25), (-89, 16), (-105, 22), (-117, 32), (-125, 49), (-155, 58)], [(-80, 10), (-61, 10), (-35, -7), (-42, -23), (-67, -55), (-76, -42), (-81, -6)], [(113, -22), (129, -12), (145, -14), (154, -28), (146, -39), (119, -35)], [(-55, 60), (-20, 70), (-27, 82), (-48, 83), (-65, 75)], [(45, -13), (50, -16), (49, -25), (44, -25)], [(129, 31), (141, 45), (145, 42), (135, 33)]]

def font(size, mono=False):
    path = Path('C:/Windows/Fonts') / ('consola.ttf' if mono else 'segoeui.ttf')
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()

def mix(a, b, t):
    return tuple((round(x + (y - x) * max(0, min(1, t))) for x, y in zip(a, b)))

class SceneRenderer:

    def __init__(self, seed=7813):
        self.rng = random.Random(seed)
        self.epoch = time.monotonic()
        self.last = None
        self.pulses = deque(maxlen=96)
        self.pulse_count = 0
        self.background = None
        self.background_key = None
        self.grid = None
        self.grid_key = None
        self.assets = {}
        self.glyphs = {}
        self.fonts = {}
        self.last_ms = 0
        self.last_size = (0, 0)
        self.last_geometry = {}
        self.simulated = True
        self.earth_texture = None
        self.earth_masks = {}
        self.globe_cache = None

    def f(self, size, mono=False):
        key = (size, mono)
        if key not in self.fonts:
            self.fonts[key] = font(size, mono)
        return self.fonts[key]

    def glow(self, r, color):
        r = max(2, int(r))
        key = ('glow', r, color)
        if key not in self.assets:
            image = Image.new('RGBA', (r * 2 + 2, r * 2 + 2))
            d = ImageDraw.Draw(image)
            for ring in range(24, 0, -1):
                rr = r * ring / 24
                alpha = int(80 * (1 - ring / 25) ** 2)
                d.ellipse((r - rr, r - rr, r + rr, r + rr), fill=(*color, alpha))
            if len(self.assets) > 24:
                self.assets.clear()
            self.assets[key] = image
        return self.assets[key]

    def light(self, image, x, y, r, color):
        sprite = self.glow(r, color)
        image.paste(sprite, (round(x) - sprite.width // 2, round(y) - sprite.height // 2), sprite)

    def backdrop(self, w, h, preset):
        key = (w, h, preset)
        if self.background_key == key:
            return self.background.copy()
        image = Image.new('RGB', (w, h))
        d = ImageDraw.Draw(image)
        for y in range(h):
            v = y / max(1, h - 1)
            d.line((0, y, w, y), fill=mix((3, 8, 17), (7, 19, 29), v))
        rng = random.Random(9102)
        for _ in range(210):
            x = rng.randrange(w)
            y = rng.randrange(max(1, h - 85))
            b = rng.randrange(38, 133)
            d.point((x, y), fill=(int(b * 0.7), int(b * 0.83), b))
            if b > 125:
                d.line((x - 2, y, x + 2, y), fill=(45, 67, 88))
        horizon = h * 0.64
        for i in range(13):
            y = horizon + (h - horizon) * (i / 12) ** 1.8
            d.line((0, y, w, y), fill=(10, 36, 47))
        for i in range(-10, 11):
            d.line((w * 0.5 + i * 18, horizon, w * 0.5 + i * w * 0.16, h), fill=(10, 36, 47))
        self.background = image
        self.background_key = key
        return image.copy()

    def sphere(self, r, kind):
        r = int(r)
        key = ('sphere', r, kind)
        if key in self.assets:
            return self.assets[key]
        size = 2 * r + 2
        image = Image.new('RGBA', (size, size))
        pixels = image.load()
        rng = random.Random(52)
        noise = Image.new('L', (28, 28))
        noise.putdata([rng.randrange(50, 256) for _ in range(784)])
        noise = noise.resize((size, size), Image.Resampling.BICUBIC).load()
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                x = xx / r
                y = yy / r
                rr = x * x + y * y
                if rr > 1:
                    continue
                z = math.sqrt(1 - rr)
                light = max(0, -0.57 * x - 0.23 * y + 0.75 * z)
                if kind == 'earth':
                    edge = max(0, 1 - z)
                    c = mix((3, 12, 30), (27, 109, 174), light)
                    c = mix(c, (40, 142, 197), edge * 0.32)
                else:
                    heat = 0.65 * noise[xx + r + 1, yy + r + 1] / 255 + 0.35 * rng.random()
                    c = mix((177, 37, 2), (255, 241, 172), max(0, min(1, 0.12 + light * 0.35 + heat * 0.57)))
                pixels[xx + r + 1, yy + r + 1] = (*c, 255)
        if len(self.assets) > 24:
            self.assets.clear()
        self.assets[key] = image
        return image

    def atom(self, image, cx, cy, r, t):
        d = ImageDraw.Draw(image)
        self.light(image, cx, cy, r * 1.12, (25, 104, 199))
        rng = random.Random(139)
        for _ in range(170):
            angle = rng.random() * TAU
            distance = r * min(1.3, abs(rng.gauss(0.67, 0.22)))
            x = cx + math.cos(angle) * distance
            y = cy + math.sin(angle) * distance * 0.65
            d.point((x, y), fill=(17, 57 + rng.randrange(55), 98 + rng.randrange(80)))
        for band in range(3):
            theta = band * math.pi / 3 + 0.2
            points = []
            for i in range(101):
                a = i * TAU / 100
                x = math.cos(a) * r
                y = math.sin(a) * r * 0.29
                points.append((cx + x * math.cos(theta) - y * math.sin(theta), cy + x * math.sin(theta) + y * math.cos(theta)))
            d.line(points, fill=(29, 99, 144), width=1)
            a = t * (0.9 + band * 0.17) + band * 2.1
            trail = []
            for j in range(16):
                angle = a - j * 0.037
                x = math.cos(angle) * r
                y = math.sin(angle) * r * 0.29
                trail.append((cx + x * math.cos(theta) - y * math.sin(theta), cy + x * math.sin(theta) + y * math.cos(theta)))
            for j in range(1, len(trail)):
                d.line((trail[j - 1], trail[j]), fill=mix((15, 58, 87), CYAN, 1 - j / len(trail)), width=2)
            if band == 0:
                ex, ey = trail[0]
                self.light(image, ex, ey, 14, CYAN)
                d.ellipse((ex - 3, ey - 3, ex + 3, ey + 3), fill=(218, 255, 250))
        self.light(image, cx, cy, 28, (255, 108, 66))
        d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=(255, 156, 98), outline=(255, 239, 207), width=2)
        d.line((cx - 3, cy, cx + 3, cy), fill=(125, 48, 29), width=1)
        d.line((cx, cy - 3, cx, cy + 3), fill=(125, 48, 29), width=1)

    def sun(self, image, cx, cy, r, t):
        d = ImageDraw.Draw(image)
        self.light(image, cx, cy, r * 1.9, (255, 124, 27))
        for k in range(3):
            points = []
            for i in range(181):
                a = i * TAU / 180
                rr = r * (1.08 + k * 0.12) + math.sin(a * 11 + t * 0.7 + k) * r * 0.028
                points.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            d.line(points, fill=mix((83, 29, 6), (239, 130, 35), 1 - k * 0.34), width=1)
        sphere = self.sphere(r, 'sun')
        image.paste(sphere, (round(cx - r - 1), round(cy - r - 1)), sphere)
        for k in range(10):
            angle = k * TAU / 10 + t * 0.018
            rr = r * 0.73
            x = cx + math.cos(angle) * rr
            y = cy + math.sin(angle) * rr
            length = r * 0.17
            d.arc((x - length, y - length, x + length, y + length), 10 + k * 18 + t * 13, 170 + k * 18 + t * 13, fill=(255, 215, 108), width=1)

    @staticmethod
    def projection(lon, lat, rotation):
        a = math.radians(lon) + rotation
        b = math.radians(lat)
        return (math.cos(b) * math.sin(a), -math.sin(b), math.cos(b) * math.cos(a))

    def globe(self, r, rotation):
        cache_key = (int(r), round(rotation / 0.005))
        if self.globe_cache is not None and self.globe_cache[0] == cache_key:
            return self.globe_cache[1]
        if self.earth_texture is None:
            tex = Image.new('RGB', (720, 360), (15, 66, 118))
            td = ImageDraw.Draw(tex)
            rng = random.Random(351)
            for y in range(360):
                td.line((0, y, 720, y), fill=mix((10, 43, 86), (22, 83, 133), math.sin(y / 360 * math.pi)))
            for polygon in LAND:
                coast = []
                for i, (lon, lat) in enumerate(polygon):
                    lon2, lat2 = polygon[(i + 1) % len(polygon)]
                    steps = max(2, round(math.hypot(lon2 - lon, lat2 - lat) / 2))
                    for j in range(steps):
                        a = j / steps
                        coast.append(((lon + (lon2 - lon) * a + math.sin(a * math.pi) * rng.uniform(-1.1, 1.1) + 180) * 2, (90 - lat - (lat2 - lat) * a + math.sin(a * math.pi) * rng.uniform(-0.7, 0.7)) * 2))
                td.polygon(coast, fill=(64, 113, 79))
                td.line(coast + [coast[0]], fill=(91, 141, 103), width=1)
            clouds = Image.new('RGBA', tex.size)
            cd = ImageDraw.Draw(clouds)
            for _ in range(210):
                x = rng.randrange(720)
                y = rng.randrange(45, 315)
                rx = rng.randrange(3, 18)
                ry = rng.randrange(1, 4)
                cd.ellipse((x - rx, y - ry, x + rx, y + ry), fill=(216, 237, 244, rng.randrange(20, 120)))
            tex.paste(clouds.filter(ImageFilter.GaussianBlur(1.4)), (0, 0), clouds.filter(ImageFilter.GaussianBlur(1.4)))
            td = ImageDraw.Draw(tex)
            td.rectangle((0, 338, 720, 359), fill=(157, 192, 209))
            wide = Image.new('RGB', (2160, 360))
            wide.paste(tex, (0, 0))
            wide.paste(tex, (720, 0))
            wide.paste(tex, (1440, 0))
            self.earth_texture = wide
        r = int(r)
        size = r * 2 + 2
        key = r
        if key not in self.earth_masks:
            shade = Image.new('RGB', (size, size))
            alpha = Image.new('L', (size, size))
            sp = shade.load()
            ap = alpha.load()
            for yy in range(size):
                for xx in range(size):
                    x = (xx - r - 1) / r
                    y = (yy - r - 1) / r
                    rr = x * x + y * y
                    if rr <= 1:
                        z = math.sqrt(1 - rr)
                        light = max(0, -0.63 * x - 0.2 * y + 0.72 * z)
                        b = int(255 * (0.16 + 0.84 * light))
                        sp[xx, yy] = (b, b, min(255, b + 8))
                        ap[xx, yy] = 255
            if len(self.earth_masks) >= 3:
                self.earth_masks.clear()
            self.earth_masks[key] = (shade, alpha)
        shade, alpha = self.earth_masks[key]
        mesh = []
        step = 14
        center = (-rotation + math.pi) % TAU - math.pi

        def uv(x, y):
            x = (x - r - 1) / r
            y = (y - r - 1) / r
            rr = x * x + y * y
            if rr >= 1:
                x, y = (x / math.sqrt(rr) * 0.9999, y / math.sqrt(rr) * 0.9999)
            z = math.sqrt(max(1e-05, 1 - x * x - y * y))
            return ((math.atan2(x, z) + center) / TAU * 720 + 1080, (math.asin(max(-1, min(1, y))) / math.pi + 0.5) * 360)
        for y in range(0, size, step):
            for x in range(0, size, step):
                x1 = min(size, x + step)
                y1 = min(size, y + step)
                mesh.append(((x, y, x1, y1), uv(x, y) + uv(x, y1) + uv(x1, y1) + uv(x1, y)))
        mapped = self.earth_texture.transform((size, size), Image.Transform.MESH, mesh, Image.Resampling.BILINEAR)
        mapped = ImageChops.multiply(mapped, shade).convert('RGBA')
        mapped.putalpha(alpha)
        self.globe_cache = (cache_key, mapped)
        return mapped

    def earth(self, image, cx, cy, r, t):
        d = ImageDraw.Draw(image)
        self.light(image, cx, cy, r * 1.47, (37, 114, 255))
        rotation = 0.34 + t * 0.023
        sphere = self.globe(r, rotation)
        image.paste(sphere, (round(cx - r - 1), round(cy - r - 1)), sphere)
        d.arc((cx - r, cy - r, cx + r, cy + r), 205, 340, fill=(129, 210, 255), width=2)
        d.arc((cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), 35, 170, fill=(37, 100, 172), width=1)

    def glyph(self, char, color, cell):
        key = (char, color, cell)
        if key not in self.glyphs:
            if len(self.glyphs) > 200:
                self.glyphs.clear()
            tile = Image.new('RGBA', (cell, cell + 3))
            d = ImageDraw.Draw(tile)
            d.text((cell / 2, (cell + 3) / 2), char, font=self.f(max(9, cell - 2), True), fill=color, anchor='mm')
            self.glyphs[key] = tile
        return self.glyphs[key]

    def matrix(self, image, bits, previous, t, detail):
        w, h = image.size
        cell = 16 if detail == 'High' else 18 if detail == 'Balanced' else 22
        cols = max(1, (w - 46) // cell)
        rows = max(1, (h - 146) // (cell + 3))
        capacity = cols * rows
        key = (w, h, bits, previous, detail)
        if self.grid_key != key:
            layer = Image.new('RGB', (w, h), (3, 12, 17))
            d = ImageDraw.Draw(layer)
            for col in range(cols):
                d.line((24 + col * cell, 56, 24 + col * cell, h - 84), fill=(5, 27, 29))
            for index in range(capacity):
                x = 24 + index % cols * cell
                y = 57 + index // cols * (cell + 3)
                char = bits[index] if index < len(bits) else '·'
                changed = index < len(previous) and index < len(bits) and (bits[index] != previous[index])
                color = (242, 182, 89) if changed else (28, 112, 91) if char == '1' else (13, 62, 57) if char == '0' else (10, 33, 39)
                glyph = self.glyph(char, color, cell)
                layer.paste(glyph, (x, y), glyph)
            self.grid = layer
            self.grid_key = key
        image.paste(self.grid)
        for col in range(0, cols, 1 if detail != 'Low power' else 2):
            head = (t * (2.1 + col * 17 % 19 * 0.16) + col * 3.71) % (rows + 12) - 6
            for tail in range(7):
                row = int(head) - tail
                if not 0 <= row < rows:
                    continue
                index = row * cols + col
                char = bits[index] if index < len(bits) else '·'
                color = (192, 255, 220) if tail == 0 else mix((9, 36, 32), (50, 228, 132), 1 - tail / 7)
                glyph = self.glyph(char, color, cell)
                image.paste(glyph, (24 + col * cell, 57 + row * (cell + 3)), glyph)
        self.last_geometry = dict(cell=cell, cols=cols, rows=rows, left=24, top=57)

    def render(self, width, height, preset='Cosmos', bits='', previous='', bus_events=(), pointer=None, detail='Balanced', now=None):
        started = time.perf_counter()
        clock = time.monotonic() if now is None else now
        t = clock - self.epoch
        dt = 0 if self.last is None else min(0.25, max(0, clock - self.last))
        self.last = clock
        scale = min(1, 1280 / max(1, width), 720 / max(1, height))
        w = max(200, round(width * scale))
        h = max(180, round(height * scale))
        if detail == 'Low power':
            w = max(200, round(w * 0.8))
            h = max(180, round(h * 0.8))
        while self.pulses and clock - self.pulses[0][0] > 3.5:
            self.pulses.popleft()
        recent = sum((0 <= clock - stamp < 1.5 for stamp, _ in bus_events))
        rate = 3.8 + min(4, recent * 0.2) if self.simulated else 0
        if self.rng.random() < 1 - math.exp(-rate * dt):
            self.pulses.append((clock, self.rng.randrange(3), self.rng.random() * TAU, self.rng.uniform(0.5, 1)))
            self.pulse_count += 1
        image = self.backdrop(w, h, preset)
        d = ImageDraw.Draw(image)
        if preset == 'Matrix':
            self.matrix(image, bits[:8192], previous[:8192], t, detail)
        else:
            centers = [(w * 0.19, h * 0.47), (w * 0.5, h * 0.47), (w * 0.81, h * 0.47)]
            r = min(h * 0.225, w * 0.112)
            if preset not in ('Cosmos', 'Overview'):
                which = {'Hydrogen': 0, 'Stellar': 1, 'Dyson': 1, 'Earth': 2, 'Biosphere': 2}.get(preset, 0)
                centers = [(w * 0.5, h * 0.46)] * 3
                r = min(w * 0.27, h * 0.31)
                active = [which]
            else:
                active = [0, 1, 2]
            if len(active) == 3:
                for i in range(2):
                    x0, y0 = centers[i]
                    x1, y1 = centers[i + 1]
                    y0 += r * 0.65
                    y1 += r * 0.65
                    points = [(x0 + (x1 - x0) * j / 60, y0 + math.sin(j / 60 * math.pi) * r * 0.32) for j in range(61)]
                    d.line(points, fill=(15, 58, 74), width=3)
                    d.line(points, fill=(28, 105, 110), width=1)
                    for k in range(3):
                        u = (t * 0.14 + k / 3 + i * 0.12) % 1
                        x = x0 + (x1 - x0) * u
                        y = y0 + math.sin(u * math.pi) * r * 0.32
                        self.light(image, x, y, 9, CYAN)
                        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=CYAN)
            names = ['HYDROGEN / ¹H', 'STELLAR / PLASMA', 'EARTH / BIOSPHERE']
            colors = [CYAN, GOLD, BLUE]
            for which in active:
                x, y = centers[which]
                (self.atom if which == 0 else self.sun if which == 1 else self.earth)(image, x, y, r * (0.92 if which == 0 else 1), t)
                d.text((x, h * 0.79), names[which], font=self.f(12, True), fill=colors[which], anchor='mm')
            if preset == 'Dyson':
                x, y = centers[1]
                for i in range(80):
                    a = i * TAU / 80 + t * 0.08
                    px = x + math.cos(a) * r * 1.35
                    py = y + math.sin(a) * r * 0.5
                    d.rectangle((px - 2, py - 1, px + 2, py + 1), fill=(211, 174, 91))
            for birth, which, angle, strength in self.pulses:
                age = clock - birth
                if not 0 <= age <= 1.4 or which not in active:
                    continue
                x, y = centers[which]
                color = colors[which]
                fade = max(0, 1 - age / 1.4)
                rr = r * (0.95 + age * 0.6)
                arc_angle = math.degrees(angle)
                d.arc((x - rr, y - rr, x + rr, y + rr), arc_angle - 14, arc_angle + 25, fill=tuple((int(c * fade) for c in color)), width=2)
                for k in range(5):
                    a = angle + (k - 2) * 0.055
                    reach = r * (1 + age * (0.6 + k * 0.08))
                    px = x + math.cos(a) * reach
                    py = y + math.sin(a) * reach
                    d.ellipse((px - 1, py - 1, px + 1, py + 1), fill=tuple((int(c * fade) for c in color)))
                if which == 1:
                    points = []
                    for j in range(24):
                        u = j / 23
                        a = angle + (u - 0.5) * 0.34
                        rr = r * (1 + math.sin(u * math.pi) * (0.16 + 0.38 * fade))
                        points.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
                    d.line(points, fill=mix((84, 24, 6), (255, 217, 139), fade), width=2)
        for stamp, source in list(bus_events)[-12:]:
            age = clock - stamp
            if 0 <= age < 1.5:
                rr = 12 + age * min(w, h) * 0.34
                fade = 1 - age / 1.5
                color = CYAN if source != 'hydrogen' else (80, 158, 238)
                d.ellipse((w * 0.5 - rr, h * 0.47 - rr, w * 0.5 + rr, h * 0.47 + rr), outline=tuple((int(c * fade * 0.55) for c in color)), width=1)
        y = h - 43
        d.line((24, y, w - 24, y), fill=(20, 45, 58))
        wave = []
        for x in range(24, w - 24, 4):
            sample = clock - (w - 24 - x) / max(1, w - 48) * 3
            amplitude = 2
            for birth, _, _, strength in self.pulses:
                age = sample - birth
                if 0 <= age < 0.65:
                    amplitude += strength * 18 * math.exp(-age * 8) * math.sin(age * TAU * 9)
            wave.append((x, y - amplitude))
        d.line(wave, fill=(201, 154, 73), width=1)
        for birth, _, _, _ in self.pulses:
            age = clock - birth
            if 0 <= age < 3:
                x = w - 24 - age / 3 * (w - 48)
                d.line((x, y - 17, x, y - 12), fill=GOLD)
        d.rectangle((0, 0, w, 39), fill=(5, 15, 24))
        d.text((19, 18), 'HYDROGEN  /  ' + ('DIGITAL FLUX MATRIX' if preset == 'Matrix' else preset.upper() + ' FIELD'), font=self.f(12, True), fill=(157, 192, 203), anchor='lm')
        d.text((w - 19, 18), f'{len(bits):,} sampled bits  ·  {self.pulse_count} visual pulses', font=self.f(11, True), fill=(73, 180, 164), anchor='rm')
        d.text((24, h - 13), 'STOCHASTIC VISUAL PULSES', font=self.f(10, True), fill=(192, 160, 99), anchor='lm')
        d.text((w - 24, h - 13), 'CYAN = RECEIVED BUS EVENTS  /  ILLUSTRATIVE MODELS', font=self.f(9, True), fill=(76, 124, 141), anchor='rm')
        if pointer and preset == 'Matrix':
            px = pointer[0] * w / max(1, width)
            py = pointer[1] * h / max(1, height)
            g = self.last_geometry
            col = int((px - g['left']) // g['cell'])
            row = int((py - g['top']) // (g['cell'] + 3))
            index = row * g['cols'] + col
            if 0 <= col < g['cols'] and 0 <= row < g['rows'] and (index < len(bits)):
                d.text((24, 44), f'BIT [{index}] = {bits[index]}', font=self.f(11, True), fill=GOLD)
        if (w, h) != (width, height):
            image = image.resize((max(1, width), max(1, height)), Image.Resampling.BILINEAR)
        self.last_ms = (time.perf_counter() - started) * 1000
        self.last_size = (width, height)
        return image
