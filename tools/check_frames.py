"""Проверка математики кадров виджета без Xcode.

Повторяет формулу из CaterpillarProvider.animationFrame и печатает, как
меняются поза и сдвиг от кадра к кадру — чтобы убедиться, что анимация
не «дёргается» и не стоит на месте.
"""

import math

FRAME_RATE = 2.0
CYCLE = 16


def frame_pose(frame):
    phase = (frame % CYCLE) / CYCLE
    base = ((frame // CYCLE) % 8) / 8
    push = 0.0 if phase < 0.5 else (phase - 0.5) * 2 / 8
    travel = ((base + push) * 2 - 1) * 0.75
    lean = math.sin(phase * 2 * math.pi) * 0.22
    head = math.sin(phase * 2 * math.pi + 0.9) * 0.55
    blink = 0.9 if frame % 64 == 17 else 0.0
    smoking = (frame // 30) % 3 != 0
    smoke_t = (frame % 12) / 12
    return dict(phase=phase, travel=travel, lean=lean, head=head,
                blink=blink, smoking=smoking, smoke_t=smoke_t)


def main():
    print(f"{'кадр':>4} {'t,с':>5} {'phase':>6} {'travel':>7} {'lean':>6} "
          f"{'head':>6} {'blink':>5} {'дым':>4} {'smokeT':>6}")
    prev = None
    max_jump = 0.0
    for f in range(0, 41):
        p = frame_pose(f)
        print(f"{f:>4} {f / FRAME_RATE:>5.1f} {p['phase']:>6.3f} {p['travel']:>7.3f} "
              f"{p['lean']:>6.3f} {p['head']:>6.3f} {p['blink']:>5.2f} "
              f"{'да' if p['smoking'] else 'нет':>4} {p['smoke_t']:>6.2f}")
        if prev is not None:
            max_jump = max(max_jump, abs(p["travel"] - prev["travel"]))
        prev = p

    print()
    print(f"макс. скачок travel за кадр: {max_jump:.4f} "
          f"(доля полного размаха: {max_jump / 1.5:.1%})")
    phases = {round(frame_pose(f)["phase"], 3) for f in range(CYCLE)}
    print("уникальных фаз за цикл:", len(phases), "из", CYCLE)
    smoking_frames = sum(1 for f in range(300) if frame_pose(f)["smoking"])
    print(f"дымит {smoking_frames / 300:.0%} времени")


if __name__ == "__main__":
    main()
