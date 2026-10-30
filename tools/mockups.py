"""Мокапы для README и для проверки композиции на реальных размерах.

    python tools/mockups.py
Out: preview/app-screen.png, preview/widget-only.png, preview/home-screen.png
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preview import Scene, bokeh_bg, draw_caterpillar  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "preview")

BOLD = "C:/Windows/Fonts/segoeuib.ttf"
SEMI = "C:/Windows/Fonts/segoeuisl.ttf"
REG = "C:/Windows/Fonts/segoeui.ttf"

WHITE = (255, 255, 255, 255)


def font(path, size):
    return ImageFont.truetype(path, size)


def text(draw, xy, s, f, fill=WHITE, anchor="la"):
    draw.text(xy, s, font=f, fill=fill, anchor=anchor)


def rounded(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                           radius=radius, fill=255)
    return mask


def with_alpha(img: Image.Image, alpha: int) -> Image.Image:
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def shadow_rect(size, radius, blur, offset, opacity=120):
    """Мягкая тень под скруглённым прямоугольником."""
    pad = blur * 3
    canvas = Image.new("RGBA", (size[0] + pad * 2, size[1] + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([pad, pad + offset, pad + size[0], pad + size[1] + offset],
                        radius=radius, fill=(0, 0, 0, opacity))
    return canvas.filter(ImageFilter.GaussianBlur(blur))


def widget_image(width, height, phase=0.12, smoking=True, travel=0.0, h_align=0.30):
    bg = bokeh_bg((width, height)).convert("RGBA")
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    k = height * 0.98 / 112.0
    sc = Scene(layer, (width * (h_align + travel), height * 0.018), k)
    draw_caterpillar(sc, phase, 0.35, smoking, 1.0, branch_width=width / k + 40)
    bg.alpha_composite(layer)
    return bg


def status_bar(draw, w, scale=3, dark=False):
    col = (255, 255, 255, 235) if not dark else (20, 20, 20, 235)
    f = font(BOLD, 17 * scale)
    text(draw, (int(w * 0.11), int(46 * scale / 3 * 3 / 3 * 3)), "", f)
    # время
    draw.text((w * 0.09, 20 * scale), "9:41", font=f, fill=col)
    # батарейка / сеть
    x = w * 0.82
    y = 24 * scale
    draw.rounded_rectangle([x, y, x + 26 * scale, y + 12 * scale],
                           radius=3 * scale, outline=col, width=int(1.6 * scale))
    draw.rounded_rectangle([x + 2 * scale, y + 2 * scale,
                            x + 20 * scale, y + 10 * scale],
                           radius=2 * scale, fill=col)
    for i in range(4):
        h = (4 + i * 3) * scale
        draw.rounded_rectangle([x - (26 - i * 6) * scale, y + 12 * scale - h,
                                x - (22 - i * 6) * scale, y + 12 * scale],
                               radius=1.5 * scale, fill=col)


def make_widget_only():
    W, H = 1092, 510
    img = widget_image(W, H, phase=0.12, smoking=True, h_align=0.42)
    mask = rounded((W, H), 64)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    shadow = shadow_rect((W, H), 64, 40, 18, 150)
    canvas = Image.new("RGBA", (W + 240, H + 240), (26, 38, 18, 255))
    canvas.alpha_composite(shadow, (0, 0))
    canvas.alpha_composite(out, (120, 120))
    canvas.convert("RGB").save(os.path.join(OUT, "widget-only.png"))


def make_app_screen():
    W, H = 1179, 2556
    scale = 3
    bg = bokeh_bg((W, H)).convert("RGBA")
    dark = Image.new("RGBA", (W, H), (10, 16, 6, 110))
    bg.alpha_composite(dark)

    d = ImageDraw.Draw(bg)
    status_bar(d, W, scale)

    # заголовок
    f_title = font(BOLD, 40 * scale)
    f_sub = font(SEMI, 14 * scale)
    d.text((W / 2, 170), "Гусеница", font=f_title, fill=WHITE, anchor="ma")
    d.text((W / 2, 316), "ползёт · иногда курит", font=f_sub,
           fill=(255, 255, 255, 170), anchor="ma")

    # карточка со сценой
    cw, ch = W - 120, 1020
    cx, cy = 60, 410
    card = widget_image(cw, ch, phase=0.15, smoking=True, h_align=0.42)
    bg.alpha_composite(shadow_rect((cw, ch), 78, 40, 24, 150), (cx - 120, cy - 120))
    bg.paste(card, (cx, cy), rounded((cw, ch), 78))
    d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=78,
                        outline=(255, 255, 255, 40), width=2)

    # памятка
    hy = cy + ch + 42
    hh = 300
    glass = Image.new("RGBA", (cw, hh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.rounded_rectangle([0, 0, cw - 1, hh - 1], radius=54, fill=(255, 255, 255, 18))
    gd.rounded_rectangle([0, 0, cw - 1, hh - 1], radius=54,
                         outline=(255, 255, 255, 26), width=2)
    bg.alpha_composite(glass, (cx, hy))

    f_h1 = font(BOLD, 14 * scale)
    f_h2 = font(REG, 13 * scale)
    d.text((cx + 42, hy + 40), "Виджет 2×4 на рабочий стол", font=f_h1,
           fill=(255, 255, 255, 235))
    d.text((cx + 42, hy + 100),
           "Зажми пустое место на рабочем столе → «+» →\nнайди «Гусеница» → выбери средний виджет.",
           font=f_h2, fill=(255, 255, 255, 150), spacing=14)

    # кнопка
    by = hy + hh + 42
    bh = 132
    d.rounded_rectangle([cx, by, cx + cw, by + bh], radius=bh // 2,
                        fill=(199, 219, 140, 255))
    d.text((W / 2, by + bh / 2 - 4), "Затянуться", font=font(BOLD, 16 * scale),
           fill=(20, 24, 14, 255), anchor="mm")

    # домашний индикатор
    d.rounded_rectangle([W / 2 - 130, H - 30, W / 2 + 130, H - 20], radius=5,
                        fill=(255, 255, 255, 200))

    bg.convert("RGB").save(os.path.join(OUT, "app-screen.png"))


def make_home_screen():
    W, H = 1179, 2556
    scale = 3
    bg = bokeh_bg((W, H)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (W, H), (8, 14, 4, 120)))

    # домашний экран: иконки + виджет
    icon = 212
    gap = 54
    x0 = 84
    y0 = 300
    palette = [(64, 92, 48), (84, 108, 60), (56, 74, 44), (96, 118, 66)]
    for i in range(4):
        x = x0 + i * (icon + gap)
        bg.alpha_composite(shadow_rect((icon, icon), 56, 20, 10, 110), (x - 60, y0 - 60))
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle([x, y0, x + icon, y0 + icon], radius=56,
                            fill=palette[i] + (255,))

    # виджет 2x4
    wx, wy = 60, 700
    ww, wh = W - 120, 500
    widget = widget_image(ww, wh, phase=0.12, smoking=True, h_align=0.30)
    bg.alpha_composite(shadow_rect((ww, wh), 64, 34, 16, 150), (wx - 100, wy - 100))
    bg.paste(widget, (wx, wy), rounded((ww, wh), 64))

    # ещё ряд иконок
    y1 = wy + wh + 90
    for i in range(4):
        x = x0 + i * (icon + gap)
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle([x, y1, x + icon, y1 + icon], radius=56,
                            fill=palette[(i + 2) % 4] + (255,))

    # док
    dock_y = H - 300
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle([60, dock_y, W - 60, dock_y + 250], radius=80,
                        fill=(255, 255, 255, 46))
    for i in range(4):
        x = 110 + i * (icon + 54)
        d.rounded_rectangle([x, dock_y + 34, x + icon, dock_y + 34 + icon], radius=52,
                            fill=palette[i] + (255,))

    d.rounded_rectangle([W / 2 - 130, H - 30, W / 2 + 130, H - 20], radius=5,
                        fill=(255, 255, 255, 200))

    bg.convert("RGB").save(os.path.join(OUT, "home-screen.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    make_widget_only()
    make_app_screen()
    make_home_screen()
    print("ok", OUT)


if __name__ == "__main__":
    main()
