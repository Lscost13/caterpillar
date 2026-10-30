//
//  CaterpillarPose.swift
//  Caterpillar
//
//  Поза гусеницы. Одна и та же структура используется приложением (плавная
//  анимация 30-60 fps) и виджетом (одна поза на запись таймлайна, потому что
//  WidgetKit не умеет непрерывную анимацию).
//

import Foundation
import CoreGraphics

// Тригонометрия для CGFloat: на 32-битных платформах CGFloat != Double,
// поэтому конвертируем явно, без неявных преобразований.
@inline(__always) func catSin(_ x: CGFloat) -> CGFloat { CGFloat(sin(Double(x))) }
@inline(__always) func catCos(_ x: CGFloat) -> CGFloat { CGFloat(cos(Double(x))) }

struct CaterpillarPose: Equatable {
    /// Фаза волны тела, 0...1 (один полный цикл «ползка»).
    var phase: CGFloat = 0
    /// Горизонтальный сдвиг вдоль ветки, -1...1.
    var travel: CGFloat = 0
    /// Наклон корпуса, -1...1.
    var lean: CGFloat = 0
    /// Прищур век, 0 (открыто) ... 1 (закрыто).
    var blink: CGFloat = 0
    /// Поворот головы, -1...1.
    var headTurn: CGFloat = 0
    /// Сила дыма, 0...1.
    var smoke: CGFloat = 0
    /// Фаза подъёма дыма, 0...1.
    var smokeT: CGFloat = 0

    static let idle = CaterpillarPose()

    // MARK: - Живая анимация (приложение)

    /// Плавная, непрерывная поза. Вызывается из TimelineView(.animation).
    static func live(at date: Date, boost: CGFloat = 0) -> CaterpillarPose {
        let t = CGFloat(date.timeIntervalSinceReferenceDate)

        // Волна тела: один цикл ~ 9 секунд, гусеница «переставляет» сегменты.
        let phase = (t / 9.0).truncatingRemainder(dividingBy: 1)

        // Медленно курсирует по ветке влево-вправо.
        let travel = 0.55 * catSin(t / 13.0 * .pi)
        let lean = 0.30 * catSin(t / 6.5)
        let headTurn = 0.55 * catSin(t / 5.3)

        // Моргание раз в ~4.7 секунды.
        let bc = t.truncatingRemainder(dividingBy: 4.7)
        let blink: CGFloat = bc < 0.18 ? catSin(bc / 0.18 * .pi) : 0

        // Курит примерно с 5-й по 15-ю секунду каждого 15-секундного цикла.
        let cyc = t.truncatingRemainder(dividingBy: 15.0)
        var smoke: CGFloat = 0
        if cyc > 5.0 {
            smoke = min(1, (cyc - 5.0) / 1.2) * min(1, (15.0 - cyc) / 1.2)
        }
        smoke = max(smoke, boost)

        return CaterpillarPose(phase: phase,
                               travel: travel,
                               lean: lean,
                               blink: blink,
                               headTurn: headTurn,
                               smoke: smoke,
                               smokeT: (t / 7.0).truncatingRemainder(dividingBy: 1))
    }

    // MARK: - Медленная поза (виджет)

    /// Кадр для виджета. Детерминирован от даты, поэтому состояние не нужно
    /// хранить между запусками расширения. Кадры идут раз в минуту — на каждом
    /// поза заметно другая (волна тела, сдвиг по ветке, дым).
    static func slow(at date: Date) -> CaterpillarPose {
        let t = date.timeIntervalSince1970

        // Волна тела: полный цикл 8 минут = 8 кадров.
        let phase = CGFloat((t / 480.0).truncatingRemainder(dividingBy: 1))

        // Ползёт по ветке туда-обратно: полный проход 30 минут.
        let travel = 0.55 * catSin(CGFloat(t / 1800.0) * 2 * .pi)
        let lean = 0.35 * catSin(CGFloat(t / 420.0) * 2 * .pi)
        let headTurn = 0.65 * catSin(CGFloat(t / 660.0) * 2 * .pi)

        // Курит 5 минут из каждых 12.
        let cycle = t.truncatingRemainder(dividingBy: 720.0)
        let smoking = cycle < 300.0

        // Дым поднимается кадр за кадром: каждую минуту новая фаза.
        let smokeT = CGFloat((t / 60.0).truncatingRemainder(dividingBy: 1))

        // Редкое моргание: один кадр из девяти.
        let slot = Int(t / 60.0)
        let blink: CGFloat = (slot % 9 == 4) ? 0.85 : 0

        return CaterpillarPose(phase: phase,
                               travel: travel,
                               lean: lean,
                               blink: blink,
                               headTurn: headTurn,
                               smoke: smoking ? 1 : 0,
                               smokeT: smokeT)
    }
}
