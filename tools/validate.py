"""Проверки проекта, которые можно выполнить на Windows без Xcode.

1. project.pbxproj парсится как OpenStep-plist и все ссылки на объекты живут.
2. Info.plist-ы валидны.
3. Contents.json-ы валидны, иконка на месте и нужного размера.
4. Схема — валидный XML.
5. Во всех .swift сбалансированы скобки, и нет случайных «умных» кавычек.

    python tools/validate.py
"""

from __future__ import annotations

import json
import os
import plistlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(ROOT, "Caterpillar")
PBXPROJ = os.path.join(PROJECT_DIR, "Caterpillar.xcodeproj", "project.pbxproj")

errors: list[str] = []
warnings: list[str] = []


# ------------------------------------------------------------------ OpenStep
class Parser:
    """Минимальный парсер формата OpenStep property list (как в pbxproj)."""

    def __init__(self, text: str):
        self.s = text
        self.i = 0

    def error(self, msg: str):
        raise ValueError(f"{msg} at offset {self.i}")

    def skip(self):
        while self.i < len(self.s):
            c = self.s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif self.s.startswith("/*", self.i):
                end = self.s.find("*/", self.i + 2)
                if end < 0:
                    self.error("unterminated comment")
                self.i = end + 2
            elif self.s.startswith("//", self.i):
                end = self.s.find("\n", self.i)
                self.i = len(self.s) if end < 0 else end + 1
            else:
                return

    def atom(self) -> str:
        self.skip()
        if self.i >= len(self.s):
            self.error("unexpected end")
        c = self.s[self.i]
        if c == '"':
            self.i += 1
            buf = []
            while True:
                if self.i >= len(self.s):
                    self.error("unterminated string")
                ch = self.s[self.i]
                if ch == "\\":
                    buf.append(self.s[self.i + 1])
                    self.i += 2
                    continue
                if ch == '"':
                    self.i += 1
                    break
                buf.append(ch)
                self.i += 1
            return "".join(buf)
        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in "{}()=;,\"'":
            self.i += 1
        token = self.s[start:self.i].strip()
        if not token:
            self.error("empty token")
        return token

    def value(self):
        self.skip()
        c = self.s[self.i]
        if c == "{":
            return self.dictionary()
        if c == "(":
            return self.array()
        return self.atom()

    def dictionary(self) -> dict:
        self.skip()
        assert self.s[self.i] == "{"
        self.i += 1
        out = {}
        while True:
            self.skip()
            if self.i >= len(self.s):
                self.error("unterminated dict")
            if self.s[self.i] == "}":
                self.i += 1
                return out
            key = self.atom()
            self.skip()
            if self.s[self.i] != "=":
                self.error(f"expected '=' after {key!r}")
            self.i += 1
            out[key] = self.value()
            self.skip()
            if self.i < len(self.s) and self.s[self.i] == ";":
                self.i += 1

    def array(self) -> list:
        self.skip()
        assert self.s[self.i] == "("
        self.i += 1
        out = []
        while True:
            self.skip()
            if self.i >= len(self.s):
                self.error("unterminated array")
            if self.s[self.i] == ")":
                self.i += 1
                return out
            out.append(self.value())
            self.skip()
            if self.i < len(self.s) and self.s[self.i] == ",":
                self.i += 1


