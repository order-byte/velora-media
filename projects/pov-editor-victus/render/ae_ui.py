"""Adobe After Effects (Windows 11) screen, drawn at the HP Victus 15 panel's
native 1920x1080.

`build_base()` paints every static pixel once (at 2x, then downsampled for
anti-aliased icons). `draw_frame()` adds what changes while the comp plays:
the viewer image, the blue CTI, timecodes and the green RAM-preview cache line.
"""
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
SS = 2  # supersampling for the static layer

FONT_DIR = "/usr/share/fonts/opentype/inter/"


def font(size, weight="Regular"):
    return ImageFont.truetype(f"{FONT_DIR}Inter-{weight}.otf", size)


# After Effects dark theme
APP_BG = (16, 16, 16)
PANEL = (35, 35, 35)
PANEL_DK = (29, 29, 29)
PANEL_LT = (46, 46, 46)
FIELD = (24, 24, 24)
LINE = (52, 52, 52)
TXT = (196, 196, 196)
TXT_DIM = (138, 138, 138)
TXT_HI = (236, 236, 236)
BLUE = (45, 140, 235)
CTI = (58, 150, 255)
CACHE_GREEN = (63, 196, 84)
AQUA = (92, 160, 168)
AQUA_HI = (126, 190, 198)
SEAFOAM = (122, 160, 122)
YELLOW_FOLDER = (205, 170, 70)

# layout (1x pixels)
TITLE = (0, 32)
MENU = (32, 60)
TOOLS = (60, 100)
TASKBAR_Y = 1032
LEFT = (4, 400)
CENTER = (404, 1512)
RIGHT = (1516, 1916)
COMP_Y = (104, 612)
TL_Y = (616, 1028)

VIEW_Y = (156, 578)
FRAME = (590, 160, 736, 414)  # x, y, w, h of the comp frame inside the viewer

TL_TAB = (616, 642)
TL_TIME = (642, 680)
TL_COLS = (680, 700)
TL_LAYERS = 700
ROW_H = 16
TL_BOTTOM = (1004, 1028)
TG_X0, TG_X1 = 856, 1496  # time graph span for the whole comp

FPS = 30


@dataclass
class Shot:
    name: str
    start: int
    end: int


SHOTS = [
    Shot("MCL_01_cover_front.mp4", 0, 61),
    Shot("MCL_02_taillight_flash.mp4", 61, 71),
    Shot("MCL_03_cover_headlights.mp4", 71, 129),
    Shot("MCL_04_topdown_light.mp4", 129, 156),
    Shot("MCL_05_topdown_glitch.mp4", 156, 188),
    Shot("MCL_06_cover_side_walk.mp4", 188, 239),
    Shot("MCL_07_cover_pull_rear.mp4", 239, 313),
    Shot("MCL_08_gear_shift.mp4", 313, 318),
    Shot("MCL_09_rev_gauge.mp4", 318, 339),
    Shot("MCL_10_road_empty.mp4", 339, 368),
    Shot("MCL_11_pass_blur.mp4", 368, 397),
    Shot("MCL_12_road_approach.mp4", 397, 444),
    Shot("MCL_13_rear_sunset.mp4", 444, 503),
    Shot("MCL_14_wheel_close.mp4", 503, 527),
    Shot("MCL_15_brake_disc.mp4", 527, 615),
    Shot("MCL_16_canyon_road.mp4", 615, 730),
    Shot("MCL_17_roof_pov.mp4", 730, 789),
    Shot("MCL_18_plate_rear.mp4", 789, 853),
    Shot("MCL_19_studio_side.mp4", 853, 956),
]
TOTAL_FRAMES = 956


def timecode(frame):
    s, f = divmod(frame, FPS)
    m, s = divmod(s, 60)
    return f"0:{m:02d}:{s:02d}:{f:02d}"


def frame_x(frame):
    return TG_X0 + (TG_X1 - TG_X0) * frame / TOTAL_FRAMES


class Painter:
    """ImageDraw wrapper that takes 1x coordinates and draws at SS scale."""

    def __init__(self, img, scale):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.s = scale
        self._fonts = {}

    def _f(self, size, weight):
        key = (size, weight)
        if key not in self._fonts:
            self._fonts[key] = font(round(size * self.s), weight)
        return self._fonts[key]

    def sc(self, *v):
        return [round(x * self.s) for x in v]

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1, r=0):
        box = self.sc(x0, y0, x1, y1)
        box[2] -= 1
        box[3] -= 1
        w = max(1, round(width * self.s))
        if r:
            self.d.rounded_rectangle(box, radius=round(r * self.s), fill=fill, outline=outline, width=w)
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=w)

    def line(self, pts, fill, width=1):
        self.d.line(self.sc(*[c for p in pts for c in p]), fill=fill, width=max(1, round(width * self.s)))

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon(self.sc(*[c for p in pts for c in p]), fill=fill, outline=outline)

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        self.d.ellipse(self.sc(x0, y0, x1, y1), fill=fill, outline=outline, width=max(1, round(width * self.s)))

    def arc(self, x0, y0, x1, y1, a0, a1, fill, width=1):
        self.d.arc(self.sc(x0, y0, x1, y1), a0, a1, fill=fill, width=max(1, round(width * self.s)))

    def text(self, x, y, s, size=12, fill=TXT, weight="Regular", anchor="la"):
        self.d.text(self.sc(x, y), s, font=self._f(size, weight), fill=fill, anchor=anchor)

    def text_w(self, s, size=12, weight="Regular"):
        return self.d.textlength(s, font=self._f(size, weight)) / self.s

    def clip_text(self, x, y, s, max_w, size=11, fill=TXT, weight="Regular"):
        while s and self.text_w(s, size, weight) > max_w:
            s = s[:-1]
        self.text(x, y, s, size, fill, weight)


# ---------------------------------------------------------------- icons

def ico_hamburger(p, x, y, c=TXT_DIM):
    for k in range(3):
        p.line([(x, y + k * 3), (x + 8, y + k * 3)], c, 1)


