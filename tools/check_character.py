"""Проверка «характера» виджета: повторяется ли поведение и нет ли рывков.

Повторяет формулы из CaterpillarProvider.animationFrame и проверяет:
  • поза непрерывна (соседние кадры отличаются мало),
  • решения по эпизодам не повторяются,
  • на стыке эпизодов нет скачков (окно smoothstep гасит решение).
"""

import math

FPS = 8.0
EPISODE = 8.0
PER_EPISODE = int(EPISODE * FPS)          # 64 кадра


def hash01(value, salt):
    x = (value & 0xFFFFFFFFFFFFFFFF) & + (0)  # placeholder, ниже честная версия
    x = ((value ^ (salt * 0x9E3779B97F4A7C15)) & 0xFFFFFFFFFFFFFFFF)
    x ^= x >> 33
    x = (x * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    x ^= x >> 29
    return (x % 10000) / 10000


def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def pose(t):
    frame = int(t * FPS)
    episode = frame // PER_EPISODE
    phase = (frame % PER_EPISODE) / PER_EPISODE

    h1 = hash01(episode, 1)
    h2 = hash01(episode, 2)
    h3 = hash01(episode, 3)
    h4 = hash01(episode, 4)

    window = smoothstep(0.10, 0.35, phase) * (1 - smoothstep(0.65, 0.90, phase))

    base_phase = (t / 8.0) % 1.0
    body_phase = base_phase + window * (h1 - 0.5) * 0.30

    drift = 0.55 * math.sin((t / 97.0) * 2 * math.pi) + 0.28 * math.sin((t / 41.0) * 2 * math.pi + 1.7)
    travel = drift + window * (h2 - 0.5) * 0.35

    head_base = math.sin((t / 13.0) * 2 * math.pi + 0.5) * 0.35
    head = head_base + window * (h3 - 0.5) * 1.30

    lean = math.sin((t / 7.0) * 2 * math.pi) * 0.18 + window * (h4 - 0.5) * 0.30

    blink_at = int(hash01(episode, 5) * PER_EPISODE)
    wants_blink = hash01(episode, 6) > 0.55
    blink = 0.9 if (wants_blink and (frame % PER_EPISODE) == blink_at) else 0.0

    smoking = hash01(int(t / 20.0), 7) > 0.30
    return dict(phase=body_phase, travel=travel, head=head, lean=lean,
                blink=blink, smoking=smoking)


def main():
    frames = [pose(i / FPS) for i in range(0, int(FPS * 600))]   # 10 минут

    max_travel_jump = 0.0
    max_head_jump = 0.0
    for a, b in zip(frames, frames[1:]):
        max_travel_jump = max(max_travel_jump, abs(b["travel"] - a["travel"]))
        max_head_jump = max(max_head_jump, abs(b["head"] - a["head"]))

    print(f"кадров: {len(frames)} (10 минут)")
    print(f"макс. шаг travel за кадр: {max_travel_jump:.4f} (диапазон ~2.0)")
    print(f"макс. шаг head за кадр:  {max_head_jump:.4f}")
    print(f"travel в диапазоне: {min(f['travel'] for f in frames):.2f} .. {max(f['travel'] for f in frames):.2f}")
    smoke_share = sum(1 for f in frames if f["smoking"]) / len(frames)
    print(f"курит: {smoke_share:.0%} времени")
    blinks = sum(1 for f in frames if f["blink"] > 0)
    print(f"морганий за 10 минут: {blinks}")

    # не повторяется ли поведение: сравниваем эпизоды между собой
    per_ep = int(FPS * EPISODE)
    eps = [tuple(round(pose(i * per_ep / FPS)[k], 2) for k in ("travel", "head", "lean"))
           for i in range(len(frames) // per_ep)]
    print(f"эпизодов: {len(eps)}, уникальных: {len(set(eps))}")


if __name__ == "__main__":
    main()
