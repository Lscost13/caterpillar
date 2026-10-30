//
//  CaterpillarWidget.swift
//  CaterpillarWidget
//
//  Виджет 2x4 (systemMedium) с анимацией.
//
//  Как это устроено:
//    • WidgetKit проигрывает таймлайн — заранее расчерченные кадры. Мы кладём
//      их по 8 штук в секунду, поэтому движение читается как анимация.
//    • Поза кадра — чистая функция от времени. Это обязательно: система может
//      перерисовать один и тот же момент, и картинка должна быть той же.
//    • «Решения» гусеницы берутся из хеша номера эпизода (эпизод = 8 секунд).
//      Хеш от абсолютного времени не повторяется, поэтому поведение каждый раз
//      новое, хотя никакого состояния мы не храним.
//    • Внутри эпизода решение включается и выключается плавно (окно
//      smoothstep), поэтому на стыке эпизодов не бывает рывков.
//

import WidgetKit
import SwiftUI
import AppIntents

// MARK: - «Оживить» с виджета

/// Тап по кнопке перезапускает таймлайн: iOS сразу перерисовывает виджет и
/// начинает проигрывать кадры заново.
struct WakeIntent: AppIntent {
    static let title: LocalizedStringResource = "Оживить"

    func perform() async throws -> some IntentResult {
        WidgetCenter.shared.reloadAllTimelines()
        return .result()
    }
}

// MARK: - Timeline

struct CaterpillarEntry: TimelineEntry {
    let date: Date
    let pose: CaterpillarPose
}

struct CaterpillarProvider: TimelineProvider {
    /// Кадров в секунду на самом плавном участке.
    private let frameRate: Double = 8
    /// Сколько секунд в конце «засыпаем».
    private let sleepSeconds: Double = 20
    /// Длительность одного «решения», секунды.
    private let episodeSeconds: Double = 8

    /// Таймлайн строится ступенями: сначала плотно (плавно), потом всё реже.
    /// Так виджет живёт два часа, а не пять минут — и не упирается в конец
    /// таймлайна, где iOS уже не даёт перезагрузку.
    private struct Tier {
        let seconds: Double
        let step: TimeInterval
    }

    private var tiers: [Tier] {
        [
            Tier(seconds: 10 * 60, step: 1.0 / frameRate),   // 10 минут плавно
            Tier(seconds: 25 * 60, step: 1.0 / 3.0),         // 25 минут пореже
            Tier(seconds: 55 * 60, step: 1.0)                // час «редкий пульс»
        ]
    }

    func placeholder(in context: Context) -> CaterpillarEntry {
        CaterpillarEntry(date: Date(), pose: animationFrame(at: Date()))
    }

