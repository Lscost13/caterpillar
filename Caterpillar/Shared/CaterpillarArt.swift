//
//  CaterpillarArt.swift
//  Caterpillar
//
//  Вся графика нарисована кодом (SwiftUI Canvas), без растровых ассетов:
//  одинаково чётко и в приложении, и в виджете на любом экране.
//
//  Система координат: локальные «единицы» (unit), y растёт вниз.
//    y = 0     — верх головы
//    y = 100   — поверхность ветки (лапки стоят здесь)
//    ширина фигуры ~ 40 unit
//

import SwiftUI

// MARK: - Палитра

enum CatColor {
    static let bodyDark = Color(red: 104 / 255, green: 122 / 255, blue: 88 / 255)
    static let body = Color(red: 150 / 255, green: 168 / 255, blue: 130 / 255)
    static let bodyHi = Color(red: 206 / 255, green: 215 / 255, blue: 176 / 255)
    static let belly = Color(red: 172 / 255, green: 186 / 255, blue: 148 / 255)
    static let edge = Color(red: 60 / 255, green: 71 / 255, blue: 48 / 255)
    static let foot = Color(red: 44 / 255, green: 51 / 255, blue: 36 / 255)
    static let eyeWhite = Color(red: 238 / 255, green: 244 / 255, blue: 232 / 255)
    static let iris = Color(red: 124 / 255, green: 182 / 255, blue: 204 / 255)
    static let irisDeep = Color(red: 66 / 255, green: 122 / 255, blue: 146 / 255)
    static let pupil = Color(red: 20 / 255, green: 25 / 255, blue: 31 / 255)
    static let brow = Color(red: 50 / 255, green: 59 / 255, blue: 40 / 255)
    static let mouth = Color(red: 38 / 255, green: 44 / 255, blue: 33 / 255)
    static let cig = Color(red: 244 / 255, green: 242 / 255, blue: 233 / 255)
    static let cigFilter = Color(red: 226 / 255, green: 199 / 255, blue: 152 / 255)
    static let ember = Color(red: 233 / 255, green: 137 / 255, blue: 56 / 255)
    static let emberHot = Color(red: 255 / 255, green: 208 / 255, blue: 145 / 255)
    static let smoke = Color(red: 236 / 255, green: 242 / 255, blue: 232 / 255)
    static let branch = Color(red: 104 / 255, green: 82 / 255, blue: 56 / 255)
    static let branchHi = Color(red: 146 / 255, green: 120 / 255, blue: 86 / 255)
    static let branchLo = Color(red: 62 / 255, green: 48 / 255, blue: 32 / 255)
}

// MARK: - Геометрия

enum CatGeom {
    /// Поверхность ветки (лапки).
    static let baseY: CGFloat = 100
    /// Лапки -> макушка.
    static let bodyH: CGFloat = 84
    /// Центр головы по y.
    static let headCY: CGFloat = 21.5
    static let headW: CGFloat = 23
    static let headH: CGFloat = 36
    /// До какого s тело уходит за голову.
    static let bodyTopS: CGFloat = 0.78

    /// Сколько единиц сцены видно по высоте и сколько срезано сверху.
    static let designHeight: CGFloat = 112
    static let designTop: CGFloat = 2.5

    /// Профиль толщины тела: (s, радиус).
    static let segments: [(CGFloat, CGFloat)] = [
        (0.00, 5.4), (0.06, 8.2), (0.12, 9.3), (0.20, 10.1),
        (0.28, 10.5), (0.36, 10.4), (0.44, 10.0), (0.52, 9.2),
        (0.60, 8.4), (0.68, 7.6), (0.78, 7.2)
    ]

    static func radius(_ s: CGFloat) -> CGFloat {
        let clampS = min(max(s, segments[0].0), segments[segments.count - 1].0)
        for i in 0..<(segments.count - 1) {
            let (s0, r0) = segments[i]
            let (s1, r1) = segments[i + 1]
            if clampS >= s0 && clampS <= s1 {
                var k = (s1 - s0) > 0 ? (clampS - s0) / (s1 - s0) : 0
                k = k * k * (3 - 2 * k)                      // smoothstep
                return r0 + (r1 - r0) * k
            }
        }
        return segments[segments.count - 1].1
    }