def ico_close(p, x, y, c=TXT_DIM, s=7):
    p.line([(x, y), (x + s, y + s)], c, 1)
    p.line([(x + s, y), (x, y + s)], c, 1)


def ico_tri_right(p, x, y, c=TXT_DIM, s=6):
    p.poly([(x, y), (x + s * 0.8, y + s / 2), (x, y + s)], fill=c)


def ico_tri_down(p, x, y, c=TXT_DIM, s=6):
    p.poly([(x, y), (x + s, y), (x + s / 2, y + s * 0.8)], fill=c)


def ico_eye(p, x, y, c=TXT):
    p.ellipse(x, y + 2, x + 12, y + 9, outline=c, width=1)
    p.ellipse(x + 4, y + 3.5, x + 8, y + 7.5, fill=c)


def ico_speaker(p, x, y, c=TXT):
    p.poly([(x, y + 3), (x + 3, y + 3), (x + 6, y), (x + 6, y + 10), (x + 3, y + 7), (x, y + 7)], fill=c)
    p.arc(x + 4, y + 1, x + 11, y + 9, -50, 50, c, 1)


def ico_film(p, x, y, c=(150, 150, 150)):
    p.rect(x, y, x + 12, y + 10, outline=c, width=1)
    for k in range(3):
        p.rect(x + 1.5 + k * 3.5, y + 1.5, x + 3.5 + k * 3.5, y + 2.8, fill=c)
        p.rect(x + 1.5 + k * 3.5, y + 7.2, x + 3.5 + k * 3.5, y + 8.5, fill=c)


def ico_folder(p, x, y, c=YELLOW_FOLDER):
    p.poly([(x, y + 2), (x + 5, y + 2), (x + 6.5, y + 3.5), (x + 13, y + 3.5), (x + 13, y + 11), (x, y + 11)], fill=c)
    p.rect(x, y + 5, x + 13, y + 11, fill=tuple(min(255, v + 25) for v in c))


def ico_comp(p, x, y):
    p.rect(x, y, x + 13, y + 11, fill=(70, 70, 92), r=1.5)
    p.rect(x + 2, y + 2, x + 11, y + 9, fill=(152, 138, 222))
    p.rect(x + 4, y + 4, x + 9, y + 7, fill=(70, 70, 92))


def ico_audio_file(p, x, y, c=(150, 150, 150)):
    p.rect(x + 1, y, x + 11, y + 12, outline=c, width=1)
    for k, hgt in enumerate((3, 6, 4, 7, 2)):
        p.line([(x + 3 + k * 1.6, y + 6 - hgt / 2), (x + 3 + k * 1.6, y + 6 + hgt / 2)], c, 1)


def ico_magnifier(p, x, y, c=TXT_DIM, s=10):
    p.ellipse(x, y, x + s * 0.7, y + s * 0.7, outline=c, width=1.3)
    p.line([(x + s * 0.6, y + s * 0.6), (x + s, y + s)], c, 1.6)


def ico_lock(p, x, y, c=TXT_DIM):
    p.arc(x + 2, y, x + 8, y + 7, 180, 360, c, 1)
    p.rect(x + 1, y + 4, x + 9, y + 10, outline=c, width=1)


def ico_label_tag(p, x, y, c=TXT_DIM):
    p.poly([(x, y + 2), (x + 7, y + 2), (x + 10, y + 5.5), (x + 7, y + 9), (x, y + 9)], outline=c)


def ico_solo(p, x, y, c=TXT_DIM):
    p.ellipse(x + 2, y + 2, x + 9, y + 9, outline=c, width=1)


def ico_pickwhip(p, x, y, c=TXT_DIM):
    p.ellipse(x, y, x + 10, y + 10, outline=c, width=1)
    p.ellipse(x + 3, y + 3, x + 7, y + 7, outline=c, width=1)


def ico_arrow_tool(p, x, y, c):
    p.poly([(x, y), (x, y + 15), (x + 4, y + 11), (x + 7, y + 17), (x + 9, y + 16), (x + 6.5, y + 10), (x + 11, y + 10)], fill=c)


def ico_hand(p, x, y, c):
    for k in range(4):
        p.rect(x + 1 + k * 3, y + 1 + abs(1.5 - k), x + 3 + k * 3, y + 10, fill=c, r=1)
    p.rect(x + 1, y + 8, x + 13, y + 16, fill=c, r=3)
    p.poly([(x - 2, y + 8), (x, y + 7), (x + 3, y + 11), (x + 2, y + 13)], fill=c)


def ico_zoom(p, x, y, c):
    ico_magnifier(p, x, y, c, 16)


def ico_house(p, x, y, c):
    p.poly([(x, y + 7), (x + 8, y), (x + 16, y + 7)], outline=c)
    p.rect(x + 3, y + 7, x + 13, y + 16, outline=c, width=1.3)
    p.rect(x + 6.5, y + 11, x + 9.5, y + 16, fill=c)


def ico_orbit(p, x, y, c):
    p.ellipse(x, y + 3, x + 16, y + 13, outline=c, width=1.3)
    p.ellipse(x + 5, y, x + 11, y + 16, outline=c, width=1.3)


def ico_pan(p, x, y, c):
    p.line([(x + 8, y), (x + 8, y + 16)], c, 1.3)
    p.line([(x, y + 8), (x + 16, y + 8)], c, 1.3)
    for a, b, q in (((x + 8, y), (x + 5, y + 3), (x + 11, y + 3)), ((x + 8, y + 16), (x + 5, y + 13), (x + 11, y + 13)),
                    ((x, y + 8), (x + 3, y + 5), (x + 3, y + 11)), ((x + 16, y + 8), (x + 13, y + 5), (x + 13, y + 11))):
        p.poly([a, b, q], fill=c)


