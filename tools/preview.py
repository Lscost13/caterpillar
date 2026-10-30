"""Dev-only preview renderer.

Draws the caterpillar with the same geometry that the SwiftUI Canvas code uses,
so the look can be iterated cheaply on Windows before committing it to Swift.

Run:  python tools/preview.py
Out:  preview/frames.png, preview/hero.png, preview/widget-*.png
"""

from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------- palette
BODY_DARK = (104, 122, 88)
BODY = (150, 168, 130)
BODY_HI = (206, 215, 176)
BELLY = (172, 186, 148)
EDGE = (60, 71, 48)
FOOT = (44, 51, 36)
EYE_WHITE = (238, 244, 232)
IRIS = (124, 182, 204)
IRIS_D = (66, 122, 146)
PUPIL = (20, 25, 31)
BROW = (50, 59, 40)
MOUTH = (38, 44, 33)
CIG = (244, 242, 233)
CIG_FILTER = (226, 199, 152)
EMBER = (233, 137, 56)
SMOKE = (236, 242, 232)
BRANCH = (104, 82, 56)
BRANCH_HI = (146, 120, 86)
BRANCH_LO = (62, 48, 32)

# ---------------------------------------------------------------- geometry
BASE_Y = 101.0         # feet line == branch surface, local units
BODY_H = 84.0          # feet -> crown of the head
HEAD_CY = 21.5         # head centre, absolute local y
HEAD_W = 23.0
HEAD_H = 36.0
BODY_TOP_S = 0.780     # where the neck disappears behind the head
SEGMENTS = [(0.00, 5.4), (0.06, 8.2), (0.12, 9.3), (0.20, 10.1),
            (0.28, 10.5), (0.36, 10.4), (0.44, 10.0), (0.52, 9.2),
            (0.60, 8.4), (0.68, 7.6), (0.78, 7.2)]


def radius(s: float) -> float:
    pts = SEGMENTS
    if s <= pts[0][0]:
        return pts[0][1]
    if s >= pts[-1][0]:
        return pts[-1][1]
    for (s0, r0), (s1, r1) in zip(pts, pts[1:]):
        if s0 <= s <= s1:
            k = (s - s0) / (s1 - s0)
            k = k * k * (3 - 2 * k)          # smoothstep
            return r0 + (r1 - r0) * k
    return pts[-1][1]


def sway(s: float, phase: float, lean: float) -> float:
    amp = 0.9 + 2.4 * s
    return amp * math.sin(2 * math.pi * (phase + 0.28 * s)) + lean * 5.0 * s


def tail_bend(s: float) -> float:
    """The lower body curls to the right and lies flat on the branch."""
    t = min(1.0, max(0.0, s) / 0.34)
    return 17.0 * (1.0 - t) ** 2.3


def spine(s: float, phase: float, lean: float) -> tuple[float, float]:
    return sway(s, phase, lean) + tail_bend(s), BASE_Y - BODY_H * s


def head_outline(cx, cy, hw, hh, n=56):
    """Smooth tapered blob: superellipse squashed towards the chin."""
    pts = []
    e = 0.80
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = hw * math.copysign(abs(ca) ** e, ca)
        y = hh * math.copysign(abs(sa) ** e, sa)
        t = (y + hh) / (2 * hh)              # 0 chin -> 1 crown
        f = 0.80 + 0.20 * t ** 0.7
        pts.append((cx + x * f, cy + y))
    return pts