    static func sway(_ s: CGFloat, _ phase: CGFloat, _ lean: CGFloat) -> CGFloat {
        let amp = 0.9 + 2.4 * s
        return amp * catSin(2 * .pi * (phase + 0.28 * s)) + lean * 5.0 * s
    }

    /// Нижняя часть тела загибается вправо и ложится на ветку.
    static func tailBend(_ s: CGFloat) -> CGFloat {
        let t = min(1, max(0, s) / 0.34)
        return 17.0 * CGFloat(pow(Double(1.0 - t), 2.3))
    }

    static func spine(_ s: CGFloat, _ phase: CGFloat, _ lean: CGFloat) -> CGPoint {
        CGPoint(x: sway(s, phase, lean) + tailBend(s), y: baseY - bodyH * s)
    }

    /// Контур головы: суперэллипс, слегка сужающийся к подбородку.
    static func headOutline(_ center: CGPoint, _ hw: CGFloat, _ hh: CGFloat, n: Int = 56) -> [CGPoint] {
        var pts: [CGPoint] = []
        pts.reserveCapacity(n)
        let e: CGFloat = 0.80
        for i in 0..<n {
            let a = 2 * CGFloat.pi * CGFloat(i) / CGFloat(n)
            let ca = catCos(a), sa = catSin(a)
            let x = hw * (ca < 0 ? -1 : 1) * CGFloat(pow(Double(abs(ca)), Double(e)))
            let y = hh * (sa < 0 ? -1 : 1) * CGFloat(pow(Double(abs(sa)), Double(e)))
            let t = (y + hh) / (2 * hh)                       // 0 подбородок -> 1 темя
            let f = 0.80 + 0.20 * CGFloat(pow(Double(max(0, t)), 0.7))
            pts.append(CGPoint(x: center.x + x * f, y: center.y + y))
        }
        return pts
    }

    // MARK: - Геометрия для оверлеев (виджет)

    /// Кончик сигареты в юнитах сцены.
    static func cigTip(_ pose: CaterpillarPose) -> CGPoint {
        let neck = spine(bodyTopS, pose.phase, pose.lean)
        let cx = neck.x + pose.headTurn * 1.8
        return CGPoint(x: cx + headW / 2 * 0.44 + 9.6,
                       y: headCY + headH / 2 * 0.56 - 3.8)
    }

    /// Перевод точки сцены в координаты вью — те же формулы, что в Canvas.
    static func screenPoint(_ unit: CGPoint,
                            pose: CaterpillarPose,
                            size: CGSize,
                            hAlignment: CGFloat,
                            travelRange: CGFloat) -> CGPoint {
        let k = size.height / designHeight
        let originX = size.width * hAlignment + pose.travel * size.width * travelRange
        return CGPoint(x: originX + unit.x * k, y: (unit.y + designTop) * k)
    }
}


// MARK: - Наборы цветов

/// Цвета сцены. full — обычная гусеница, mono — версия для тонированного
/// режима виджета (iOS 18 перекрашивает содержимое, и цветная сцена
/// превращается в чёрное пятно).
struct CatPalette {
    var body: Color
    var bodyDark: Color
    var belly: Color
    var bodyHi: Color
    var edge: Color
    var foot: Color
    var eyeWhite: Color
    var iris: Color
    var irisDeep: Color
    var pupil: Color
    var brow: Color
    var mouth: Color
    var cig: Color
    var cigFilter: Color
    var ember: Color
    var emberHot: Color
    var smoke: Color
    var branch: Color
    var branchHi: Color
    var branchLo: Color

    static let full = CatPalette(
        body: CatColor.body,
        bodyDark: CatColor.bodyDark,
        belly: CatColor.belly,
        bodyHi: CatColor.bodyHi,
        edge: CatColor.edge,
        foot: CatColor.foot,
        eyeWhite: CatColor.eyeWhite,
        iris: CatColor.iris,
        irisDeep: CatColor.irisDeep,
        pupil: CatColor.pupil,
        brow: CatColor.brow,
        mouth: CatColor.mouth,
        cig: CatColor.cig,
        cigFilter: CatColor.cigFilter,
        ember: CatColor.ember,
        emberHot: CatColor.emberHot,
        smoke: CatColor.smoke,
        branch: CatColor.branch,
        branchHi: CatColor.branchHi,
        branchLo: CatColor.branchLo
    )

