//
//  ContentView.swift
//  Caterpillar
//
//  Экран приложения: живая гусеница (полноценная анимация) + памятка, как
//  добавить виджет 2x4 на рабочий стол. Плюс полноэкранный режим — там
//  гусеница ползёт непрерывно, а экран не гаснет.
//

import SwiftUI
import UIKit
import WidgetKit

struct ContentView: View {
    /// Момент, когда пользователь ткнул в гусеницу — из-за этого она дымит.
    @State private var puffAt: Date?
    /// Полноэкранный режим: только гусеница, без интерфейса.
    @State private var immersive = false

    var body: some View {
        ZStack {
            if immersive {
                immersiveScreen
            } else {
                mainScreen
            }
        }
        // Пока приложение открыто, экран не гаснет: гусеница ползёт постоянно.
        .onAppear { UIApplication.shared.isIdleTimerDisabled = true }
        .onDisappear { UIApplication.shared.isIdleTimerDisabled = false }
    }

    // MARK: - Обычный экран

    private var mainScreen: some View {
        ZStack {
            BokehBackground().ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(spacing: 14) {
                    header
                    sceneCard
                    hint
                    puffButton
                    immersiveButton
                    caption
                }
                .padding(.horizontal, 20)
                .padding(.top, 10)
                .padding(.bottom, 26)
            }
        }
    }

    private var header: some View {
        VStack(spacing: 2) {
            Text("Гусеница")
                .font(.system(size: 34, weight: .black, design: .rounded))
                .foregroundStyle(.white)
                .shadow(color: .black.opacity(0.35), radius: 8, y: 3)
            Text("ползёт · иногда курит")
                .font(.system(size: 13, weight: .semibold, design: .rounded))
                .foregroundStyle(.white.opacity(0.65))
        }
        .frame(maxWidth: .infinity, alignment: .center)
    }

    private var sceneCard: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 40.0)) { timeline in
            CaterpillarScene(pose: livePose(at: timeline.date),
                             hAlignment: 0.42,
                             travelRange: 0.06)
        }
        .frame(height: 320)
        .frame(maxWidth: .infinity)
        .background(BokehBackground())
        .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 26, style: .continuous)
                .strokeBorder(.white.opacity(0.14), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.35), radius: 18, y: 10)
        .contentShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
        .onTapGesture {
            puffAt = Date()
        }
    }

    private var hint: some View {
        VStack(alignment: .leading, spacing: 6) {
            Label("Виджет 2×4 на рабочий стол", systemImage: "square.grid.2x2.fill")
                .font(.system(size: 13, weight: .bold, design: .rounded))
                .foregroundStyle(.white.opacity(0.9))
            Text("Зажми пустое место на рабочем столе → «+» → найди «Гусеница» → выбери средний виджет. "
                 + "Виджет меняет кадр раз в минуту: iOS не разрешает виджетам непрерывную анимацию.")
                .font(.system(size: 12, weight: .medium, design: .rounded))
                .foregroundStyle(.white.opacity(0.6))
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(.white.opacity(0.07))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .strokeBorder(.white.opacity(0.08), lineWidth: 1)
        )
    }

    private var puffButton: some View {
        Button {
            puffAt = Date()
            WidgetCenter.shared.reloadAllTimelines()
        } label: {
            HStack(spacing: 8) {
                Image(systemName: "smoke.fill")
                Text("Затянуться")
                    .font(.system(size: 15, weight: .bold, design: .rounded))
            }
            .foregroundStyle(.black.opacity(0.85))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 13)
            .background(
                Capsule().fill(Color(red: 0.78, green: 0.86, blue: 0.55))
            )
        }
        .buttonStyle(.plain)
    }

    private var immersiveButton: some View {
        Button {
            withAnimation(.easeInOut(duration: 0.25)) { immersive = true }
        } label: {
            HStack(spacing: 8) {
                Image(systemName: "arrow.up.left.and.arrow.down.right")
                Text("На весь экран")
                    .font(.system(size: 15, weight: .bold, design: .rounded))
            }
            .foregroundStyle(.white.opacity(0.9))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(
                Capsule().strokeBorder(.white.opacity(0.22), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }

    private var caption: some View {
        Text("Экран не гаснет, пока приложение открыто — в полноэкранном режиме гусеница ползёт без остановки.")
            .font(.system(size: 11, weight: .medium, design: .rounded))
            .foregroundStyle(.white.opacity(0.4))
            .multilineTextAlignment(.center)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, 8)
    }

    // MARK: - Полноэкранный режим

    private var immersiveScreen: some View {
        ZStack {
            BokehBackground().ignoresSafeArea()

            TimelineView(.animation(minimumInterval: 1.0 / 60.0)) { timeline in
                CaterpillarScene(pose: livePose(at: timeline.date),
                                 hAlignment: 0.5,
                                 travelRange: 0.14)
            }
            .ignoresSafeArea()

            VStack {
                Spacer()
                Text("тап — вернуться")
                    .font(.system(size: 12, weight: .semibold, design: .rounded))
                    .foregroundStyle(.white.opacity(0.45))
                    .padding(.bottom, 26)
            }
        }
        .statusBarHidden(true)
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.25)) { immersive = false }
        }
    }

    // MARK: - Поза

    private func livePose(at date: Date) -> CaterpillarPose {
        let boost: CGFloat
        if let puffAt {
            let age = date.timeIntervalSince(puffAt)
            boost = CGFloat(max(0, min(1, 1 - age / 2.6)))
        } else {
            boost = 0
        }
        return CaterpillarPose.live(at: date, boost: boost)
    }
}

#Preview {
    ContentView()
}