def check_pbxproj():
    with open(PBXPROJ, encoding="utf-8") as fh:
        text = fh.read()

    if not text.startswith("// !$*UTF8*$!"):
        errors.append("pbxproj: нет заголовка // !$*UTF8*$!")

    try:
        # Комментарии в pbxproj — просто украшение; убираем их до парсинга.
        stripped = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        data = Parser(stripped).dictionary()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pbxproj: не парсится: {exc}")
        return

    objects = data.get("objects", {})
    root = data.get("rootObject")
    if root not in objects:
        errors.append("pbxproj: rootObject не найден в objects")
        return

    refs = set(re.findall(r"\b[0-9A-F]{24}\b", text))
    missing = sorted(r for r in refs if r not in objects)
    if missing:
        errors.append(f"pbxproj: ссылки на несуществующие объекты: {missing}")

    project = objects[root]
    targets = project.get("targets", [])
    if len(targets) != 2:
        errors.append(f"pbxproj: ожидалось 2 таргета, найдено {len(targets)}")

    product_types = {objects[t].get("productType") for t in targets if t in objects}
    if "com.apple.product-type.application" not in product_types:
        errors.append("pbxproj: нет application-таргета")
    if "com.apple.product-type.app-extension" not in product_types:
        errors.append("pbxproj: нет app-extension-таргета")

    for tid in targets:
        target = objects.get(tid)
        if not target:
            continue
        name = target.get("name")
        if target.get("productReference") not in objects:
            errors.append(f"pbxproj: {name}: битый productReference")
        if target.get("buildConfigurationList") not in objects:
            errors.append(f"pbxproj: {name}: битый buildConfigurationList")
        for phase in target.get("buildPhases", []):
            if phase not in objects:
                errors.append(f"pbxproj: {name}: битая build phase {phase}")
                continue
            for bf in objects[phase].get("files", []):
                if bf not in objects:
                    errors.append(f"pbxproj: {name}: битый build file {bf}")
                    continue
                if objects[bf].get("fileRef") not in objects:
                    errors.append(f"pbxproj: {name}: build file без fileRef")
        for dep in target.get("dependencies", []):
            if dep not in objects:
                errors.append(f"pbxproj: {name}: битая зависимость {dep}")

    for oid, obj in objects.items():
        if obj.get("isa") == "PBXGroup":
            for child in obj.get("children", []):
                if child not in objects:
                    errors.append(f"pbxproj: группа {oid}: битый child {child}")

    # исходники, которые обязаны попасть в оба таргета
    src_counts: dict[str, int] = {}
    for oid, obj in objects.items():
        if obj.get("isa") == "PBXBuildFile":
            name = objects[obj["fileRef"]].get("path", "?")
            src_counts[name] = src_counts.get(name, 0) + 1
    for shared in ("CaterpillarArt.swift", "CaterpillarPose.swift"):
        if src_counts.get(shared) != 2:
            errors.append(f"pbxproj: {shared} должен компилироваться в двух таргетах "
                          f"(найдено {src_counts.get(shared, 0)})")
    for name in ("CaterpillarWidget.swift", "ContentView.swift", "CaterpillarApp.swift"):
        if src_counts.get(name) != 1:
            errors.append(f"pbxproj: {name} должен быть ровно в одном таргете")


def check_plists():
    for rel in ("App/Info.plist", "Widget/Info.plist"):
        path = os.path.join(PROJECT_DIR, rel)
        if not os.path.exists(path):
            errors.append(f"{rel}: файла нет")
            continue
        try:
            with open(path, "rb") as fh:
                data = plistlib.load(fh)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel}: невалидный plist: {exc}")
            continue
        for key in ("CFBundleIdentifier", "CFBundleExecutable", "CFBundleVersion"):
            if key not in data:
                errors.append(f"{rel}: нет {key}")
    widget_plist = os.path.join(PROJECT_DIR, "Widget/Info.plist")
    if os.path.exists(widget_plist):
        with open(widget_plist, "rb") as fh:
            data = plistlib.load(fh)
        point = data.get("NSExtension", {}).get("NSExtensionPointIdentifier")
        if point != "com.apple.widgetkit-extension":
            errors.append(f"Widget/Info.plist: NSExtensionPointIdentifier = {point!r}")