    static let mono = CatPalette(
        body: .white.opacity(0.40),
        bodyDark: .white.opacity(0.24),
        belly: .white.opacity(0.62),
        bodyHi: .white.opacity(0.80),
        edge: .white.opacity(0.85),
        foot: .white.opacity(0.90),
        eyeWhite: .white,
        iris: .white.opacity(0.75),
        irisDeep: .white.opacity(0.55),
        pupil: .black.opacity(0.80),
        brow: .white.opacity(0.95),
        mouth: .black.opacity(0.60),
        cig: .white,
        cigFilter: .white.opacity(0.70),
        ember: .white,
        emberHot: .white,
        smoke: .white,
        branch: .white.opacity(0.20),
        branchHi: .white.opacity(0.34),
        branchLo: .white.opacity(0.12)
    )
}

// MARK: - Сцена

/// Рисует ветку и гусеницу в заданной позе.
/// В приложении поза пересчитывается каждый кадр, в виджете — на каждую
/// запись таймлайна (WidgetKit не поддерживает непрерывную анимацию).
struct CaterpillarScene: View {
    var pose: CaterpillarPose
    /// Где стоит гусеница по ширине: 0 — слева, 1 — справа.
    var hAlignment: CGFloat = 0.32
    /// Насколько сильно сдвиг `travel` двигает её по ветке.
    var travelRange: CGFloat = 0.10
    /// Палитра: цветная или монохромная (для тонированного виджета).
    var colors: CatPalette = .full