def ico_dolly(p, x, y, c):
    p.line([(x + 2, y + 14), (x + 14, y + 2)], c, 1.3)
    p.poly([(x + 14, y + 2), (x + 9, y + 3), (x + 13, y + 7)], fill=c)
    p.poly([(x + 2, y + 14), (x + 3, y + 9), (x + 7, y + 13)], fill=c)


def ico_rotate(p, x, y, c):
    p.arc(x, y + 1, x + 16, y + 17, 200, 520, c, 1.4)
    p.poly([(x + 1, y + 5), (x + 6, y + 6), (x + 1, y + 11)], fill=c)


def ico_anchor(p, x, y, c):
    p.rect(x + 1, y + 1, x + 15, y + 15, outline=c, width=1.2)
    p.ellipse(x + 5, y + 5, x + 11, y + 11, outline=c, width=1.2)
    p.line([(x + 8, y + 2), (x + 8, y + 14)], c, 1)
    p.line([(x + 2, y + 8), (x + 14, y + 8)], c, 1)


def ico_rect_tool(p, x, y, c):
    p.rect(x, y + 2, x + 16, y + 14, outline=c, width=1.5)


def ico_pen(p, x, y, c):
    p.poly([(x + 8, y), (x + 14, y + 10), (x + 10, y + 16), (x + 6, y + 16), (x + 2, y + 10)], outline=c)
    p.line([(x + 8, y + 2), (x + 8, y + 9)], c, 1)
    p.ellipse(x + 7, y + 8, x + 9, y + 10, fill=c)


def ico_type(p, x, y, c):
    p.text(x + 1, y - 3, "T", 18, c, "Medium")


def ico_brush(p, x, y, c):
    p.line([(x + 15, y + 1), (x + 6, y + 10)], c, 2.5)
    p.ellipse(x + 1, y + 9, x + 8, y + 16, fill=c)


def ico_stamp(p, x, y, c):
    p.rect(x + 6, y, x + 10, y + 8, fill=c, r=1.5)
    p.rect(x + 1, y + 8, x + 15, y + 12, fill=c, r=1.5)
    p.rect(x + 3, y + 13, x + 13, y + 15, fill=c)


def ico_eraser(p, x, y, c):
    p.poly([(x + 9, y + 1), (x + 16, y + 8), (x + 8, y + 16), (x + 1, y + 9)], outline=c)
    p.poly([(x + 1, y + 9), (x + 5, y + 5), (x + 12, y + 12), (x + 8, y + 16)], fill=c)


def ico_roto(p, x, y, c):
    p.ellipse(x, y + 2, x + 9, y + 11, outline=c, width=1.3)
    p.line([(x + 8, y + 10), (x + 15, y + 16)], c, 2)
    p.ellipse(x + 10, y, x + 16, y + 6, fill=c)


def ico_puppet(p, x, y, c):
    p.ellipse(x + 5, y, x + 11, y + 6, fill=c)
    p.line([(x + 8, y + 6), (x + 8, y + 12)], c, 1.6)
    p.line([(x + 2, y + 8), (x + 14, y + 8)], c, 1.6)
    p.line([(x + 8, y + 12), (x + 4, y + 17)], c, 1.6)
    p.line([(x + 8, y + 12), (x + 12, y + 17)], c, 1.6)


def ae_badge(p, x, y, s):
    """The After Effects app icon: deep purple tile, lilac 'Ae'."""
    p.rect(x, y, x + s, y + s, fill=(0, 0, 91), r=s * 0.22)
    p.text(x + s / 2, y + s / 2 + s * 0.02, "Ae", round(s * 0.52), (153, 153, 255), "SemiBold", anchor="mm")


def pr_badge(p, x, y, s):
    p.rect(x, y, x + s, y + s, fill=(0, 0, 91), r=s * 0.22)
    p.text(x + s / 2, y + s / 2 + s * 0.02, "Pr", round(s * 0.52), (153, 153, 255), "SemiBold", anchor="mm")
    p.rect(x, y, x + s, y + s, outline=(234, 119, 255), width=0.0001, r=s * 0.22)


# ---------------------------------------------------------------- panels

def panel(p, x0, y0, x1, y1, tabs, active=0, focused=False):
    """Panel frame with tab header. tabs: list of (title, bright_part)."""
    p.rect(x0, y0, x1, y1, fill=PANEL, r=3)
    x = x0 + 10
    for i, tab in enumerate(tabs):
        title, extra = tab if isinstance(tab, tuple) else (tab, "")
        col = TXT_HI if i == active else TXT_DIM
        if i == active:
            ico_close(p, x, y0 + 10, TXT_DIM, 6)
            x += 14
        p.text(x, y0 + 7, title, 12, col, "Medium" if i == active else "Regular")
        x += p.text_w(title, 12, "Medium" if i == active else "Regular")
        if extra:
            x += 4
            p.text(x, y0 + 7, extra, 12, col, "Medium")
            x += p.text_w(extra, 12, "Medium")
        if i == active:
            x += 6
            ico_hamburger(p, x, y0 + 10)
            x += 12
        x += 18
    if focused:
        p.rect(x0, y0, x1, y1, outline=BLUE, width=1.5, r=3)


