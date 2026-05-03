from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

W, H = 1920, 1080
FONTS = "/Users/songsong/.claude/plugins/cache/anthropic-agent-skills/document-skills/2c7ec5e78b8e/skills/canvas-design/canvas-fonts"

def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)

# ── Palette ────────────────────────────────────────────────────────────────
BG       = (8,  11, 20)
PANEL    = (14, 18, 30)
CARD     = (20, 26, 42)
STEEL    = (130, 148, 172)
STEEL_LT = (185, 200, 220)
CHROME   = (210, 220, 235)
ACCENT   = (48,  148, 255)
ACCENT2  = (110, 200, 255)
AMBER    = (205, 162, 72)
WHITE    = (238, 244, 252)
DIM      = (65,  84, 118)
GRID_C   = (22,  30,  52)
ARM_DARK = (44,  56,  80)
ARM_MID  = (62,  78, 108)
ARM_LT   = (82, 100, 132)
GREEN    = (72, 200, 120)

f_mono   = font("JetBrainsMono-Regular.ttf", 12)
f_mono_b = font("JetBrainsMono-Bold.ttf", 13)
f_title  = font("BigShoulders-Bold.ttf", 60)
f_title2 = font("BigShoulders-Bold.ttf", 42)
f_sub    = font("InstrumentSans-Regular.ttf", 16)
f_sub_b  = font("InstrumentSans-Bold.ttf", 17)
f_tag    = font("Jura-Light.ttf", 13)
f_num    = font("GeistMono-Regular.ttf", 11)
f_big    = font("GeistMono-Bold.ttf", 13)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ══════════════════════════════════════════════════════════
# BACKGROUND
# ══════════════════════════════════════════════════════════
for y in range(H):
    t = y / H
    r = int(8  + 6*t)
    g = int(11 + 8*t)
    b = int(20 + 18*t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Fine grid
for x in range(0, W, 64):
    draw.line([(x, 0), (x, H)], fill=GRID_C)
for y in range(0, H, 64):
    draw.line([(0, y), (W, y)], fill=GRID_C)

# Main canvas border
draw.rectangle([52, 44, W-52, H-44], outline=(32, 44, 72), width=1)
draw.rectangle([54, 46, W-54, H-46], outline=(22, 30, 52), width=1)

# ══════════════════════════════════════════════════════════
# INTERIOR ZONE (left 62% of canvas)
# ══════════════════════════════════════════════════════════
IW = int(W * 0.62)  # interior panel width
draw.rectangle([60, 52, IW, H-52], fill=(11, 15, 26))

# ── Ambient lighting wash (top of cabin) ──────────────────
for i in range(80):
    t = i / 80
    alpha = int(20 * (1-t))
    draw.rectangle([60, 52+i, IW, 52+i+1],
                   fill=(int(20+30*t), int(28+40*t), int(45+60*t)))

# ── Roof lining ───────────────────────────────────────────
roof_pts = [(60, 52), (IW, 52), (IW, 200), (60+60, 200)]
draw.polygon(roof_pts, fill=(16, 22, 38))
draw.line([(60, 200), (IW, 200)], fill=(30, 42, 68), width=1)

# Ambient interior LED strip
for x in range(200, IW - 200, 3):
    intensity = int(40 * math.sin(math.pi * (x-200) / (IW-400))**2)
    draw.rectangle([x, 198, x+2, 202],
                   fill=(intensity//4, intensity//2, intensity))

# ── A-pillar & windshield frame ───────────────────────────
# Left A-pillar
draw.polygon([(60, 52), (140, 52), (200, 460), (60, 460)],
             fill=(18, 24, 40), outline=(30, 42, 65))
# Windshield arc
for i in range(3):
    draw.arc([160-i, 80-i, IW-80+i, 560+i],
             start=195, end=345, fill=(28+i*4, 38+i*4, 62+i*4), width=2)
# Windshield reflective tint bands
for j in range(5):
    y_ = 200 + j * 40
    draw.line([(200, y_), (IW-100, y_-20)],
              fill=(25, 35, 58), width=1)

# ── Dashboard silhouette ──────────────────────────────────
dash_pts = [
    (60,  460), (200, 360), (420, 310), (700, 295),
    (IW-60, 310), (IW-60, 480), (60, 480)
]
draw.polygon(dash_pts, fill=(16, 21, 36), outline=(34, 46, 72), width=1)
# Dash surface highlight
draw.line([(200, 360), (IW-60, 310)], fill=(30, 42, 68), width=2)

# ── Instrument cluster binnacle ───────────────────────────
ic_x1, ic_y1 = 155, 240
ic_x2, ic_y2 = 430, 378
draw.rounded_rectangle([ic_x1, ic_y1, ic_x2, ic_y2],
                        radius=8, fill=(10, 14, 26), outline=(36, 50, 80), width=2)
# Gauges
for gx, label, val in [(220, "220", 68), (355, "0", 12)]:
    # Gauge background
    draw.ellipse([gx-52, ic_y1+14, gx+52, ic_y1+118],
                 fill=(8, 12, 22), outline=(30, 42, 68), width=1)
    # Gauge arc (track)
    draw.arc([gx-44, ic_y1+22, gx+44, ic_y1+110],
             start=210, end=330, fill=(24, 34, 56), width=8)
    # Gauge arc (value)
    end_a = 210 + int(val * 1.2)
    draw.arc([gx-44, ic_y1+22, gx+44, ic_y1+110],
             start=210, end=end_a, fill=ACCENT, width=8)
    draw.text((gx-16, ic_y1+54), label, font=f_mono, fill=STEEL_LT)
    draw.text((gx-12, ic_y1+72), "km/h" if gx < 300 else "rpm×100",
              font=f_num, fill=DIM)
# Digital readout strip
draw.rectangle([ic_x1+8, ic_y2-28, ic_x2-8, ic_y2-6],
               fill=(8, 12, 22))
draw.text((ic_x1+14, ic_y2-25), "RANGE  412 km   TRIP  238.4 km   14:32",
          font=f_num, fill=(80, 110, 160))

# ── MBUX Central screen ───────────────────────────────────
scr_x1, scr_y1 = 460, 195
scr_x2, scr_y2 = IW - 60, 378
draw.rounded_rectangle([scr_x1, scr_y1, scr_x2, scr_y2],
                        radius=10, fill=(6, 10, 20), outline=ACCENT, width=2)
# Screen outer glow
for i in range(8, 0, -1):
    gc = (int(ACCENT[0]*0.12*(i/8)), int(ACCENT[1]*0.12*(i/8)), int(ACCENT[2]*0.22*(i/8)))
    draw.rounded_rectangle([scr_x1-i*2, scr_y1-i*2, scr_x2+i*2, scr_y2+i*2],
                            radius=12, outline=gc, width=1)

# Screen top status bar
draw.rectangle([scr_x1+4, scr_y1+4, scr_x2-4, scr_y1+26],
               fill=(10, 16, 34))
draw.text((scr_x1+12, scr_y1+8),
          "14:32   ▲  Mercedes-Benz   ●  ●  ●   ⚡ 84%   COMAND Online",
          font=f_num, fill=(90, 130, 190))

# Nav map grid
map_x1, map_y1 = scr_x1+6, scr_y1+30
map_x2, map_y2 = scr_x2-6, scr_y2-6
for i in range(10):
    x_ = map_x1 + i * int((map_x2-map_x1)/10)
    draw.line([(x_, map_y1), (x_, map_y2)], fill=(18, 28, 52), width=1)
for i in range(7):
    y_ = map_y1 + i * int((map_y2-map_y1)/7)
    draw.line([(map_x1, y_), (map_x2, y_)], fill=(18, 28, 52), width=1)

# Route polyline
route = [
    (map_x1+20, map_y2-20),
    (map_x1+80, map_y2-80),
    (map_x1+150, map_y2-100),
    (map_x1+220, map_y1+80),
    (map_x1+290, map_y1+60),
    (map_x1+380, map_y1+40),
]
draw.line(route, fill=(40, 100, 220), width=3)
# Road intersections
for rx_, ry_ in route[1:-1]:
    draw.ellipse([rx_-3, ry_-3, rx_+3, ry_+3], fill=(60, 130, 255))

# Touch target — lower-center of screen so arm approaches cleanly from below
TOUCH_X = map_x1 + 160
TOUCH_Y = map_y2 - 55
# Ripple rings
for r_, a_ in [(46, 30), (34, 55), (22, 90)]:
    col = (int(ACCENT[0]*a_/100), int(ACCENT[1]*a_/100), int(ACCENT[2]*a_/100))
    draw.ellipse([TOUCH_X-r_, TOUCH_Y-r_, TOUCH_X+r_, TOUCH_Y+r_],
                 outline=col, width=1)
draw.ellipse([TOUCH_X-14, TOUCH_Y-14, TOUCH_X+14, TOUCH_Y+14],
             fill=(20, 60, 140, 160), outline=ACCENT2, width=2)
draw.ellipse([TOUCH_X-5, TOUCH_Y-5, TOUCH_X+5, TOUCH_Y+5], fill=ACCENT2)

# Location pin
draw.polygon([(TOUCH_X, TOUCH_Y-26), (TOUCH_X-7, TOUCH_Y-36),
              (TOUCH_X+7, TOUCH_Y-36)], fill=AMBER)
draw.ellipse([TOUCH_X-7, TOUCH_Y-40, TOUCH_X+7, TOUCH_Y-26], fill=AMBER)

# Map labels
draw.text((map_x1+8, map_y1+8), "NAV  ·  MUNICH  →  FRANKFURT",
          font=f_num, fill=(60, 90, 150))
draw.text((map_x2-110, map_y2-20), "2h 14min  ·  214 km", font=f_num, fill=(60, 90, 150))

# ── Steering wheel ────────────────────────────────────────
sw_cx, sw_cy, sw_r = 185, 590, 100
# Shadow
draw.ellipse([sw_cx-sw_r-4, sw_cy-sw_r-4, sw_cx+sw_r+4, sw_cy+sw_r+4],
             fill=(10, 14, 24))
# Outer rim
for i in range(4):
    draw.ellipse([sw_cx-sw_r+i, sw_cy-sw_r+i, sw_cx+sw_r-i, sw_cy+sw_r-i],
                 outline=(40+i*8, 52+i*8, 78+i*8), width=1)
draw.ellipse([sw_cx-sw_r, sw_cy-sw_r, sw_cx+sw_r, sw_cy+sw_r],
             outline=STEEL, width=4)
# Grip texture bands
for angle in [20, 60, 100, 200, 240, 280]:
    r1, r2 = sw_r - 14, sw_r - 4
    rad = math.radians(angle)
    x1 = sw_cx + int(r1 * math.cos(rad))
    y1 = sw_cy + int(r1 * math.sin(rad))
    x2 = sw_cx + int(r2 * math.cos(rad))
    y2 = sw_cy + int(r2 * math.sin(rad))
    draw.line([(x1, y1), (x2, y2)], fill=(50, 65, 94), width=2)
# Spokes
for angle in [270, 30, 150]:
    rad = math.radians(angle)
    x1 = sw_cx + int(22 * math.cos(rad))
    y1 = sw_cy + int(22 * math.sin(rad))
    x2 = sw_cx + int((sw_r - 12) * math.cos(rad))
    y2 = sw_cy + int((sw_r - 12) * math.sin(rad))
    draw.line([(x1, y1), (x2, y2)], fill=STEEL, width=5)
# Hub
draw.ellipse([sw_cx-24, sw_cy-24, sw_cx+24, sw_cy+24], fill=(20, 28, 46))
draw.ellipse([sw_cx-22, sw_cy-22, sw_cx+22, sw_cy+22], fill=(16, 22, 38))
# MB star
for ang in [90, 210, 330]:
    rad = math.radians(ang)
    draw.line([(sw_cx, sw_cy),
               (sw_cx + int(16 * math.cos(rad)),
                sw_cy + int(16 * math.sin(rad)))],
              fill=CHROME, width=2)
# Paddle shifters
for side in [-1, 1]:
    px = sw_cx + side * (sw_r + 22)
    draw.rounded_rectangle([px - 14, sw_cy - 30, px + 14, sw_cy + 30],
                            radius=4, fill=(18, 24, 40), outline=STEEL, width=1)

# ── Center console ────────────────────────────────────────
CON_X1, CON_X2 = 360, 640
CON_Y1 = 500
CON_Y2 = H - 55
draw.rectangle([CON_X1, CON_Y1, CON_X2, CON_Y2],
               fill=(14, 18, 32), outline=(36, 50, 80), width=1)
# Console surface sheen
draw.line([(CON_X1+1, CON_Y1), (CON_X2-1, CON_Y1+1)], fill=(50, 68, 100), width=2)

# Armrest
draw.rounded_rectangle([CON_X1+10, CON_Y1+40, CON_X2-10, CON_Y1+160],
                        radius=6, fill=(18, 24, 40), outline=(34, 46, 72))
# Stitching line
draw.line([(CON_X1+22, CON_Y1+100), (CON_X2-22, CON_Y1+100)],
          fill=(28, 38, 62), width=1)

# Rotary knob (COMAND controller)
knob_cx, knob_cy = (CON_X1+CON_X2)//2, CON_Y1 + 220
draw.ellipse([knob_cx-32, knob_cy-32, knob_cx+32, knob_cy+32],
             fill=(20, 26, 44), outline=STEEL, width=2)
draw.ellipse([knob_cx-22, knob_cy-22, knob_cx+22, knob_cy+22],
             fill=(16, 22, 36))
for a_ in range(0, 360, 45):
    rad = math.radians(a_)
    draw.ellipse([knob_cx + int(26*math.cos(rad)) - 2,
                  knob_cy + int(26*math.sin(rad)) - 2,
                  knob_cx + int(26*math.cos(rad)) + 2,
                  knob_cy + int(26*math.sin(rad)) + 2],
                 fill=STEEL)

# USB / charge ports
for px in [CON_X1+30, CON_X2-45]:
    draw.rounded_rectangle([px, CON_Y1+280, px+30, CON_Y1+300],
                            radius=2, fill=(10, 14, 24), outline=DIM)

# ── Passenger side / door panel ───────────────────────────
draw.rectangle([CON_X2+30, 420, IW-65, H-55],
               fill=(12, 16, 28), outline=(28, 38, 62))
# Door pull
draw.rounded_rectangle([CON_X2+50, 540, CON_X2+120, 580],
                        radius=8, fill=(20, 26, 44), outline=STEEL)

# ── Seat silhouette (driver) ──────────────────────────────
seat_x = 200
draw.rounded_rectangle([seat_x-72, 580, seat_x+72, 840],
                        radius=10, fill=(14, 18, 30), outline=(30, 40, 64))
draw.rounded_rectangle([seat_x-82, 840, seat_x+82, 960],
                        radius=6, fill=(14, 18, 30), outline=(30, 40, 64))
draw.rounded_rectangle([seat_x-50, 510, seat_x+50, 584],
                        radius=14, fill=(16, 22, 36), outline=(30, 40, 64))
# Seat stitching
for sy_ in range(620, 830, 50):
    draw.line([(seat_x-55, sy_), (seat_x+55, sy_)], fill=(22, 30, 50), width=1)
# Headrest pillar
draw.rectangle([seat_x-8, 515, seat_x+8, 580], fill=(18, 24, 40))

# ══════════════════════════════════════════════════════════
# ROBOT ARM — 6-axis, mounted on console, reaching to screen
# ══════════════════════════════════════════════════════════
# Base: right edge of center console top
BASE_X = CON_X2 - 30
BASE_Y = CON_Y1 - 6

# Natural 6-DOF arm arc from console base up to lower screen edge
J = [
    (BASE_X,        BASE_Y),           # J0 base mount
    (BASE_X,        BASE_Y - 38),      # J1 rotation base (vertical)
    (BASE_X - 40,   BASE_Y - 120),     # J2 shoulder (pulls left)
    (BASE_X - 20,   BASE_Y - 210),     # J3 upper arm (starts converging)
    (TOUCH_X + 20,  TOUCH_Y + 100),    # J4 forearm (below screen bottom edge)
    (TOUCH_X + 6,   TOUCH_Y + 38),     # J5 wrist (aligning to screen)
    (TOUCH_X,       TOUCH_Y + 4),      # J6 end-effector (screen contact)
]

def draw_link(p1, p2, w=14, fill=ARM_MID, outline=CHROME):
    x1, y1 = p1; x2, y2 = p2
    angle = math.atan2(y2-y1, x2-x1)
    perp = angle + math.pi/2
    ox = w/2 * math.cos(perp)
    oy = w/2 * math.sin(perp)
    pts = [(int(x1+ox), int(y1+oy)), (int(x2+ox), int(y2+oy)),
           (int(x2-ox), int(y2-oy)), (int(x1-ox), int(y1-oy))]
    draw.polygon(pts, fill=fill, outline=outline)

def draw_joint(x, y, r, fill=ARM_DARK, outline=CHROME):
    draw.ellipse([x-r, y-r, x+r, y+r], fill=fill, outline=outline, width=2)
    # Inner ring detail
    draw.ellipse([x-r+4, y-r+4, x+r-4, y+r-4], outline=(60, 78, 108), width=1)

# Base mounting plate
draw.rectangle([J[0][0]-48, J[0][1], J[0][0]+48, J[0][1]+10],
               fill=(50, 64, 92), outline=CHROME, width=1)
draw.rectangle([J[0][0]-36, J[0][1]-16, J[0][0]+36, J[0][1]+2],
               fill=(44, 58, 84), outline=CHROME, width=1)
# Mounting bolts
for bx in [J[0][0]-28, J[0][0]+28]:
    draw.ellipse([bx-4, J[0][1]-4, bx+4, J[0][1]+4], fill=CHROME)

# Link widths: decreasing toward tip
link_styles = [
    (20, ARM_DARK),   # J0-J1 base column
    (18, ARM_MID),    # J1-J2 upper arm
    (16, ARM_MID),    # J2-J3 elbow
    (13, ARM_LT),     # J3-J4 forearm
    (10, ARM_LT),     # J4-J5 wrist
    (7,  (90, 108, 140)),  # J5-J6 end-effector
]
for i, (w_, fill_) in enumerate(link_styles):
    draw_link(J[i], J[i+1], w=w_, fill=fill_)

# Joints (J1..J5, skip base and tip)
joint_r = [0, 22, 20, 18, 15, 12, 0]
joint_c  = [0, ARM_DARK, ARM_DARK, ARM_MID, ARM_LT, ARM_LT, 0]
for i in range(1, 6):
    draw_joint(*J[i], joint_r[i], fill=joint_c[i])
    # Axis marker dot (blue)
    draw.ellipse([J[i][0]-5, J[i][1]-5, J[i][0]+5, J[i][1]+5], fill=ACCENT)

# End-effector finger
fx, fy = J[6]
draw.rounded_rectangle([fx-7, fy-22, fx+7, fy+2],
                        radius=3, fill=(88, 108, 140), outline=CHROME, width=1)
draw.ellipse([fx-5, fy-5, fx+5, fy+5], fill=ACCENT2)
# Fingertip glow
for g_ in range(10, 0, -1):
    gc = (int(ACCENT2[0]*g_//20), int(ACCENT2[1]*g_//12), int(ACCENT2[2]*g_//8))
    draw.ellipse([fx-g_*2, fy-g_*2, fx+g_*2, fy+g_*2], outline=gc, width=1)

# ── Joint annotation leaders ──────────────────────────────
ann_col = (45, 60, 95)
ann_txt = (88, 115, 160)
# Place annotations alternating left/right to avoid overlap
offsets = [
    (-88, -8),   # J1 — left
    (-88, -8),   # J2 — left
    ( 32, -8),   # J3 — right
    ( 32, -8),   # J4 — right
    ( 32, -8),   # J5 — right
]
for i, (dx_, dy_) in enumerate(offsets, 1):
    jx, jy = J[i]
    ex = jx + dx_
    # leader line: small diagonal then horizontal
    mid_x = jx + dx_//2
    draw.line([(jx, jy), (mid_x, jy + dy_), (ex, jy + dy_)],
              fill=ann_col, width=1)
    label = f"J{i:02d}  θ{i}"
    draw.text((ex + (4 if dx_ > 0 else -60), jy + dy_ - 14),
              label, font=f_num, fill=ann_txt)

# Cable bundle (thin lines following arm path)
for offset in [-6, -3, 3, 6]:
    cable_pts = [(J[i][0]+offset, J[i][1]+offset) for i in range(6)]
    draw.line(cable_pts, fill=(28, 38, 60), width=1)

# ══════════════════════════════════════════════════════════
# RIGHT PANEL — Specs + data readout
# ══════════════════════════════════════════════════════════
RX = IW + 24    # right panel x start
RX2 = W - 56

draw.rectangle([RX-6, 52, RX2, H-52], fill=(10, 14, 24))
draw.rectangle([RX-6, 52, RX-4, H-52], fill=ACCENT)

# ── Title ─────────────────────────────────────────────────
ty = 70
draw.text((RX+12, ty), "EMBODIED", font=f_title, fill=WHITE)
ty += 62
draw.text((RX+12, ty), "INTELLIGENCE", font=f_title, fill=ACCENT)
ty += 50
draw.line([(RX+12, ty), (RX2-12, ty)], fill=(35, 50, 82), width=1)
ty += 12
draw.text((RX+12, ty), "IN-CABIN AUTOMATION TESTING SOLUTION", font=f_sub, fill=STEEL)
ty += 22
draw.text((RX+12, ty), "Mercedes-Benz GLC  ·  Embodied AI Division  ·  2026",
          font=f_tag, fill=DIM)
ty += 30
draw.line([(RX+12, ty), (RX2-12, ty)], fill=(35, 50, 82), width=1)
ty += 16

# ── Spec rows ─────────────────────────────────────────────
specs = [
    ("PLATFORM",        "Mercedes-Benz GLC 300e"),
    ("ARM CONFIGURATION","6-DOF Industrial Series"),
    ("PAYLOAD CAPACITY", "3.5 kg  ·  IP54 rated"),
    ("REPEATABILITY",    "+/- 0.02 mm"),
    ("DEGREES OF FREEDOM","6 axes  ·  full wrist"),
    ("AI CONTROLLER",   "Embodied AI Runtime v3.1"),
    ("TEST COVERAGE",   "HMI  ·  OTA  ·  Safety"),
    ("ACTION CYCLE",    "< 0.8 s  per interaction"),
]
for label, value in specs:
    draw.text((RX+12, ty), label, font=f_tag, fill=DIM)
    ty += 17
    draw.text((RX+12, ty), value, font=f_sub_b, fill=STEEL_LT)
    ty += 24
    draw.line([(RX+12, ty), (RX2-12, ty)], fill=(24, 34, 56), width=1)
    ty += 12

ty += 6
draw.text((RX+12, ty), "SYSTEM STATUS", font=f_tag, fill=DIM)
ty += 18
for col, label in [
    (ACCENT,       "ARM ONLINE"),
    (ACCENT,       "VISION CALIBRATED"),
    (GREEN,        "MBUX CONNECTED"),
    (AMBER,        "TEST SEQUENCE ARMED"),
]:
    draw.ellipse([RX+12, ty+1, RX+20, ty+9], fill=col)
    draw.text((RX+26, ty-1), label, font=f_mono, fill=STEEL)
    ty += 20

ty += 14

# ── End-effector position box ─────────────────────────────
draw.rectangle([RX+12, ty, RX2-12, ty+92],
               fill=(8, 12, 22), outline=(36, 52, 86), width=1)
draw.rectangle([RX+12, ty, RX2-12, ty+20], fill=(14, 20, 38))
draw.text((RX+18, ty+4), "END-EFFECTOR  COORDINATE  READOUT",
          font=f_num, fill=DIM)
ty += 22
axes = [
    ("X", f"{TOUCH_X - BASE_X:+.1f} mm"),
    ("Y", f"{TOUCH_Y - BASE_Y:+.1f} mm"),
    ("Z", "+  412.0 mm"),
]
col_w = (RX2 - RX - 24) // 3
for i, (axis, val) in enumerate(axes):
    ax_ = RX + 18 + i * col_w
    draw.text((ax_, ty+4), axis, font=f_big, fill=ACCENT2)
    draw.text((ax_, ty+20), val, font=f_mono, fill=CHROME)
ty += 44
draw.text((RX+18, ty),
          "θ1=+34°  θ2=−12°  θ3=+78°  θ4=−45°  θ5=+22°  θ6=0°",
          font=f_num, fill=(65, 88, 135))
ty += 30

# ── Event log ─────────────────────────────────────────────
draw.text((RX+12, ty), "LIVE TEST LOG", font=f_tag, fill=DIM)
ty += 16
draw.rectangle([RX+12, ty, RX2-12, ty+1], fill=(30, 44, 72))
ty += 8
events = [
    ("[14:32:01.004]", "NAVIGATE_HOME        ", "OK",   ACCENT),
    ("[14:32:01.882]", "ARM_MOVE (452,234)   ", "OK",   ACCENT),
    ("[14:32:02.118]", "TAP_SCREEN           ", "OK",   ACCENT),
    ("[14:32:02.890]", "VERIFY_SCREEN_STATE  ", "PASS", GREEN),
    ("[14:32:03.441]", "TAP_SCREEN (588,191) ", "OK",   ACCENT),
    ("[14:32:04.203]", "ASSERT_UI_ELEMENT    ", "PASS", GREEN),
    ("[14:32:04.889]", "SCREENSHOT_CAPTURE   ", "OK",   ACCENT),
    ("[14:32:05.312]", "CYCLE_COMPLETE       ", "PASS", GREEN),
]
for ts, action, result, rcol in events:
    draw.text((RX+14, ty), ts, font=f_num, fill=(55, 75, 118))
    draw.text((RX+14+112, ty), action, font=f_num, fill=STEEL)
    draw.text((RX2-52, ty), result, font=f_num, fill=rcol)
    ty += 17

ty += 8
draw.line([(RX+12, ty), (RX2-12, ty)], fill=(28, 40, 66), width=1)
ty += 10

# Pass rate bar
draw.text((RX+12, ty), "TEST PASS RATE   98.6 %", font=f_mono_b, fill=STEEL_LT)
ty += 20
bar_w = RX2 - RX - 36
fill_w = int(bar_w * 0.986)
draw.rectangle([RX+12, ty, RX+12+bar_w, ty+8],
               fill=(16, 22, 38), outline=(36, 50, 80))
draw.rectangle([RX+12, ty, RX+12+fill_w, ty+8], fill=GREEN)

# ── Bottom bar ────────────────────────────────────────────
draw.rectangle([60, H-52, W-52, H-50], fill=(30, 45, 80))
draw.rectangle([60, H-50, W-52, H-48], fill=ACCENT)
draw.text((76, H-40), "© 2026  EMBODIED INTELLIGENCE  ·  IN-CABIN AUTOMATION DIVISION",
          font=f_num, fill=DIM)
draw.text((W-340, H-40), "DOC: EI-GLC-HMI-AUT-2026-R01", font=f_num, fill=DIM)

# ── Corner registration marks ─────────────────────────────
for cx_, cy_, dirs in [
    (60, 52, [(1,0),(0,1)]),
    (W-52, 52, [(-1,0),(0,1)]),
    (60, H-52, [(1,0),(0,-1)]),
    (W-52, H-52, [(-1,0),(0,-1)])
]:
    for dx, dy in dirs:
        draw.line([(cx_, cy_), (cx_+dx*22, cy_+dy*22)], fill=(50, 68, 105), width=1)

# ══════════════════════════════════════════════════════════
# VIGNETTE + FINAL TONE
# ══════════════════════════════════════════════════════════
img_rgba = img.convert("RGBA")
vig = Image.new("RGBA", (W, H), (0,0,0,0))
vd = ImageDraw.Draw(vig)
for i in range(150, 0, -1):
    a = int((1 - i/150)**2 * 140)
    vd.rectangle([i, i, W-i, H-i], outline=(0, 0, 0, a), width=2)
img_rgba = Image.alpha_composite(img_rgba, vig)
img_out = img_rgba.convert("RGB")

# Subtle cold tint
tint = Image.new("RGB", (W, H), (0, 4, 14))
img_out = Image.blend(img_out, tint, 0.07)

out = "/Users/songsong/Desktop/claude/embodied-intelligence-test.png"
img_out.save(out, "PNG")
print(f"Saved → {out}")