    var body: some View {
        Canvas(rendersAsynchronously: false) { context, size in
            // Копия контекста: вложенные функции не должны захватывать inout-параметр.
            let ctx = context
            let pal = colors
            // Явные типы: иначе вывод типов в большой вьюхе срывается на [Any].
            let sides: [CGFloat] = [-1, 1]
            let k = size.height / CatGeom.designHeight
            let originX = size.width * hAlignment + pose.travel * size.width * travelRange

            func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint {
                CGPoint(x: originX + x * k, y: (y + CatGeom.designTop) * k)
            }
            func disc(_ x: CGFloat, _ y: CGFloat, _ r: CGFloat) -> Path {
                let c = P(x, y)
                return Path(ellipseIn: CGRect(x: c.x - r * k, y: c.y - r * k,
                                              width: 2 * r * k, height: 2 * r * k))
            }
            func oval(_ x: CGFloat, _ y: CGFloat, _ rx: CGFloat, _ ry: CGFloat) -> Path {
                let c = P(x, y)
                return Path(ellipseIn: CGRect(x: c.x - rx * k, y: c.y - ry * k,
                                              width: 2 * rx * k, height: 2 * ry * k))
            }
            func poly(_ pts: [CGPoint]) -> Path {
                var p = Path()
                guard let first = pts.first else { return p }
                p.move(to: first)
                for pt in pts.dropFirst() { p.addLine(to: pt) }
                p.closeSubpath()
                return p
            }
            func stroke(_ pts: [CGPoint], _ color: Color, _ width: CGFloat) {
                var p = Path()
                guard let first = pts.first else { return }
                p.move(to: first)
                for pt in pts.dropFirst() { p.addLine(to: pt) }
                ctx.stroke(p, with: .color(color),
                               style: StrokeStyle(lineWidth: width * k,
                                                  lineCap: .round, lineJoin: .round))
            }

            let phase = pose.phase
            let lean = pose.lean

            // ---------------------------------------------------- тело
            var bodyPts: [CGPoint] = []
            let n = 34
            for i in 0...n {
                let s = CatGeom.bodyTopS * CGFloat(i) / CGFloat(n)
                let c = CatGeom.spine(s, phase, lean)
                let r = CatGeom.radius(s)
                bodyPts.append(P(c.x - r, c.y))
            }
            for i in stride(from: n, through: 0, by: -1) {
                let s = CatGeom.bodyTopS * CGFloat(i) / CGFloat(n)
                let c = CatGeom.spine(s, phase, lean)
                let r = CatGeom.radius(s)
                bodyPts.append(P(c.x + r, c.y))
            }
            let bottom = CatGeom.spine(0, phase, lean)
            let rb = CatGeom.radius(0)
            for i in 1..<12 {
                let a = CGFloat.pi - CGFloat.pi * CGFloat(i) / 12
                bodyPts.append(P(bottom.x - rb * catCos(a), bottom.y + rb * catSin(a)))
            }
            let bodyPath = poly(bodyPts)
            ctx.fill(bodyPath, with: .color(pal.body))
            ctx.stroke(bodyPath, with: .color(pal.edge),
                           style: StrokeStyle(lineWidth: 0.85 * k, lineCap: .round, lineJoin: .round))

            // светлое брюшко
            var bellyPts: [CGPoint] = []
            for i in 0...n {
                let s = 0.05 + (0.50 - 0.05) * CGFloat(i) / CGFloat(n)
                let c = CatGeom.spine(s, phase, lean)
                let r = CatGeom.radius(s) * 0.44
                bellyPts.append(P(c.x - r, c.y))
            }
            for i in stride(from: n, through: 0, by: -1) {
                let s = 0.05 + (0.50 - 0.05) * CGFloat(i) / CGFloat(n)
                let c = CatGeom.spine(s, phase, lean)
                let r = CatGeom.radius(s) * 0.44
                bellyPts.append(P(c.x + r, c.y))
            }
            ctx.fill(poly(bellyPts), with: .color(pal.belly))

            // складки между сегментами
            let creases: [CGFloat] = [0.09, 0.17, 0.25, 0.33, 0.41, 0.49]
            for s in creases {
                let c = CatGeom.spine(s, phase, lean)
                let r = CatGeom.radius(s)
                stroke([P(c.x - r * 0.84, c.y + 1.1), P(c.x + r * 0.84, c.y - 0.4)],
                       pal.bodyDark, 1.0)
            }

            // лапки
            let footS: [CGFloat] = [0.08, 0.16, 0.24, 0.32, 0.40, 0.48]
            for (i, s) in footS.enumerated() {
                let c = CatGeom.spine(s, phase, lean)
                let r = CatGeom.radius(s)
                let lift = 1.4 * catSin(2 * .pi * (phase * 2 + CGFloat(i) * 0.18))
                for side in sides {
                    let x = c.x + side * (r * 0.95)
                    stroke([P(x, c.y), P(x + side * 2.5, c.y + 1.1 + lift * 0.3)],
                           pal.foot, 1.9)
                }
            }

            // ---------------------------------------------------- голова
            let hw = CatGeom.headW / 2
            let hh = CatGeom.headH / 2
            let neckRef = CatGeom.spine(CatGeom.bodyTopS, phase, lean)
            let cx = neckRef.x + pose.headTurn * 1.8
            let cy = CatGeom.headCY

            // шея
            let neckBase = CatGeom.spine(CatGeom.bodyTopS - 0.03, phase, lean)
            stroke([P(neckBase.x, neckBase.y), P(cx, cy + hh * 0.62)], pal.body, 11.2)

            // череп
            let skull = CatGeom.headOutline(CGPoint(x: cx, y: cy), hw, hh).map { P($0.x, $0.y) }
            let skullPath = poly(skull)
            ctx.fill(skullPath, with: .color(pal.body))
            ctx.stroke(skullPath, with: .color(pal.edge),
                           style: StrokeStyle(lineWidth: 0.95 * k, lineCap: .round, lineJoin: .round))

            // мягкий блик на щеке (радиальный градиент вместо блюра — он
            // безопаснее для бюджета памяти виджета)
            let cheek = P(cx - hw * 0.30, cy - hh * 0.05)
            ctx.fill(disc(cx - hw * 0.30, cy - hh * 0.05, hw * 1.05),
                         with: .radialGradient(Gradient(colors: [pal.bodyHi.opacity(0.55),
                                                                 pal.bodyHi.opacity(0.0)]),
                                               center: cheek,
                                               startRadius: 0,
                                               endRadius: hw * 1.05 * k))

            // брови: толстые клинья, опущенные к переносице
            for side in sides {
                let ax = cx + side * hw * 0.12, ay = cy - hh * 0.30
                let bx = cx + side * hw * 0.66, by = cy - hh * 0.56
                var nx = by - ay, ny = -(bx - ax)
                let len = max(0.001, CGFloat(sqrt(Double(nx * nx + ny * ny))))
                nx /= len; ny /= len
                let ta: CGFloat = 1.6, tb: CGFloat = 2.7
                ctx.fill(poly([P(ax + nx * ta, ay + ny * ta),
                                   P(bx + nx * tb, by + ny * tb),
                                   P(bx - nx * tb, by - ny * tb),
                                   P(ax - nx * ta, ay - ny * ta)]),
                             with: .color(pal.brow))
            }
            // переносица
            stroke([P(cx, cy - hh * 0.52), P(cx, cy - hh * 0.22)], pal.brow, 1.4)

            // глаза
            let er = hw * 0.35
            for side in sides {
                let ex = cx + side * hw * 0.44
                let ey = cy - hh * 0.06
                ctx.fill(disc(ex, ey, er), with: .color(pal.eyeWhite))
                ctx.stroke(disc(ex, ey, er), with: .color(pal.edge), lineWidth: 0.55 * k)
                let ix = ex + side * er * 0.06
                let iy = ey + er * 0.02
                ctx.fill(disc(ix, iy, er * 0.74), with: .color(pal.iris))
                ctx.fill(disc(ix, iy, er * 0.48), with: .color(pal.irisDeep))
                ctx.fill(disc(ix, iy + er * 0.02, er * 0.34), with: .color(pal.pupil))
                ctx.fill(disc(ix - er * 0.24, iy - er * 0.30, er * 0.14),
                             with: .color(.white.opacity(0.95)))
                if pose.blink > 0.2 {
                    ctx.fill(oval(ex, ey - er * 0.25, er * 1.06, er * (0.9 - 0.55 * pose.blink)),
                                 with: .color(pal.body))
                    stroke([P(ex - er, ey), P(ex + er, ey)], pal.brow, 1.2)
                }
            }

            // рот
            let my = cy + hh * 0.52
            let mouthPts = [P(cx - hw * 0.58, my - 1.6),
                            P(cx - hw * 0.02, my - 0.2),
                            P(cx + hw * 0.46, my + 1.2)]
            stroke(mouthPts, pal.mouth, 1.6)

            // ---------------------------------------------------- сигарета
            let cigBase = CGPoint(x: cx + hw * 0.44, y: cy + hh * 0.56)
            let cigTip = CGPoint(x: cigBase.x + 9.6, y: cigBase.y - 3.8)
            let emberOn = pose.smoke > 0.02

            var cigPath = Path()
            cigPath.move(to: P(cigBase.x, cigBase.y))
            cigPath.addLine(to: P(cigTip.x, cigTip.y))
            ctx.stroke(cigPath, with: .color(pal.cig),
                           style: StrokeStyle(lineWidth: 2.3 * k, lineCap: .round))
            var filterPath = Path()
            filterPath.move(to: P(cigBase.x, cigBase.y))
            filterPath.addLine(to: P(cigBase.x + (cigTip.x - cigBase.x) * 0.26,
                                     cigBase.y + (cigTip.y - cigBase.y) * 0.26))
            ctx.stroke(filterPath, with: .color(pal.cigFilter),
                           style: StrokeStyle(lineWidth: 2.35 * k, lineCap: .butt))

            ctx.fill(disc(cigTip.x, cigTip.y, 1.6),
                         with: .color(emberOn ? pal.ember : pal.cigFilter))
            if emberOn {
                let glow = P(cigTip.x + 0.6, cigTip.y - 0.4)
                ctx.fill(disc(cigTip.x + 0.6, cigTip.y - 0.4, 1.0),
                             with: .color(pal.emberHot))
                ctx.fill(disc(cigTip.x + 0.6, cigTip.y - 0.4, 3.2),
                             with: .radialGradient(Gradient(colors: [pal.ember.opacity(0.45),
                                                                     pal.ember.opacity(0)]),
                                                   center: glow, startRadius: 0, endRadius: 3.2 * k))
            }

            // ---------------------------------------------------- ветка
            let surface = P(0, CatGeom.baseY).y
            if surface < size.height {
                ctx.fill(Path(CGRect(x: 0, y: surface,
                                         width: size.width, height: size.height - surface)),
                             with: .color(pal.branch))
                ctx.fill(Path(CGRect(x: 0, y: surface,
                                         width: size.width, height: 1.4 * k)),
                             with: .color(pal.branchHi))
                var wood = Path()
                for i in 0..<40 {
                    let wx = -40 + CGFloat(i) * 7.5
                    let wy = CatGeom.baseY + 5 + CGFloat((i * 37) % 16)
                    let a = P(wx, wy)
                    let b = P(wx + 13, wy + 0.5)
                    if a.y > size.height { continue }
                    wood.move(to: a)
                    wood.addLine(to: b)
                }
                ctx.stroke(wood, with: .color(pal.branchLo),
                               style: StrokeStyle(lineWidth: 0.6 * k, lineCap: .round))
            }

            // ---------------------------------------------------- дым
            if pose.smoke > 0.02 {
                for i in 0..<9 {
                    var p = (pose.smokeT + CGFloat(i) / 9).truncatingRemainder(dividingBy: 1)
                    if p < 0 { p += 1 }
                    let r = 1.5 + 11.5 * p
                    let x = cigTip.x + catSin(p * 5.4 + CGFloat(i) * 1.6) * 6.0 * p + 1.4 * p
                    let y = cigTip.y - p * 56
                    let alpha: CGFloat = pose.smoke * CGFloat(pow(Double(1 - p), 1.05)) * 0.55
                    let center = P(x, y)
                    ctx.fill(disc(x, y, r),
                                 with: .radialGradient(Gradient(colors: [pal.smoke.opacity(alpha),
                                                                         pal.smoke.opacity(alpha * 0.45),
                                                                         pal.smoke.opacity(0)]),
                                                       center: center,
                                                       startRadius: 0,
                                                       endRadius: r * k))
                }
            }
        }
    }
}