def build_title_menu_tools(p):
    p.rect(0, 0, W, TITLE[1], fill=(31, 31, 31))
    ae_badge(p, 10, 7, 18)
    p.text(38, 9, r"Adobe After Effects 2025 - D:\Projects\McLaren F1\McLaren_F1_Edit.aep *", 12, (205, 205, 205))
    # window controls
    cx = W - 46 * 3
    p.line([(cx + 18, 16), (cx + 28, 16)], (220, 220, 220), 1)
    p.rect(cx + 46 + 18, 11, cx + 46 + 28, 21, outline=(220, 220, 220), width=1)
    ico_close(p, cx + 92 + 18, 11, (220, 220, 220), 10)

    p.rect(0, MENU[0], W, MENU[1], fill=(31, 31, 31))
    x = 12
    for m in ("File", "Edit", "Composition", "Layer", "Effect", "Animation", "View", "Window", "Help"):
        p.text(x, MENU[0] + 6, m, 13, (214, 214, 214))
        x += p.text_w(m, 13) + 19

    p.rect(0, TOOLS[0], W, TOOLS[1], fill=(31, 31, 31))
    y = TOOLS[0] + 12
    c = (190, 190, 190)
    ico_house(p, 14, y, c)
    p.line([(44, y - 2), (44, y + 18)], (60, 60, 60), 1)
    tools = [ico_arrow_tool, ico_hand, ico_zoom, None, ico_orbit, ico_pan, ico_dolly, None, ico_rotate,
             ico_anchor, ico_rect_tool, ico_pen, ico_type, ico_brush, ico_stamp, ico_eraser, ico_roto, ico_puppet]
    x = 58
    for i, t in enumerate(tools):
        if t is None:
            p.line([(x - 4, y - 2), (x - 4, y + 18)], (60, 60, 60), 1)
            x += 8
            continue
        if i == 0:
            p.rect(x - 6, y - 5, x + 20, y + 21, fill=(52, 52, 52), r=3)
            t(p, x + 1, y, BLUE)
        else:
            t(p, x, y, c)
        if t in (ico_orbit, ico_rect_tool, ico_pen, ico_type, ico_brush, ico_puppet):
            p.poly([(x + 18, y + 14), (x + 21, y + 14), (x + 21, y + 17)], fill=(120, 120, 120))
        x += 36
    # snapping
    x += 16
    p.rect(x, y + 2, x + 12, y + 14, outline=(150, 150, 150), width=1, r=2)
    p.line([(x + 2.5, y + 8), (x + 5, y + 11), (x + 10, y + 4)], BLUE, 1.6)
    p.text(x + 20, y + 1, "Snapping", 12, (190, 190, 190))
    # workspaces
    ws = ["Default", "Review", "Learn", "Standard", "Small Screen", "Libraries"]
    x = W - 40
    xs = []
    for name in reversed(ws):
        x -= p.text_w(name, 12) + 26
        xs.append((x, name))
    p.text(W - 32, y, "»", 14, (190, 190, 190))
    for x, name in xs:
        if name == "Default":
            p.text(x, y + 1, name, 12, BLUE, "Medium")
            p.line([(x, y + 19), (x + p.text_w(name, 12, "Medium"), y + 19)], BLUE, 2)
            ico_hamburger(p, x + p.text_w(name, 12, "Medium") + 6, y + 4, BLUE)
        else:
            p.text(x, y + 1, name, 12, (176, 176, 176))
    ico_magnifier(p, xs[-1][0] - 44, y + 1, (190, 190, 190), 14)


def build_project(p):
    x0, x1 = LEFT
    y0, y1 = COMP_Y[0], TL_Y[1]
    panel(p, x0, y0, x1, y1, [("Project", ""), ("Effect Controls", "(none)")])
    # thumbnail + comp info
    p.rect(x0 + 10, y0 + 40, x0 + 106, y0 + 94, fill=(10, 10, 12))
    p.text(x0 + 116, y0 + 40, "McLaren_F1_Edit", 12, TXT_HI, "Medium")
    ico_tri_down(p, x0 + 116 + p.text_w("McLaren_F1_Edit", 12, "Medium") + 6, y0 + 45)
    p.text(x0 + 116, y0 + 58, "1920 x 1080 (1.00)", 11, TXT_DIM)
    p.text(x0 + 116, y0 + 74, "\u0394 0:00:31:26, 30.00 fps", 11, TXT_DIM)
    # search
    p.rect(x0 + 10, y0 + 104, x1 - 10, y0 + 126, fill=FIELD, r=3)
    ico_magnifier(p, x0 + 18, y0 + 110, TXT_DIM, 10)
    # columns
    cy = y0 + 134
    p.rect(x0 + 1, cy, x1 - 1, cy + 20, fill=PANEL_LT)
    cols = [("Name", x0 + 28), ("", x0 + 196), ("Type", x0 + 216), ("Size", x0 + 300), ("Frame R...", x0 + 344)]
    for name, cx in cols:
        if name:
            p.text(cx, cy + 4, name, 11, TXT_DIM)
        p.line([(cx - 6, cy + 3), (cx - 6, cy + 17)], (64, 64, 64), 1)
    ico_label_tag(p, x0 + 196, cy + 5)
    ico_tri_down(p, x0 + 60, cy + 8, TXT_DIM, 5)
    rows = [("folder", "01_FOOTAGE", "Folder", "", "", True, 0)]
    for i, s in enumerate(SHOTS):
        rows.append(("film", s.name, "MPEG", f"{38 + (i * 37) % 160} MB", "30", False, 1))
    rows += [
        ("folder", "02_AUDIO", "Folder", "", "", False, 0),
        ("folder", "03_SFX", "Folder", "", "", False, 0),
        ("folder", "Solids", "Folder", "", "", False, 0),
        ("comp", "McLaren_F1_Edit", "Composition", "", "30", False, 0),
        ("comp", "McLaren_F1_Edit_9x16", "Composition", "", "30", False, 0),
    ]
    y = cy + 24
    for kind, name, typ, size, fr, open_, depth in rows:
        if y > y1 - 46:
            break
        if name == "McLaren_F1_Edit":
            p.rect(x0 + 1, y - 2, x1 - 1, y + 17, fill=(60, 74, 96))
        xi = x0 + 12 + depth * 16
        if kind == "folder":
            (ico_tri_down if open_ else ico_tri_right)(p, xi, y + 4, TXT_DIM, 6)
            ico_folder(p, xi + 12, y + 1)
        elif kind == "film":
            ico_film(p, xi + 12, y + 2)
        else:
            ico_comp(p, xi + 12, y + 2)
        p.clip_text(xi + 32, y + 1, name, x0 + 188 - (xi + 32), 11, TXT)
        p.rect(x0 + 196, y + 3, x0 + 206, y + 13, fill={"folder": (200, 180, 90), "film": AQUA, "comp": (170, 150, 120)}[kind])
        p.text(x0 + 216, y + 1, typ, 11, TXT_DIM)
        p.text(x0 + 300, y + 1, size, 11, TXT_DIM)
        p.text(x0 + 344, y + 1, fr, 11, TXT_DIM)
        y += 20
    # bottom bar
    by = y1 - 28
    p.line([(x0 + 1, by), (x1 - 1, by)], (28, 28, 28), 1)
    for k, ic in enumerate((ico_folder, ico_comp, ico_film)):
        ic(p, x0 + 14 + k * 26, by + 8)
    p.text(x0 + 100, by + 7, "8 bpc", 11, TXT_DIM)
    p.rect(x1 - 26, by + 7, x1 - 15, by + 21, outline=TXT_DIM, width=1)


