#!/usr/bin/env bash
#
# Собирает НЕПОДПИСАННЫЙ .ipa из исходников.
# Запускать на macOS с установленным Xcode 15+ (нужен iOS 17 SDK).
#
#   cd Caterpillar
#   bash ../scripts/build-ipa.sh
#
# Результат: build/Caterpillar.ipa — его можно подписать своим Apple ID
# через Sideloadly / AltStore / TrollStore-re-signed.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$HERE/../Caterpillar" && pwd)"
cd "$PROJECT_DIR"

APP_NAME="Caterpillar"
SCHEME="Caterpillar"
BUILD_DIR="build"
OUT_DIR="$BUILD_DIR/out"
IPA_PATH="$BUILD_DIR/$APP_NAME.ipa"

echo "==> Xcode:"
xcodebuild -version

rm -rf "$BUILD_DIR"
mkdir -p "$OUT_DIR"

echo "==> Сборка (arm64, без подписи)…"
xcodebuild \
  -project "$PROJECT_DIR/$APP_NAME.xcodeproj" \
  -scheme "$SCHEME" \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  SYMROOT="$PROJECT_DIR/$OUT_DIR" \
  OBJROOT="$PROJECT_DIR/$BUILD_DIR/obj" \
  ARCHS=arm64 \
  ONLY_ACTIVE_ARCH=NO \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGN_IDENTITY="" \
  build

APP_PATH="$PROJECT_DIR/$OUT_DIR/Release-iphoneos/$APP_NAME.app"
if [ ! -d "$APP_PATH" ]; then
  # на всякий случай: Xcode мог положить продукт в другую подпапку
  APP_PATH="$(find "$PROJECT_DIR/$OUT_DIR" -maxdepth 4 -type d -name "$APP_NAME.app" | head -n 1)"
fi
if [ -z "${APP_PATH:-}" ] || [ ! -d "$APP_PATH" ]; then
  echo "!! Не нашёл $APP_NAME.app в $OUT_DIR" >&2
  exit 1
fi

echo "==> Проверка содержимого бандла…"
test -d "$APP_PATH/PlugIns/CaterpillarWidget.appex" || {
  echo "!! Виджет-расширение не встроилось в приложение" >&2
  exit 1
}
/usr/libexec/PlistBuddy -c "Print :NSExtension:NSExtensionPointIdentifier" \
  "$APP_PATH/PlugIns/CaterpillarWidget.appex/Info.plist"

echo "==> Упаковка .ipa…"
rm -rf "$BUILD_DIR/Payload"
mkdir -p "$BUILD_DIR/Payload"
cp -R "$APP_PATH" "$BUILD_DIR/Payload/"
(cd "$BUILD_DIR" && zip -qry "$APP_NAME.ipa" Payload)
rm -rf "$BUILD_DIR/Payload"

echo
echo "Готово: $PROJECT_DIR/$IPA_PATH"
ls -lh "$IPA_PATH"
echo
echo "Дальше: подписать своим Apple ID (Sideloadly / AltStore) и установить."