// MARK: - Фон с боке

/// Размытая зелень, как на фото-референсе. Сделана градиентами, без блюра
/// и картинок — дёшево для виджета.
struct BokehBackground: View {
    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            ZStack {
                LinearGradient(colors: [Color(red: 0.40, green: 0.53, blue: 0.17),
                                        Color(red: 0.26, green: 0.38, blue: 0.12),
                                        Color(red: 0.19, green: 0.28, blue: 0.09)],
                               startPoint: .top, endPoint: .bottom)
                blob(x: w * 0.14, y: h * 0.16, r: w * 0.42,
                     color: Color(red: 0.72, green: 0.78, blue: 0.34), opacity: 0.55)
                blob(x: w * 0.62, y: h * 0.05, r: w * 0.36,
                     color: Color(red: 0.62, green: 0.72, blue: 0.26), opacity: 0.45)
                blob(x: w * 0.90, y: h * 0.34, r: w * 0.30,
                     color: Color(red: 0.68, green: 0.76, blue: 0.30), opacity: 0.35)
                blob(x: w * 0.05, y: h * 0.62, r: w * 0.34,
                     color: Color(red: 0.58, green: 0.68, blue: 0.22), opacity: 0.40)
                blob(x: w * 0.55, y: h * 0.78, r: w * 0.40,
                     color: Color(red: 0.50, green: 0.62, blue: 0.20), opacity: 0.35)
                blob(x: w * 0.82, y: h * 0.88, r: w * 0.26,
                     color: Color(red: 0.44, green: 0.55, blue: 0.17), opacity: 0.45)
                // мягкая виньетка по краям
                RadialGradient(colors: [.clear, .black.opacity(0.34)],
                               center: .center,
                               startRadius: min(w, h) * 0.22,
                               endRadius: max(w, h) * 0.78)
            }
        }
    }

    @ViewBuilder
    private func blob(x: CGFloat, y: CGFloat, r: CGFloat, color: Color, opacity: Double) -> some View {
        Circle()
            .fill(RadialGradient(colors: [color.opacity(opacity), color.opacity(opacity * 0.35), color.opacity(0)],
                                 center: .center, startRadius: 0, endRadius: r))
            .frame(width: r * 2, height: r * 2)
            .position(x: x, y: y)
    }
}

#Preview("Сцена") {
    ZStack {
        BokehBackground()
        CaterpillarScene(pose: CaterpillarPose(phase: 0.2, smoke: 1, smokeT: 0.3), hAlignment: 0.35)
            .frame(height: 340)
    }
    .frame(width: 360, height: 340)
}
