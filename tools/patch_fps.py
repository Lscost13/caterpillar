"""Патч частоты кадров виджета: 2 fps -> 8 fps.

Скорость движения остаётся прежней (цикл волны 8 секунд), но кадров в нём
в 4 раза больше — вместо слайд-шоу получается плавный стоп-моушен.
"""

import io
import re

PATH = r"C:\Users\Manul\Documents\ipa\Caterpillar\Widget\CaterpillarWidget.swift"

src = io.open(PATH, encoding="utf-8").read()
before = src

src = src.replace(
    "    /// Кадров в секунду.\n    private let frameRate: Double = 2\n"
    "    /// Сколько кадров отдаём за раз: 600 / 2 = 5 минут анимации.\n"
    "    private let frameCount = 600",
    "    /// Кадров в секунду (8 — уже читается как анимация, а не слайд-шоу).\n"
    "    private let frameRate: Double = 8\n"
    "    /// Сколько кадров отдаём за раз: 2400 / 8 = 5 минут анимации.\n"
    "    private let frameCount = 2400\n"
    "    /// Длительность одного цикла волны по телу, секунды.\n"
    "    private let cycleSeconds: Double = 8",
)

new_body = '''    /// Один кадр «стоп-моушен».
    private func animationFrame(at date: Date) -> CaterpillarPose {
        let t = date.timeIntervalSince1970
        let frame = Int(t * frameRate)

        // кадров в одном цикле волны (8 секунд)
        let perCycle = max(1, Int(cycleSeconds * frameRate))
        let phase = CGFloat(frame % perCycle) / CGFloat(perCycle)

        // сдвиг по ветке: 8 позиций, движение «толчком» во второй половине
        // каждого цикла — как у настоящей гусеницы, а не равномерное скольжение
        let base = CGFloat((frame / perCycle) % 8) / 8
        let push: CGFloat = phase < 0.5 ? 0 : (phase - 0.5) * 2 / 8
        let travel = ((base + push) * 2 - 1) * 0.75

        // моргание — один кадр на четыре цикла (~32 секунды)
        let blink: CGFloat = (frame % (perCycle * 4) == perCycle * 2) ? 0.9 : 0

        // курит два блока из трёх (~16 секунд каждый)
        let smoking = (frame / (perCycle * 2)) % 3 != 0

        // дым поднимается кадр за кадром (3 секунды на полный подъём)
        let smokeT = CGFloat(frame % (perCycle / 2 + 1)) / CGFloat(max(1, perCycle / 2))

        return CaterpillarPose(phase: phase,
                               travel: travel,
                               lean: catSin(phase * 2 * .pi) * 0.22,
                               blink: blink,
                               headTurn: catSin(phase * 2 * .pi + 0.9) * 0.55,
                               smoke: smoking ? 1 : 0,
                               smokeT: smokeT)
    }
'''

pattern = re.compile(
    r"    /// Один кадр «стоп-моушен»\.\n.*?\n    \}\n", re.S)
assert pattern.search(src), "не нашёл функцию animationFrame"
src = pattern.sub(new_body, src, count=1)

io.open(PATH, "w", encoding="utf-8", newline="\n").write(src)

print("frameRate 8:", "frameRate: Double = 8" in src)
print("frameCount 2400:", "frameCount = 2400" in src)
print("cycleSeconds:", "cycleSeconds: Double = 8" in src)
print("файл изменился:", src != before)