class Scene:
    """Draws into a PIL image using a local 40x100 unit box mapped by `k`."""

    def __init__(self, img: Image.Image, box, k: float):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.ox, self.oy = box
        self.k = k

    def P(self, x, y):
        return (self.ox + x * self.k, self.oy + y * self.k)

    # ------------------------------------------------------------ helpers
    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=1.0):
        x0, y0 = self.P(cx - rx, cy - ry)
        x1, y1 = self.P(cx + rx, cy + ry)
        self.d.ellipse([x0, y0, x1, y1], fill=fill, outline=outline,
                       width=max(1, int(width * self.k)))

    def circle(self, cx, cy, r, fill):
        self.ellipse(cx, cy, r, r, fill=fill)

    def poly(self, pts, fill=None, outline=None, width=1.0):
        pp = [self.P(x, y) for x, y in pts]
        if fill:
            self.d.polygon(pp, fill=fill)
        if outline:
            self.d.line(pp + [pp[0]], fill=outline, width=max(1, int(width * self.k)),
                        joint="curve")

    def soft_poly(self, pts, fill, alpha):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.polygon([self.P(x, y) for x, y in pts], fill=fill + (alpha,))
        layer = layer.filter(ImageFilter.GaussianBlur(self.k * 1.6))
        self.img.alpha_composite(layer)

    def line(self, p0, p1, fill, width):
        self.d.line([self.P(*p0), self.P(*p1)], fill=fill,
                    width=max(1, int(width * self.k)))

    def capsule(self, p0, p1, r, fill):
        self.d.line([self.P(*p0), self.P(*p1)], fill=fill,
                    width=max(1, int(2 * r * self.k)))
        self.circle(p0[0], p0[1], r, fill)
        self.circle(p1[0], p1[1], r, fill)

    # ------------------------------------------------------------ pieces
    def draw_branch(self, width=200.0):
        top = BASE_Y + 0.6
        self.d.rectangle([self.P(-400, top)[0], self.P(0, top)[1],
                          self.P(width, 140)[0], self.P(0, 140)[1]], fill=BRANCH)
        self.d.rectangle([self.P(-400, top)[0], self.P(0, top)[1],
                          self.P(width, top + 1.4)[0], self.P(0, top + 1.4)[1]],
                         fill=BRANCH_HI)
        for i in range(80):
            x = -120 + i * 7.5
            y = top + 5 + (i * 37 % 16)
            self.line((x, y), (x + 13, y + 0.5), BRANCH_LO, 0.6)

    def draw_tail(self, phase, lean):
        """Tapered tail lying on the branch, pointing right."""
        cx, cy = spine(0.0, phase, lean)
        ctrl = (cx + 9.0, cy + 0.4)
        end = (cx + 17.0, cy + 1.2)
        pts = []
        for i in range(13):
            t = i / 12
            x = (1 - t) ** 2 * (cx + 1.0) + 2 * (1 - t) * t * ctrl[0] + t * t * end[0]
            y = (1 - t) ** 2 * (cy + 0.5) + 2 * (1 - t) * t * ctrl[1] + t * t * end[1]
            pts.append((x, y, 4.3 * (1 - t) ** 0.75 + 1.3))
        for i in range(len(pts) - 1):
            self.capsule(pts[i][:2], pts[i + 1][:2], pts[i][2] * 0.9, BODY)
        for x, y, r in pts:
            self.circle(x, y, r * 0.92, BODY)
        for dx, dy in [(4.5, 1.6), (9.5, 2.2), (13.8, 2.4)]:
            self.capsule((cx + dx, cy + dy + 3.0), (cx + dx + 1.2, cy + dy + 4.3), 0.8, FOOT)

    def body_path(self, phase, lean):
        """Closed outline of the body, with a rounded cap at the bottom."""
        n = 34
        left, right = [], []
        for i in range(n + 1):
            s = (BODY_TOP_S) * i / n
            cx, cy = spine(s, phase, lean)
            r = radius(s)
            left.append((cx - r, cy))
            right.append((cx + r, cy))
        bx, by = spine(0.0, phase, lean)
        rb = radius(0.0)
        cap = []
        for i in range(1, 12):
            a = math.pi - math.pi * i / 12     # right -> bottom -> left
            cap.append((bx - rb * math.cos(a), by + rb * math.sin(a)))
        return left + right[::-1] + cap

    def draw_body(self, phase, lean):
        left, right = [], []
        n = 34
        for i in range(n + 1):
            s = (BODY_TOP_S) * i / n
            cx, cy = spine(s, phase, lean)
            r = radius(s)
            left.append((cx - r, cy))
            right.append((cx + r, cy))

        path = self.body_path(phase, lean)
        self.poly(path, fill=BODY, outline=EDGE, width=0.85)

        # belly / underside highlight
        left, right = [], []
        for i in range(n + 1):
            s = 0.05 + (0.50 - 0.05) * i / n
            cx, cy = spine(s, phase, lean)
            r = radius(s) * 0.44
            left.append((cx - r, cy))
            right.append((cx + r, cy))
        self.poly(left + right[::-1], fill=BELLY)

        # segment creases
        for s in (0.09, 0.17, 0.25, 0.33, 0.41, 0.49):
            cx, cy = spine(s, phase, lean)
            r = radius(s)
            self.line((cx - r * 0.84, cy + 1.1), (cx + r * 0.84, cy - 0.4), BODY_DARK, 1.0)

        # feet: short dark prolegs, lifting with the crawl cycle
        for i, s in enumerate((0.08, 0.16, 0.24, 0.32, 0.40, 0.48)):
            cx, cy = spine(s, phase, lean)
            r = radius(s)
            lift = 1.4 * math.sin(2 * math.pi * (phase * 2 + i * 0.18))
            for side in (-1, 1):
                x = cx + side * (r * 0.95)
                tip = (x + side * 2.5, cy + 1.1 + lift * 0.3)
                self.capsule((x, cy), tip, 0.95, FOOT)


    def head_center(self, phase, lean):
        cx, _ = spine(BODY_TOP_S, phase, lean)
        return cx, HEAD_CY

    def draw_head(self, phase, lean, blink=0.0, head_turn=0.0):
        cx, cy = self.head_center(phase, lean)
        hw, hh = HEAD_W / 2, HEAD_H / 2
        cx += head_turn * 1.8

        # neck
        nx, ny = spine(BODY_TOP_S - 0.03, phase, lean)
        self.capsule((nx, ny), (cx, cy + hh * 0.62), 5.6, BODY)

        skull = head_outline(cx, cy, hw, hh)
        self.poly(skull, fill=BODY, outline=EDGE, width=0.95)

        # soft cheek highlight
        self.soft_poly([(cx - hw * 0.46, cy + hh * 0.62), (cx - hw * 0.58, cy - hh * 0.10),
                        (cx - hw * 0.20, cy - hh * 0.80), (cx - hw * 0.04, cy + hh * 0.55)],
                       BODY_HI, 120)

        # brow ridge: thick, angled down towards the nose
        for side in (-1, 1):
            ax, ay = cx + side * hw * 0.12, cy - hh * 0.30
            bx, by = cx + side * hw * 0.66, cy - hh * 0.56
            nxv, nyv = (by - ay), -(bx - ax)
            ln = math.hypot(nxv, nyv) or 1.0
            nxv, nyv = nxv / ln, nyv / ln
            ta, tb = 1.6, 2.7
            self.poly([(ax + nxv * ta, ay + nyv * ta), (bx + nxv * tb, by + nyv * tb),
                       (bx - nxv * tb, by - nyv * tb), (ax - nxv * ta, ay - nyv * ta)],
                      fill=BROW)
        # furrow
        self.line((cx, cy - hh * 0.50), (cx, cy - hh * 0.24), BROW, 1.2)

        # eyes
        er = hw * 0.350
        for side in (-1, 1):
            ex = cx + side * hw * 0.44
            ey = cy - hh * 0.06
            self.circle(ex, ey, er, EYE_WHITE)
            self.circle(ex, ey, er - 0.3, None)
            self.ellipse(ex, ey, er, er, outline=EDGE, width=0.55)
            ix = ex + side * er * 0.06
            iy = ey + er * 0.02
            self.circle(ix, iy, er * 0.74, IRIS)
            self.circle(ix, iy, er * 0.48, IRIS_D)
            self.circle(ix, iy + er * 0.02, er * 0.34, PUPIL)
            self.circle(ix - er * 0.24, iy - er * 0.30, er * 0.14, (255, 255, 255))
            if blink > 0.2:
                self.ellipse(ex, ey - er * 0.25, er * 1.06, er * (0.9 - 0.55 * blink), fill=BODY)
                self.line((ex - er, ey), (ex + er, ey), BROW, 1.2)

        # mouth
        my = cy + hh * 0.52
        self.d.line([self.P(cx - hw * 0.58, my - 1.6), self.P(cx - hw * 0.02, my - 0.2),
                     self.P(cx + hw * 0.46, my + 1.2)], fill=MOUTH,
                    width=max(1, int(1.15 * self.k)), joint="curve")

    def cig_tip(self, phase, lean):
        cx, cy = self.head_center(phase, lean)
        hw, hh = HEAD_W / 2, HEAD_H / 2
        base = (cx + hw * 0.44, cy + hh * 0.56)
        return base, (base[0] + 9.6, base[1] - 3.8)

    def draw_cigarette(self, phase, lean, ember=1.0):
        base, tip = self.cig_tip(phase, lean)
        self.line(base, tip, CIG, 2.3)
        self.line(base, (base[0] + (tip[0] - base[0]) * 0.26,
                         base[1] + (tip[1] - base[1]) * 0.26), CIG_FILTER, 2.3)
        self.circle(tip[0], tip[1], 1.6, CIG_FILTER if ember < 0.3 else EMBER)
        if ember >= 0.3:
            self.circle(tip[0] + 0.6, tip[1] - 0.4, 0.9, (255, 208, 145))

    def draw_smoke(self, phase, lean, t, strength=1.0):
        if strength <= 0.01:
            return
        _, tip = self.cig_tip(phase, lean)
        for i in range(9):
            p = (t + i / 9.0) % 1.0
            r = 1.5 + 11.5 * p
            x = tip[0] + math.sin(p * 5.4 + i * 1.6) * 6.0 * p + 1.4 * p
            y = tip[1] - p * 56.0
            a = strength * (1.0 - p) ** 1.05 * 0.5
            layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            x0, y0 = self.P(x - r, y - r)
            x1, y1 = self.P(x + r, y + r)
            ld.ellipse([x0, y0, x1, y1], fill=SMOKE + (int(255 * a),))
            layer = layer.filter(ImageFilter.GaussianBlur(radius=max(1, r * self.k * 0.45)))
            self.img.alpha_composite(layer)