def build_comp(p):
    x0, x1 = CENTER
    y0, y1 = COMP_Y
    panel(p, x0, y0, x1, y1, [("Composition", "McLaren_F1_Edit"), ("Layer", "(none)"), ("Footage", "(none)")])
    # breadcrumb
    ico_lock(p, x0 + 10, y0 + 33)
    p.rect(x0 + 28, y0 + 30, x0 + 150, y0 + 50, fill=PANEL_LT, r=3)
    p.text(x0 + 36, y0 + 34, "McLaren_F1_Edit", 11, TXT_HI)
    # viewer pasteboard
    p.rect(x0 + 1, VIEW_Y[0], x1 - 1, VIEW_Y[1], fill=(28, 28, 28))
    fx, fy, fw, fh = FRAME
    p.rect(fx - 1, fy - 1, fx + fw + 1, fy + fh + 1, outline=(60, 60, 60), width=1)
    p.rect(fx, fy, fx + fw, fy + fh, fill=(0, 0, 0))
    # bottom viewer controls
    by = VIEW_Y[1] + 8
    x = x0 + 10
    p.rect(x, by, x + 16, by + 16, outline=TXT_DIM, width=1, r=2)
    x += 28
    p.text(x, by + 2, "38.3%", 12, TXT)
    ico_tri_down(p, x + 40, by + 6)
    x += 62
    for _ in range(4):
        p.rect(x, by + 1, x + 15, by + 15, outline=(150, 150, 150), width=1, r=2)
        x += 26
    x += 10
    p.ellipse(x, by + 1, x + 15, by + 15, outline=(150, 150, 150), width=1.2)  # camera snapshot
    p.line([(x + 7.5, by + 4), (x + 7.5, by + 8)], (150, 150, 150), 1.2)
    x += 160  # live timecode is drawn per frame here
    p.text(x, by + 2, "Full", 12, TXT)
    ico_tri_down(p, x + 30, by + 6)
    x += 52
    for _ in range(2):
        p.rect(x, by + 1, x + 15, by + 15, outline=(150, 150, 150), width=1, r=2)
        x += 26
    x += 8
    p.text(x, by + 2, "Active Camera", 12, TXT)
    ico_tri_down(p, x + 86, by + 6)
    x += 112
    p.text(x, by + 2, "1 View", 12, TXT)
    ico_tri_down(p, x + 42, by + 6)
    x += 66
    for _ in range(3):
        p.rect(x, by + 1, x + 15, by + 15, outline=(150, 150, 150), width=1, r=2)
        x += 26
    p.text(x + 6, by + 2, "+0.0", 12, TXT)


COMP_TIME_X = CENTER[0] + 10 + 28 + 62 + 4 * 26 + 10 + 26


