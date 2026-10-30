"""Рисует иконку приложения 1024x1024 тем же кодом, что и превью.

    python tools/make_icon.py
Out: Caterpillar/App/Assets.xcassets/AppIcon.appiconset/AppIcon1024.png
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preview import Scene, bokeh_bg  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Caterpillar", "App", "Assets.xcassets", "AppIcon.appiconset",
                   "AppIcon1024.png")


def main():
    size = 1024
    k = 22.0
    head_cy_units = 21.5
    head_screen_y = size * 0.40
    ox = size * 0.5
    oy = head_screen_y - head_cy_units * k

    bg = bokeh_bg((size, size)).convert("RGBA")

    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sc = Scene(layer, (ox, oy), k)
    phase = 0.343  # так, чтобы корпус стоял ровно по центру
    sc.draw_body(phase, 0.0)
    sc.draw_head(phase, 0.0, blink=0.0)
    sc.draw_cigarette(phase, 0.0, ember=1.0)
    sc.draw_smoke(phase, 0.0, 0.55, 1.0)
    sc.draw_smoke(phase, 0.0, 0.86, 0.9)

    # лёгкая виньетка, чтобы иконка не сливалась с фоном
    vignette = Image.new("L", (size, size), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-size * 0.25, -size * 0.25, size * 1.25, size * 1.25], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(size * 0.12))
    dark = Image.new("RGB", (size, size), (18, 30, 10))
    bg = Image.composite(bg.convert("RGB"), dark, vignette).convert("RGBA")

    bg.alpha_composite(layer)
    img = bg.convert("RGB")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG")
    print("written:", OUT, img.size, img.mode)


if __name__ == "__main__":
    main()