# ---------------------------------------------------------------- scenes
def draw_caterpillar(sc, phase, t, smoking, strength, blink=0.0, lean=0.0, branch_width=400.0):
    sc.draw_body(phase, lean)
    sc.draw_head(phase, lean, blink=blink)
    sc.draw_cigarette(phase, lean, ember=1.0 if smoking else 0.15)
    sc.draw_branch(width=branch_width)
    if smoking:
        sc.draw_smoke(phase, lean, t, strength)
    return sc


def bokeh_bg(size):
    w, h = size
    img = Image.new("RGB", (w, h), (60, 88, 34))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)],
               fill=(int(56 + 66 * k), int(80 + 48 * k), int(24 + 24 * k)))
    img = img.filter(ImageFilter.GaussianBlur(1))
    blobs = [(-70, -40, 250, 84, (176, 194, 84)), (130, 55, 210, 64, (150, 178, 58)),
             (340, -50, 270, 50, (182, 202, 96)), (30, 260, 230, 44, (158, 182, 72)),
             (280, 265, 250, 36, (150, 174, 64)), (500, 110, 300, 44, (176, 196, 88)),
             (620, 300, 220, 34, (146, 170, 62))]
    for x, y, r, a, col in blobs:
        layer = Image.new("RGB", (w, h), (0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.ellipse([x - r, y - r, x + r, y + r], fill=col)
        layer = layer.filter(ImageFilter.GaussianBlur(r * 0.55))
        mask = layer.convert("L").point(lambda v: int(v * a / 255))
        img = Image.composite(Image.blend(img, layer, 0.6), img, mask)
    return img


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "preview")
    os.makedirs(out, exist_ok=True)

    # hero frame
    W, H = 900, 1080
    hero = bokeh_bg((W, H)).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sc = Scene(layer, (W * 0.14, H * 0.018), H / 112.0)
    draw_caterpillar(sc, 0.14, 0.4, True, 1.0, branch_width=W / (H / 112.0) + 40)
    hero.alpha_composite(layer)
    hero.convert("RGB").save(os.path.join(out, "hero.png"))

    # medium widget mock: 364x170 pt @2x
    W, H = 364 * 2, 170 * 2
    bg = bokeh_bg((W, H)).convert("RGBA")
    k = H * 0.98 / 112.0
    for name, (phase, smoking, travel) in {
        "a": (-0.18, False, 0.0),
        "b": (0.12, True, 0.0),
        "c": (0.40, True, 0.18),
    }.items():
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sc = Scene(layer, (W * (0.30 + travel), H * 0.018), k)
        draw_caterpillar(sc, phase, 0.35, smoking, 1.0, branch_width=W / k + 40)
        comp = bg.copy()
        comp.alpha_composite(layer)
        comp.convert("RGB").save(os.path.join(out, f"widget-{name}.png"))

    # frame sheet: 6 poses
    fw, fh = 300, 640
    sheet = Image.new("RGB", (fw * 6, fh), (60, 86, 32))
    for i in range(6):
        phase = i * 0.17 - 0.34
        smoking = i in (2, 3)
        tile = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        sc = Scene(tile, (fw * 0.12, fh * 0.018), fh / 112.0)
        draw_caterpillar(sc, phase, 0.3 + i * 0.05, smoking, 1.0, branch_width=fw / (fh / 112.0) + 40)
        base = sheet.crop((i * fw, 0, (i + 1) * fw, fh)).convert("RGBA")
        base.alpha_composite(tile)
        sheet.paste(base.convert("RGB"), (i * fw, 0))
    sheet.save(os.path.join(out, "frames.png"))
    print("ok", out)


if __name__ == "__main__":
    main()