def check_assets():
    base = os.path.join(PROJECT_DIR, "App", "Assets.xcassets")
    for rel in ("Contents.json", "AppIcon.appiconset/Contents.json"):
        path = os.path.join(base, rel)
        if not os.path.exists(path):
            errors.append(f"assets: нет {rel}")
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                json.load(fh)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"assets: {rel}: невалидный JSON: {exc}")
    icon = os.path.join(base, "AppIcon.appiconset", "AppIcon1024.png")
    if not os.path.exists(icon):
        errors.append("assets: нет AppIcon1024.png")
    else:
        try:
            from PIL import Image
            with Image.open(icon) as im:
                if im.size != (1024, 1024):
                    errors.append(f"assets: иконка {im.size}, нужна 1024x1024")
                if im.mode not in ("RGB", "RGBA"):
                    errors.append(f"assets: иконка в режиме {im.mode}")
                if im.mode == "RGBA" and im.getchannel("A").getextrema()[0] < 255:
                    warnings.append("assets: в иконке есть прозрачность (App Store не любит)")
        except ImportError:
            pass


def check_scheme():
    path = os.path.join(PROJECT_DIR, "Caterpillar.xcodeproj", "xcshareddata",
                        "xcschemes", "Caterpillar.xcscheme")
    if not os.path.exists(path):
        errors.append("scheme: файла нет")
        return
    try:
        ET.parse(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"scheme: невалидный XML: {exc}")


def check_swift():
    for dirpath, _dirnames, filenames in os.walk(os.path.join(PROJECT_DIR)):
        for name in filenames:
            if not name.endswith(".swift"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT)
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
            for open_ch, close_ch in (("{", "}"), ("(", ")"), ("[", "]")):
                if src.count(open_ch) != src.count(close_ch):
                    errors.append(f"{rel}: дисбаланс {open_ch}{close_ch} "
                                  f"({src.count(open_ch)}/{src.count(close_ch)})")
            if "\u201c" in src or "\u201d" in src:
                errors.append(f"{rel}: «умные» кавычки в коде")
            if "\t" in src:
                warnings.append(f"{rel}: табы в Swift-файле")


def check_swift_palette():
    """CatPalette: каждое обращение pal.X должно существовать, а оба набора
    цветов (full/mono) — перечислять все поля в порядке объявления."""
    path = os.path.join(PROJECT_DIR, "Shared", "CaterpillarArt.swift")
    if not os.path.exists(path):
        errors.append("CaterpillarArt.swift: файла нет")
        return
    with open(path, encoding="utf-8") as fh:
        src = fh.read()

    if "struct CatPalette {" not in src:
        errors.append("CatPalette: структура не найдена")
        return

    struct_body = src.split("struct CatPalette {", 1)[1].split("static let full", 1)[0]
    fields = re.findall(r"^\s{4}var (\w+): Color$", struct_body, flags=re.M)
    if not fields:
        errors.append("CatPalette: не удалось прочитать поля")
        return

    used = sorted(set(re.findall(r"\bpal\.(\w+)", src)))
    missing = [u for u in used if u not in fields]
    if missing:
        errors.append(f"CatPalette: в коде есть несуществующие pal.*: {missing}")
    unused = [f for f in fields if f not in used]
    if unused:
        warnings.append(f"CatPalette: поля без использования: {unused}")

    for name in ("full", "mono"):
        marker = f"static let {name} = CatPalette("
        if marker not in src:
            errors.append(f"CatPalette: нет набора {name}")
            continue
        block = src.split(marker, 1)[1]
        block = block.split("\n    )", 1)[0]
        args = re.findall(r"^\s{8}(\w+):", block, flags=re.M)
        if [a for a in args if a not in fields]:
            errors.append(f"CatPalette.{name}: лишние аргументы "
                          f"{[a for a in args if a not in fields]}")
        if args != fields:
            errors.append(f"CatPalette.{name}: аргументы не совпадают с полями "
                          f"или идут не по порядку ({len(args)} из {len(fields)})")


def main() -> int:
    check_pbxproj()
    check_plists()
    check_assets()
    check_scheme()
    check_swift()
    check_swift_palette()

    for w in warnings:
        print("WARN:", w)
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    print("OK: проект выглядит целым")
    return 0


if __name__ == "__main__":
    sys.exit(main())