    func getSnapshot(in context: Context, completion: @escaping (CaterpillarEntry) -> Void) {
        let now = Date()
        completion(CaterpillarEntry(date: now, pose: animationFrame(at: now)))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<CaterpillarEntry>) -> Void) {
        var entries: [CaterpillarEntry] = []
        var cursor = Date()

        for tier in tiers {
            appendEntries(to: &entries,
                          from: cursor,
                          count: Int(tier.seconds / tier.step),
                          step: tier.step)
            cursor = cursor.addingTimeInterval(tier.seconds)
        }

        // в самом конце засыпаем: если система не даст перезагрузку, на виджете
        // будет спящая гусеница, а не случайно застывший кадр
        putToSleep(&entries, seconds: sleepSeconds)

        completion(Timeline(entries: entries, policy: .atEnd))
    }

    private func appendEntries(to entries: inout [CaterpillarEntry],
                               from start: Date,
                               count: Int,
                               step: TimeInterval) {
        entries.reserveCapacity(entries.count + count)
        for i in 0..<count {
            let date = start.addingTimeInterval(step * Double(i))
            entries.append(CaterpillarEntry(date: date, pose: animationFrame(at: date)))
        }
    }

    private func putToSleep(_ entries: inout [CaterpillarEntry], seconds: TimeInterval) {
        guard let last = entries.last,
              let first = entries.firstIndex(where: {
                  $0.date >= last.date.addingTimeInterval(-seconds)
              })
        else { return }

        var sleep = entries[first].pose
        sleep.blink = 1
        sleep.smoke = 0
        sleep.lean = 0
        sleep.headTurn = 0

        for i in first..<entries.count {
            entries[i] = CaterpillarEntry(date: entries[i].date, pose: sleep)
        }
    }

    // MARK: - Один кадр

    /// Кадр «стоп-моушен»: базовые сигналы от времени + решение текущего эпизода.
    private func animationFrame(at date: Date) -> CaterpillarPose {
        let t = date.timeIntervalSince1970
        let frame = Int(t * frameRate)

        // эпизод = одно «решение»
        let perEpisode = max(1, Int(episodeSeconds * frameRate))
        let episode = frame / perEpisode
        let phase = CGFloat(frame % perEpisode) / CGFloat(perEpisode)

        // что надумала гусеница в этом эпизоде
        let h1 = hash01(episode, 1)
        let h2 = hash01(episode, 2)
        let h3 = hash01(episode, 3)
        let h4 = hash01(episode, 4)

        // окно: 0 на границах эпизода, 1 в середине — рывков не будет
        let window = smoothstep(0.10, 0.35, phase) * (1 - smoothstep(0.65, 0.90, phase))

        // тело: своя волна + «потягивание» внутри эпизода
        let basePhase = CGFloat(t / 8.0).truncatingRemainder(dividingBy: 1)
        let bodyPhase = basePhase + window * (h1 - 0.5) * 0.30

        // ветка: медленный дрейф из несоизмеримых синусов + шаг внутри эпизода
        let drift = 0.55 * catSin(CGFloat(t / 97.0) * 2 * .pi) +
            0.28 * catSin(CGFloat(t / 41.0) * 2 * .pi + 1.7)
        let travel = drift + window * (h2 - 0.5) * 0.35

        // голова: смотрит по сторонам, иногда специально поворачивается
        let headBase = catSin(CGFloat(t / 13.0) * 2 * .pi + 0.5) * 0.35
        let headTurn = headBase + window * (h3 - 0.5) * 1.30

        // корпус
        let lean = catSin(CGFloat(t / 7.0) * 2 * .pi) * 0.18 +
            window * (h4 - 0.5) * 0.30

        // моргание: не в каждом эпизоде, в случайном кадре (в среднем раз в ~20 с)
        let blinkAt = Int(hash01(episode, 5) * CGFloat(perEpisode))
        let wantsBlink = hash01(episode, 6) > 0.55
        let blink: CGFloat = (wantsBlink && (frame % perEpisode) == blinkAt) ? 0.9 : 0

        // курение живёт блоками по 20 секунд
        let smokeBlock = Int(t / 20.0)
        let smoking = hash01(smokeBlock, 7) > 0.30
        let smokeT = CGFloat(frame % 24) / 24

        return CaterpillarPose(phase: bodyPhase,
                               travel: travel,
                               lean: lean,
                               blink: blink,
                               headTurn: headTurn,
                               smoke: smoking ? 1 : 0,
                               smokeT: smokeT)
    }

    // MARK: - Вспомогательное

    /// Стабильное псевдослучайное число 0...1 из индекса и соли.
    private func hash01(_ value: Int, _ salt: UInt64) -> CGFloat {
        var x = UInt64(bitPattern: Int64(value)) &+ salt &* 0x9E3779B97F4A7C15
        x ^= x >> 33
        x = x &* 0xFF51AFD7ED558CCD
        x ^= x >> 29
        return CGFloat(x % 10_000) / 10_000
    }

    private func smoothstep(_ edge0: CGFloat, _ edge1: CGFloat, _ x: CGFloat) -> CGFloat {
        let t = min(max((x - edge0) / (edge1 - edge0), 0), 1)
        return t * t * (3 - 2 * t)
    }
}

// MARK: - View

struct CaterpillarWidgetView: View {
    var entry: CaterpillarEntry

    @Environment(\.widgetRenderingMode) private var renderingMode

    /// iOS 18: при тёмных/тонированных иконках система перерисовывает виджет
    /// в приглушённом виде, и цветная сцена превращается в чёрное пятно.
    private var isTinted: Bool { renderingMode != .fullColor }

    var body: some View {
        CaterpillarScene(pose: entry.pose,
                         hAlignment: 0.40,
                         travelRange: 0.22,
                         colors: isTinted ? .mono : .full)
            .overlay(alignment: .bottomTrailing) { wakeButton }
            .containerBackground(for: .widget) {
                if isTinted {
                    Color.clear
                } else {
                    BokehBackground()
                }
            }
    }

    private var wakeButton: some View {
        Button(intent: WakeIntent()) {
            HStack(spacing: 5) {
                Image(systemName: "play.fill")
                    .font(.system(size: 10, weight: .bold))
                Text("оживить")
                    .font(.system(size: 11, weight: .bold, design: .rounded))
            }
            .foregroundStyle(.white.opacity(0.8))
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(Capsule().fill(.white.opacity(0.16)))
        }
        .buttonStyle(.plain)
        .padding(.trailing, 10)
        .padding(.bottom, 12)
    }
}

// MARK: - Widget

struct CaterpillarWidget: Widget {
    let kind = "CaterpillarWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: CaterpillarProvider()) { entry in
            CaterpillarWidgetView(entry: entry)
        }
        .configurationDisplayName("Гусеница")
        .description("Живёт своей жизнью: ползёт, останавливается, оглядывается и курит.")
        .supportedFamilies([.systemMedium])
        .contentMarginsDisabled()
    }
}

@main
struct CaterpillarWidgetBundle: WidgetBundle {
    var body: some Widget {
        CaterpillarWidget()
    }
}