def build_timeline(p):
    x0, x1 = CENTER
    y0, y1 = TL_Y
    panel(p, x0, y0, x1, y1, [("McLaren_F1_Edit", ""), ("Render Queue", "")], focused=True)
    p.rect(x0 + 1, TL_TIME[0], x1 - 1, y1 - 1, fill=PANEL)
    # search field and switches row (left)
    p.rect(x0 + 148, TL_TIME[0] + 9, x0 + 300, TL_TIME[0] + 29, fill=FIELD, r=3)
    ico_magnifier(p, x0 + 155, TL_TIME[0] + 14, TXT_DIM, 10)
    x = x0 + 318
    for _ in range(6):
        p.rect(x, TL_TIME[0] + 11, x + 15, TL_TIME[0] + 26, outline=(150, 150, 150), width=1, r=2)
        x += 24
    # time navigator + ruler (right)
    p.rect(TG_X0 - 6, TL_TIME[0] + 2, TG_X1 + 6, TL_TIME[0] + 8, fill=(62, 62, 62), r=3)
    p.rect(TG_X0 - 6, TL_TIME[0] + 1, TG_X0, TL_TIME[0] + 9, fill=(120, 120, 120), r=2)
    p.rect(TG_X1, TL_TIME[0] + 1, TG_X1 + 6, TL_TIME[0] + 9, fill=(120, 120, 120), r=2)
    ry = TL_TIME[0] + 10
    p.rect(TG_X0 - 8, ry, x1 - 10, TL_TIME[1], fill=PANEL_DK)
    for sec in range(0, 32):
        x = frame_x(sec * FPS)
        if sec % 2 == 0:
            p.text(x, ry + 4, f"{sec:02d}s", 10, TXT_DIM, anchor="ma")
            p.line([(x, ry + 18), (x, TL_TIME[1])], (110, 110, 110), 1)
        else:
            p.line([(x, ry + 22), (x, TL_TIME[1])], (90, 90, 90), 1)
        for q in (10, 20):
            xx = frame_x(sec * FPS + q)
            p.line([(xx, ry + 25), (xx, TL_TIME[1])], (72, 72, 72), 1)
    # column headers (left) / work area bar (right)
    cy = TL_COLS[0]
    p.rect(x0 + 1, cy, TG_X0 - 8, TL_COLS[1], fill=PANEL_LT)
    ico_eye(p, x0 + 10, cy + 4, TXT_DIM)
    ico_speaker(p, x0 + 28, cy + 5, TXT_DIM)
    ico_solo(p, x0 + 45, cy + 4)
    ico_lock(p, x0 + 62, cy + 5)
    ico_label_tag(p, x0 + 86, cy + 5)
    p.text(x0 + 108, cy + 4, "#", 11, TXT_DIM)
    p.text(x0 + 142, cy + 4, "Source Name", 11, TXT_DIM)
    sx = x0 + 272
    for g in ("\u2736", "\\", "fx", "", "", ""):
        p.text(sx + 4, cy + 3, g, 11, TXT_DIM)
        if not g:
            p.rect(sx + 3, cy + 6, sx + 12, cy + 15, outline=TXT_DIM, width=1)
        sx += 17
    p.clip_text(x0 + 372, cy + 4, "Parent & Link", 70, 11, TXT_DIM)
    for lx in (x0 + 80, x0 + 100, x0 + 126, x0 + 268, x0 + 366):
        p.line([(lx, cy + 3), (lx, cy + 17)], (66, 66, 66), 1)
    p.rect(TG_X0 - 8, cy, x1 - 10, TL_COLS[1], fill=PANEL_DK)
    p.rect(TG_X0, cy + 4, TG_X1, cy + 15, fill=(78, 78, 78))
    p.rect(TG_X0, cy + 3, TG_X0 + 4, cy + 16, fill=(150, 150, 150))
    p.rect(TG_X1 - 4, cy + 3, TG_X1, cy + 16, fill=(150, 150, 150))
    # layers
    p.rect(TG_X0 - 8, TL_LAYERS, x1 - 10, TL_BOTTOM[0], fill=(30, 30, 30))
    p.line([(TG_X0 - 8, TL_LAYERS), (TG_X0 - 8, TL_BOTTOM[0])], (20, 20, 20), 1)
    for i, s in enumerate(SHOTS):
        y = TL_LAYERS + i * ROW_H
        p.line([(x0 + 1, y + ROW_H - 1), (x1 - 10, y + ROW_H - 1)], (26, 26, 26), 1)
        ico_eye(p, x0 + 10, y + 3, (180, 180, 180))
        ico_speaker(p, x0 + 28, y + 3, (150, 150, 150))
        p.rect(x0 + 87, y + 4, x0 + 96, y + 12, fill=AQUA)
        p.text(x0 + 120, y + 2, str(i + 1), 11, TXT, anchor="ra")
        ico_film(p, x0 + 126, y + 3, (140, 140, 140))
        p.clip_text(x0 + 142, y + 1, s.name, 122, 11, TXT)
        p.text(x0 + 293, y + 1, "/", 11, TXT_DIM)
        if i in (2, 6, 12, 15, 18):
            p.text(x0 + 306, y + 1, "fx", 11, TXT_DIM)
        ico_pickwhip(p, x0 + 372, y + 3, (120, 120, 120))
        p.rect(x0 + 386, y + 1, x0 + 438, y + 15, fill=FIELD, r=2)
        p.text(x0 + 390, y + 2, "None", 11, TXT)
        ico_tri_down(p, x0 + 428, y + 6, TXT_DIM, 5)
        # time bar
        bx0, bx1 = frame_x(s.start), frame_x(s.end)
        p.rect(bx0, y + 2, bx1, y + ROW_H - 2, fill=AQUA)
        p.rect(bx0, y + 2, bx1, y + 4, fill=AQUA_HI)
        p.line([(bx0, y + 2), (bx0, y + ROW_H - 3)], (60, 110, 118), 1)
        p.line([(bx1 - 1, y + 2), (bx1 - 1, y + ROW_H - 3)], (60, 110, 118), 1)
    # vertical scrollbar: 21 layers, 19 visible
    p.rect(x1 - 9, TL_LAYERS + 1, x1 - 3, TL_BOTTOM[0] - 1, fill=(30, 30, 30), r=3)
    p.rect(x1 - 9, TL_LAYERS + 1, x1 - 3, TL_LAYERS + 1 + (TL_BOTTOM[0] - TL_LAYERS) * 19 / 21, fill=(84, 84, 84), r=3)
    # bottom bar
    by = TL_BOTTOM[0]
    p.line([(x0 + 1, by), (x1 - 1, by)], (24, 24, 24), 1)
    for k in range(3):
        p.rect(x0 + 10 + k * 22, by + 6, x0 + 24 + k * 22, by + 18, outline=(140, 140, 140), width=1, r=2)
    p.text(x0 + 84, by + 5, "Frame Render Time", 11, TXT_DIM)
    p.text(x0 + 302, by + 5, "Toggle Switches / Modes", 11, TXT)
    zx = TG_X0 + 140
    p.poly([(zx, by + 16), (zx + 6, by + 8), (zx + 12, by + 16)], fill=(150, 150, 150))
    p.rect(zx + 20, by + 11, zx + 220, by + 13, fill=(90, 90, 90))
    p.ellipse(zx + 22, by + 7, zx + 32, by + 17, fill=(190, 190, 190))
    p.poly([(zx + 228, by + 17), (zx + 236, by + 6), (zx + 244, by + 17)], fill=(150, 150, 150))


def build_right(p):
    x0, x1 = RIGHT
    # Info
    panel(p, x0, 104, x1, 262, [("Info", ""), ("Audio", "")])
    for k, (lab, val) in enumerate((("R :", "18"), ("G :", "19"), ("B :", "22"), ("A :", "255"))):
        p.text(x0 + 16, 140 + k * 18, lab, 12, TXT_DIM)
        p.text(x0 + 52, 140 + k * 18, val, 12, TXT)
    p.text(x0 + 200, 140, "X : 1284", 12, TXT)
    p.text(x0 + 200, 158, "Y : 612", 12, TXT)
    p.line([(x0 + 10, 216), (x1 - 10, 216)], LINE, 1)
    # Preview
    panel(p, x0, 266, x1, 470, [("Preview", "")])
    bx = x0 + 70
    for k in range(5):
        cx = bx + k * 54
        c = (210, 210, 210)
        if k == 0:
            p.rect(cx, 306, cx + 2, 318, fill=c); p.poly([(cx + 12, 306), (cx + 3, 312), (cx + 12, 318)], fill=c)
        elif k == 1:
            p.poly([(cx + 10, 306), (cx + 2, 312), (cx + 10, 318)], fill=c); p.rect(cx + 11, 306, cx + 13, 318, fill=c)
        elif k == 2:
            p.rect(cx, 305, cx + 4, 319, fill=BLUE); p.rect(cx + 8, 305, cx + 12, 319, fill=BLUE)  # pause: playing
        elif k == 3:
            p.rect(cx, 306, cx + 2, 318, fill=c); p.poly([(cx + 3, 306), (cx + 11, 312), (cx + 3, 318)], fill=c)
        else:
            p.poly([(cx, 306), (cx + 9, 312), (cx, 318)], fill=c); p.rect(cx + 10, 306, cx + 12, 318, fill=c)
    lines = [("Shortcut", "Spacebar"), ("Include:", ""), ("", ""), ("Range", "Work Area Extended By Current..."),
             ("Play From", "Range Start"), ("Frame Rate", "(30)       Skip  0      Resolution  Auto")]
    y = 334
    for lab, val in lines:
        if lab == "Include:":
            p.text(x0 + 16, y, lab, 12, TXT_DIM)
            for k in range(3):
                p.rect(x0 + 80 + k * 28, y - 1, x0 + 98 + k * 28, y + 15, fill=(60, 60, 60), r=2)
        elif lab:
            p.text(x0 + 16, y, lab, 12, TXT_DIM)
            p.text(x0 + 100, y, val, 12, TXT)
        y += 21
    # Effects & Presets
    panel(p, x0, 474, x1, 822, [("Effects & Presets", ""), ("Libraries", "")])
    p.rect(x0 + 10, 506, x1 - 10, 528, fill=FIELD, r=3)
    ico_magnifier(p, x0 + 18, 512, TXT_DIM, 10)
    cats = ["* Animation Presets", "3D Channel", "Audio", "Blur & Sharpen", "Boris FX Mocha", "Channel",
            "CINEMA 4D", "Color Correction", "Distort", "Expression Controls", "Generate", "Immersive Video",
            "Keying", "Matte", "Noise & Grain", "Obsolete", "Perspective"]
    for k, cname in enumerate(cats):
        y = 538 + k * 16.5
        ico_tri_right(p, x0 + 14, y + 4, TXT_DIM, 6)
        p.text(x0 + 28, y, cname, 11, TXT)
    # Align
    panel(p, x0, 826, x1, 918, [("Align", "")])
    p.text(x0 + 16, 860, "Align Layers to:", 11, TXT_DIM)
    p.text(x0 + 120, 860, "Selection", 11, TXT)
    for k in range(6):
        p.rect(x0 + 16 + k * 30, 884, x0 + 36 + k * 30, 904, outline=(130, 130, 130), width=1, r=2)
    # Character
    panel(p, x0, 922, x1, TL_Y[1], [("Character", ""), ("Paragraph", "")])
    p.rect(x0 + 12, 956, x1 - 12, 976, fill=FIELD, r=3)
    p.text(x0 + 18, 959, "Montserrat", 11, TXT)
    p.rect(x0 + 12, 984, x0 + 190, 1004, fill=FIELD, r=3)
    p.text(x0 + 18, 987, "Bold", 11, TXT)
    p.text(x0 + 206, 987, "T  72 px", 11, TXT)


def win_logo(p, x, y, s):
    g = s * 0.08
    h = (s - g) / 2
    for i in range(2):
        for j in range(2):
            p.rect(x + i * (h + g), y + j * (h + g), x + i * (h + g) + h, y + j * (h + g) + h, fill=(56, 168, 240))


def build_taskbar(p):
    y0 = TASKBAR_Y
    p.rect(0, y0, W, H, fill=(28, 28, 30))
    p.line([(0, y0), (W, y0)], (48, 48, 50), 1)
    cy = y0 + 24
    # weather widget
    p.ellipse(14, cy - 9, 30, cy + 7, fill=(235, 190, 80))
    p.text(38, cy - 15, "27\u00b0C", 12, (230, 230, 230), "Medium")
    p.text(38, cy + 1, "Haze", 11, (170, 170, 170))
    icons = ["start", "search", "taskview", "explorer", "chrome", "edge", "cc", "ae", "pr", "spotify"]
    x = W / 2 - len(icons) * 44 / 2
    for name in icons:
        cx = x + 22
        if name == "start":
            win_logo(p, cx - 11, cy - 11, 22)
        elif name == "search":
            ico_magnifier(p, cx - 9, cy - 9, (225, 225, 225), 18)
        elif name == "taskview":
            p.rect(cx - 10, cy - 8, cx + 2, cy + 6, outline=(225, 225, 225), width=1.4, r=2)
            p.rect(cx - 3, cy - 4, cx + 10, cy + 9, fill=(28, 28, 30), outline=(225, 225, 225), width=1.4, r=2)
        elif name == "explorer":
            p.poly([(cx - 11, cy - 7), (cx - 3, cy - 7), (cx - 1, cy - 5), (cx + 11, cy - 5), (cx + 11, cy + 9), (cx - 11, cy + 9)], fill=(226, 172, 40))
            p.rect(cx - 11, cy - 2, cx + 11, cy + 9, fill=(250, 205, 80))
        elif name == "chrome":
            p.ellipse(cx - 11, cy - 11, cx + 11, cy + 11, fill=(219, 68, 55))
            p.d.pieslice(p.sc(cx - 11, cy - 11, cx + 11, cy + 11), 90, 210, fill=(15, 157, 88))
            p.d.pieslice(p.sc(cx - 11, cy - 11, cx + 11, cy + 11), -30, 90, fill=(244, 180, 0))
            p.ellipse(cx - 5, cy - 5, cx + 5, cy + 5, fill=(255, 255, 255))
            p.ellipse(cx - 3.8, cy - 3.8, cx + 3.8, cy + 3.8, fill=(66, 133, 244))
        elif name == "edge":
            p.ellipse(cx - 11, cy - 11, cx + 11, cy + 11, fill=(18, 120, 200))
            p.d.pieslice(p.sc(cx - 11, cy - 11, cx + 11, cy + 11), 100, 260, fill=(60, 200, 120))
            p.ellipse(cx - 4, cy - 2, cx + 6, cy + 7, fill=(28, 28, 30))
        elif name == "cc":
            p.rect(cx - 11, cy - 11, cx + 11, cy + 11, fill=(218, 31, 38), r=5)
            p.ellipse(cx - 7, cy - 4, cx + 1, cy + 4, outline=(255, 255, 255), width=1.8)
            p.ellipse(cx - 1, cy - 4, cx + 7, cy + 4, outline=(255, 255, 255), width=1.8)
        elif name == "ae":
            p.rect(cx - 19, cy - 19, cx + 19, cy + 19, fill=(52, 52, 56), r=4)
            ae_badge(p, cx - 11, cy - 11, 22)
            p.rect(cx - 8, cy + 15, cx + 8, cy + 18, fill=(110, 160, 230), r=1.5)
        elif name == "pr":
            pr_badge(p, cx - 11, cy - 11, 22)
            p.rect(cx - 3, cy + 15, cx + 3, cy + 18, fill=(140, 140, 140), r=1.5)
        elif name == "spotify":
            p.ellipse(cx - 11, cy - 11, cx + 11, cy + 11, fill=(30, 215, 96))
            for k in range(3):
                p.arc(cx - 7 + k, cy - 5 + k * 4, cx + 7 - k, cy + 5 + k * 4, 200, 340, (20, 20, 20), 1.8)
        x += 44
    # tray
    tx = W - 270
    p.text(tx, cy - 8, "^", 14, (225, 225, 225))
    p.text(tx + 26, cy - 15, "ENG", 11, (225, 225, 225))
    p.text(tx + 30, cy + 1, "IN", 11, (225, 225, 225))
    wx = tx + 70
    for k in range(3):
        p.arc(wx - 8 + k * 3, cy - 6 + k * 3, wx + 8 - k * 3, cy + 10 - k * 3, 225, 315, (225, 225, 225), 1.5)
    ico_speaker(p, wx + 20, cy - 5, (225, 225, 225))
    p.rect(wx + 44, cy - 5, wx + 64, cy + 5, outline=(225, 225, 225), width=1.2, r=2)
    p.rect(wx + 46, cy - 3, wx + 60, cy + 3, fill=(225, 225, 225))
    p.rect(wx + 64, cy - 2, wx + 66, cy + 2, fill=(225, 225, 225))
    p.text(W - 70, cy - 15, "11:48 PM", 12, (230, 230, 230), anchor="ra")
    p.text(W - 70, cy + 1, "23-10-2026", 12, (230, 230, 230), anchor="ra")
    p.rect(W - 54, cy - 10, W - 34, cy + 10, outline=(200, 200, 200), width=1.2, r=3)
    p.line([(W - 50, cy - 3), (W - 38, cy - 3)], (200, 200, 200), 1)
    p.line([(W - 50, cy + 2), (W - 41, cy + 2)], (200, 200, 200), 1)


def build_base(thumb=None):
    img = Image.new("RGB", (W * SS, H * SS), APP_BG)
    p = Painter(img, SS)
    build_title_menu_tools(p)
    build_project(p)
    build_comp(p)
    build_timeline(p)
    build_right(p)
    build_taskbar(p)
    img = img.resize((W, H), Image.LANCZOS)
    if thumb is not None:
        img.paste(Image.fromarray(thumb).resize((96, 54), Image.LANCZOS), (LEFT[0] + 10, COMP_Y[0] + 40))
    return np.array(img)


class FrameDrawer:
    """Per-frame overlays on top of the static base (1x, RGB numpy)."""

    def __init__(self):
        self.f_tc = font(20, "Medium")
        self.f_small = font(10)
        self.f_ui = font(12)
        self.f_info = font(11)

    def draw(self, base, frame_idx, viewer_rgb):
        img = base.copy()
        fx, fy, fw, fh = FRAME
        img[fy:fy + fh, fx:fx + fw] = viewer_rgb
        x = round(frame_x(frame_idx))
        # green cache line under the work area bar: frames played so far are cached
        img[TL_COLS[1] - 4:TL_COLS[1] - 1, TG_X0:max(TG_X0, x)] = CACHE_GREEN
        # CTI line through ruler, work area and layers
        img[TL_TIME[0] + 26:TL_BOTTOM[0], x:x + 1] = CTI
        pil = Image.fromarray(img)
        d = ImageDraw.Draw(pil)
        hy = TL_TIME[0] + 12
        d.polygon([(x - 5, hy), (x + 6, hy), (x + 6, hy + 9), (x + 0.5, hy + 15), (x - 5, hy + 9)], fill=CTI)
        tc = timecode(frame_idx)
        d.text((CENTER[0] + 10, TL_TIME[0] + 4), tc, font=self.f_tc, fill=CTI)
        d.text((CENTER[0] + 12, TL_TIME[0] + 26), f"{frame_idx:05d} (30.00 fps)", font=self.f_small, fill=TXT_DIM)
        d.text((COMP_TIME_X, VIEW_Y[1] + 10), tc, font=self.f_ui, fill=TXT)
        d.text((CENTER[0] + 196, TL_BOTTOM[0] + 5), f"{9 + (frame_idx * 7) % 6}ms", font=self.f_info, fill=TXT_DIM)
        d.text((RIGHT[0] + 16, 226), "Preview: Playing (Spacebar)", font=self.f_info, fill=TXT)
        d.text((RIGHT[0] + 16, 242), f"{tc}   fps: 30 (Realtime)", font=self.f_info, fill=(120, 200, 120))
        return np.array(pil)
