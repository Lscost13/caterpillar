"""Генерирует Caterpillar.xcodeproj (project.pbxproj + shared scheme).

Скрипт детерминированный: все UUID выводятся из текстовых меток, поэтому
проект можно пересобрать в любой момент и получить тот же файл.

    python tools/gen_xcodeproj.py
"""

from __future__ import annotations

import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(ROOT, "Caterpillar")
PROJ_NAME = "Caterpillar"
APP_TARGET = "Caterpillar"
WIDGET_TARGET = "CaterpillarWidget"
BUNDLE_APP = "com.memelab.caterpillar"
BUNDLE_WIDGET = "com.memelab.caterpillar.widget"


def uid(label: str) -> str:
    return hashlib.md5(label.encode("utf-8")).hexdigest()[:24].upper()


# ------------------------------------------------------------------ файлы
FILES = {
    # key: (path inside project, group, kind)
    "app_swift": ("CaterpillarApp.swift", "App", "sourcecode.swift"),
    "content_swift": ("ContentView.swift", "App", "sourcecode.swift"),
    "pose_swift": ("CaterpillarPose.swift", "Shared", "sourcecode.swift"),
    "art_swift": ("CaterpillarArt.swift", "Shared", "sourcecode.swift"),
    "widget_swift": ("CaterpillarWidget.swift", "Widget", "sourcecode.swift"),
    "assets": ("Assets.xcassets", "App", "folder.assetcatalog"),
    "app_plist": ("Info.plist", "App", "text.plist.xml"),
    "widget_plist": ("Info.plist", "Widget", "text.plist.xml"),
}

GROUP_PATHS = {"App": "App", "Shared": "Shared", "Widget": "Widget"}


def ref(key: str) -> str:
    return uid("fileref:" + key)


def build_file(key: str, target: str) -> str:
    return uid(f"buildfile:{key}:{target}")


def main() -> None:
    os.makedirs(os.path.join(PROJECT_DIR, f"{PROJ_NAME}.xcodeproj", "xcshareddata", "xcschemes"),
                exist_ok=True)

    # -------------------------------------------------------------- ids
    proj = uid("project")
    main_group = uid("group:main")
    products_group = uid("group:products")
    groups = {name: uid("group:" + name) for name in GROUP_PATHS}
    app_target_id = uid("target:app")
    widget_target_id = uid("target:widget")
    app_product = uid("product:app")
    widget_product = uid("product:widget")
    sources_app = uid("phase:sources:app")
    sources_widget = uid("phase:sources:widget")
    frameworks_app = uid("phase:frameworks:app")
    frameworks_widget = uid("phase:frameworks:widget")
    resources_app = uid("phase:resources:app")
    resources_widget = uid("phase:resources:widget")
    embed_phase = uid("phase:embed")
    proj_cfg_list = uid("cfglist:project")
    app_cfg_list = uid("cfglist:app")
    widget_cfg_list = uid("cfglist:widget")
    proj_cfg = {c: uid("cfg:project:" + c) for c in ("Debug", "Release")}
    app_cfg = {c: uid("cfg:app:" + c) for c in ("Debug", "Release")}
    widget_cfg = {c: uid("cfg:widget:" + c) for c in ("Debug", "Release")}
    dependency = uid("dependency:app->widget")
    container_proxy = uid("proxy:app->widget")

    app_sources = ["app_swift", "content_swift", "pose_swift", "art_swift"]
    widget_sources = ["widget_swift", "pose_swift", "art_swift"]

    out: list[str] = []
    w = out.append

    w("// !$*UTF8*$!")
    w("{")
    w("\tarchiveVersion = 1;")
    w("\tclasses = {")
    w("\t};")
    w("\tobjectVersion = 56;")
    w("\tobjects = {")
    w("")

    # ---------------------------------------------------------- build files
    w("/* Begin PBXBuildFile section */")
    for key in app_sources:
        w(f"\t\t{build_file(key, 'app')} /* {FILES[key][0]} in Sources */ = {{isa = PBXBuildFile; "
          f"fileRef = {ref(key)} /* {FILES[key][0]} */; }};")
    w(f"\t\t{build_file('assets', 'app')} /* Assets.xcassets in Resources */ = {{isa = PBXBuildFile; "
      f"fileRef = {ref('assets')} /* Assets.xcassets */; }};")
    for key in widget_sources:
        w(f"\t\t{build_file(key, 'widget')} /* {FILES[key][0]} in Sources */ = {{isa = PBXBuildFile; "
          f"fileRef = {ref(key)} /* {FILES[key][0]} */; }};")
    w(f"\t\t{build_file('widget_product', 'app')} /* {WIDGET_TARGET}.appex in Embed Foundation Extensions */ = "
      f"{{isa = PBXBuildFile; fileRef = {widget_product} /* {WIDGET_TARGET}.appex */; "
      "settings = {ATTRIBUTES = (RemoveHeadersOnCopy, ); }; };")
    w("/* End PBXBuildFile section */")
    w("")

    # ------------------------------------------------------ container proxy
    w("/* Begin PBXContainerItemProxy section */")
    w(f"\t\t{container_proxy} /* PBXContainerItemProxy */ = {{")
    w("\t\t\tisa = PBXContainerItemProxy;")
    w(f"\t\t\tcontainerPortal = {proj} /* Project object */;")
    w("\t\t\tproxyType = 1;")
    w(f"\t\t\tremoteGlobalIDString = {widget_target_id};")
    w(f"\t\t\tremoteInfo = {WIDGET_TARGET};")
    w("\t\t};")
    w("/* End PBXContainerItemProxy section */")
    w("")

    # ------------------------------------------------------- copy files
    w("/* Begin PBXCopyFilesBuildPhase section */")
    w(f"\t\t{embed_phase} /* Embed Foundation Extensions */ = {{")
    w("\t\t\tisa = PBXCopyFilesBuildPhase;")
    w("\t\t\tbuildActionMask = 2147483647;")
    w("\t\t\tdstPath = \"\";")
    w("\t\t\tdstSubfolderSpec = 13;")
    w("\t\t\tfiles = (")
    w(f"\t\t\t\t{build_file('widget_product', 'app')} /* {WIDGET_TARGET}.appex in Embed Foundation Extensions */,")
    w("\t\t\t);")
    w("\t\t\tname = \"Embed Foundation Extensions\";")
    w("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    w("\t\t};")
    w("/* End PBXCopyFilesBuildPhase section */")
    w("")

    # ---------------------------------------------------- file references
    w("/* Begin PBXFileReference section */")
    for key, (name, group, kind) in FILES.items():
        w(f"\t\t{ref(key)} /* {name} */ = {{isa = PBXFileReference; "
          f"lastKnownFileType = {kind}; path = {name}; sourceTree = \"<group>\"; }};")
    w(f"\t\t{app_product} /* {APP_TARGET}.app */ = {{isa = PBXFileReference; "
      f"explicitFileType = wrapper.application; includeInIndex = 0; path = {APP_TARGET}.app; "
      "sourceTree = BUILT_PRODUCTS_DIR; };")
    w(f"\t\t{widget_product} /* {WIDGET_TARGET}.appex */ = {{isa = PBXFileReference; "
      f"explicitFileType = \"wrapper.app-extension\"; includeInIndex = 0; path = {WIDGET_TARGET}.appex; "
      "sourceTree = BUILT_PRODUCTS_DIR; };")
    w("/* End PBXFileReference section */")
    w("")

    # ------------------------------------------------------- build phases
    w("/* Begin PBXFrameworksBuildPhase section */")
    for name, pid in (("app", frameworks_app), ("widget", frameworks_widget)):
        w(f"\t\t{pid} /* Frameworks */ = {{")
        w("\t\t\tisa = PBXFrameworksBuildPhase;")
        w("\t\t\tbuildActionMask = 2147483647;")
        w("\t\t\tfiles = (")
        w("\t\t\t);")
        w("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
        w("\t\t};")
    w("/* End PBXFrameworksBuildPhase section */")
    w("")

    # ------------------------------------------------------------- groups
    w("/* Begin PBXGroup section */")
    w(f"\t\t{main_group} = {{")
    w("\t\t\tisa = PBXGroup;")
    w("\t\t\tchildren = (")
    for name in ("App", "Shared", "Widget"):
        w(f"\t\t\t\t{groups[name]} /* {name} */,")
    w(f"\t\t\t\t{products_group} /* Products */,")
    w("\t\t\t);")
    w("\t\t\tsourceTree = \"<group>\";")
    w("\t\t};")
    for name, gid in groups.items():
        children = [k for k, (_, g, _) in FILES.items() if g == name]
        w(f"\t\t{gid} /* {name} */ = {{")
        w("\t\t\tisa = PBXGroup;")
        w("\t\t\tchildren = (")
        for key in children:
            w(f"\t\t\t\t{ref(key)} /* {FILES[key][0]} */,")
        w("\t\t\t);")
        w(f"\t\t\tpath = {GROUP_PATHS[name]};")
        w("\t\t\tsourceTree = \"<group>\";")
        w("\t\t};")
    w(f"\t\t{products_group} /* Products */ = {{")
    w("\t\t\tisa = PBXGroup;")
    w("\t\t\tchildren = (")
    w(f"\t\t\t\t{app_product} /* {APP_TARGET}.app */,")
    w(f"\t\t\t\t{widget_product} /* {WIDGET_TARGET}.appex */,")
    w("\t\t\t);")
    w("\t\t\tname = Products;")
    w("\t\t\tsourceTree = \"<group>\";")
    w("\t\t};")
    w("/* End PBXGroup section */")
    w("")

    # ------------------------------------------------------------ targets
    w("/* Begin PBXNativeTarget section */")
    w(f"\t\t{app_target_id} /* {APP_TARGET} */ = {{")
    w("\t\t\tisa = PBXNativeTarget;")
    w(f"\t\t\tbuildConfigurationList = {app_cfg_list} /* Build configuration list for "
      f"PBXNativeTarget \"{APP_TARGET}\" */;")
    w("\t\t\tbuildPhases = (")
    w(f"\t\t\t\t{sources_app} /* Sources */,")
    w(f"\t\t\t\t{frameworks_app} /* Frameworks */,")
    w(f"\t\t\t\t{resources_app} /* Resources */,")
    w(f"\t\t\t\t{embed_phase} /* Embed Foundation Extensions */,")
    w("\t\t\t);")
    w("\t\t\tbuildRules = (")
    w("\t\t\t);")
    w("\t\t\tdependencies = (")
    w(f"\t\t\t\t{dependency} /* PBXTargetDependency */,")
    w("\t\t\t);")
    w(f"\t\t\tname = {APP_TARGET};")
    w(f"\t\t\tproductName = {APP_TARGET};")
    w(f"\t\t\tproductReference = {app_product} /* {APP_TARGET}.app */;")
    w("\t\t\tproductType = \"com.apple.product-type.application\";")
    w("\t\t};")
    w(f"\t\t{widget_target_id} /* {WIDGET_TARGET} */ = {{")
    w("\t\t\tisa = PBXNativeTarget;")
    w(f"\t\t\tbuildConfigurationList = {widget_cfg_list} /* Build configuration list for "
      f"PBXNativeTarget \"{WIDGET_TARGET}\" */;")
    w("\t\t\tbuildPhases = (")
    w(f"\t\t\t\t{sources_widget} /* Sources */,")
    w(f"\t\t\t\t{frameworks_widget} /* Frameworks */,")
    w(f"\t\t\t\t{resources_widget} /* Resources */,")
    w("\t\t\t);")
    w("\t\t\tbuildRules = (")
    w("\t\t\t);")
    w("\t\t\tdependencies = (")
    w("\t\t\t);")
    w(f"\t\t\tname = {WIDGET_TARGET};")
    w(f"\t\t\tproductName = {WIDGET_TARGET};")
    w(f"\t\t\tproductReference = {widget_product} /* {WIDGET_TARGET}.appex */;")
    w("\t\t\tproductType = \"com.apple.product-type.app-extension\";")
    w("\t\t};")
    w("/* End PBXNativeTarget section */")
    w("")

    # ------------------------------------------------------------ project
    w("/* Begin PBXProject section */")
    w(f"\t\t{proj} /* Project object */ = {{")
    w("\t\t\tisa = PBXProject;")
    w("\t\t\tattributes = {")
    w("\t\t\t\tBuildIndependentTargetsInParallel = 1;")
    w("\t\t\t\tLastSwiftUpdateCheck = 1600;")
    w("\t\t\t\tLastUpgradeCheck = 1600;")
    w("\t\t\t\tTargetAttributes = {")
    w(f"\t\t\t\t\t{app_target_id} = {{")
    w("\t\t\t\t\t\tCreatedOnToolsVersion = 16.0;")
    w("\t\t\t\t\t};")
    w(f"\t\t\t\t\t{widget_target_id} = {{")
    w("\t\t\t\t\t\tCreatedOnToolsVersion = 16.0;")
    w("\t\t\t\t\t};")
    w("\t\t\t\t};")
    w("\t\t\t};")
    w(f"\t\t\tbuildConfigurationList = {proj_cfg_list} /* Build configuration list for PBXProject \"{PROJ_NAME}\" */;")
    w("\t\t\tcompatibilityVersion = \"Xcode 14.0\";")
    w("\t\t\tdevelopmentRegion = ru;")
    w("\t\t\thasScannedForEncodings = 0;")
    w("\t\t\tknownRegions = (")
    w("\t\t\t\tru,")
    w("\t\t\t\ten,")
    w("\t\t\t\tBase,")
    w("\t\t\t);")
    w(f"\t\t\tmainGroup = {main_group};")
    w(f"\t\t\tproductRefGroup = {products_group} /* Products */;")
    w("\t\t\tprojectDirPath = \"\";")
    w("\t\t\tprojectRoot = \"\";")
    w("\t\t\ttargets = (")
    w(f"\t\t\t\t{app_target_id} /* {APP_TARGET} */,")
    w(f"\t\t\t\t{widget_target_id} /* {WIDGET_TARGET} */,")
    w("\t\t\t);")
    w("\t\t};")
    w("/* End PBXProject section */")
    w("")

    # ------------------------------------------------------ resources phase
    w("/* Begin PBXResourcesBuildPhase section */")
    w(f"\t\t{resources_app} /* Resources */ = {{")
    w("\t\t\tisa = PBXResourcesBuildPhase;")
    w("\t\t\tbuildActionMask = 2147483647;")
    w("\t\t\tfiles = (")
    w(f"\t\t\t\t{build_file('assets', 'app')} /* Assets.xcassets in Resources */,")
    w("\t\t\t);")
    w("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    w("\t\t};")
    w(f"\t\t{resources_widget} /* Resources */ = {{")
    w("\t\t\tisa = PBXResourcesBuildPhase;")
    w("\t\t\tbuildActionMask = 2147483647;")
    w("\t\t\tfiles = (")
    w("\t\t\t);")
    w("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    w("\t\t};")
    w("/* End PBXResourcesBuildPhase section */")
    w("")

    # ------------------------------------------------------- sources phase
    w("/* Begin PBXSourcesBuildPhase section */")
    for pid, keys, target in ((sources_app, app_sources, "app"),
                              (sources_widget, widget_sources, "widget")):
        w(f"\t\t{pid} /* Sources */ = {{")
        w("\t\t\tisa = PBXSourcesBuildPhase;")
        w("\t\t\tbuildActionMask = 2147483647;")
        w("\t\t\tfiles = (")
        for key in keys:
            w(f"\t\t\t\t{build_file(key, target)} /* {FILES[key][0]} in Sources */,")
        w("\t\t\t);")
        w("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
        w("\t\t};")
    w("/* End PBXSourcesBuildPhase section */")
    w("")

    # --------------------------------------------------- target dependency
    w("/* Begin PBXTargetDependency section */")
    w(f"\t\t{dependency} /* PBXTargetDependency */ = {{")
    w("\t\t\tisa = PBXTargetDependency;")
    w(f"\t\t\ttarget = {widget_target_id} /* {WIDGET_TARGET} */;")
    w(f"\t\t\ttargetProxy = {container_proxy} /* PBXContainerItemProxy */;")
    w("\t\t};")
    w("/* End PBXTargetDependency section */")
    w("")

    # ----------------------------------------------------- configurations
    project_common = [
        ("ALWAYS_SEARCH_USER_PATHS", "NO"),
        ("CLANG_ANALYZER_NONNULL", "YES"),
        ("CLANG_ENABLE_MODULES", "YES"),
        ("CLANG_ENABLE_OBJC_ARC", "YES"),
        ("CLANG_WARN_BOOL_CONVERSION", "YES"),
        ("CLANG_WARN_DOCUMENTATION_COMMENTS", "YES"),
        ("CLANG_WARN_EMPTY_BODY", "YES"),
        ("CLANG_WARN_ENUM_CONVERSION", "YES"),
        ("CLANG_WARN_INFINITE_RECURSION", "YES"),
        ("CLANG_WARN_INT_CONVERSION", "YES"),
        ("CLANG_WARN_UNREACHABLE_CODE", "YES"),
        ("COPY_PHASE_STRIP", "NO"),
        ("ENABLE_STRICT_OBJC_MSGSEND", "YES"),
        ("ENABLE_USER_SCRIPT_SANDBOXING", "NO"),
        ("GCC_C_LANGUAGE_STANDARD", "gnu17"),
        ("GCC_NO_COMMON_BLOCKS", "YES"),
        ("GCC_WARN_UNDECLARED_SELECTOR", "YES"),
        ("GCC_WARN_UNINITIALIZED_AUTOS", "YES"),
        ("GCC_WARN_UNUSED_FUNCTION", "YES"),
        ("GCC_WARN_UNUSED_VARIABLE", "YES"),
        ("IPHONEOS_DEPLOYMENT_TARGET", "17.0"),
        ("SDKROOT", "iphoneos"),
        ("SUPPORTED_PLATFORMS", "\"iphoneos iphonesimulator\""),
        ("SWIFT_VERSION", "5.0"),
        ("TARGETED_DEVICE_FAMILY", "1"),
    ]
    project_debug = project_common + [
        ("DEBUG_INFORMATION_FORMAT", "dwarf"),
        ("ENABLE_TESTABILITY", "YES"),
        ("GCC_DYNAMIC_NO_PIC", "NO"),
        ("GCC_OPTIMIZATION_LEVEL", "0"),
        ("GCC_PREPROCESSOR_DEFINITIONS", "(\n\t\t\t\t\t\"DEBUG=1\",\n\t\t\t\t\t\"$(inherited)\",\n\t\t\t\t)"),
        ("MTL_ENABLE_DEBUG_INFO", "INCLUDE_SOURCE"),
        ("ONLY_ACTIVE_ARCH", "YES"),
        ("SWIFT_ACTIVE_COMPILATION_CONDITIONS", "DEBUG"),
        ("SWIFT_OPTIMIZATION_LEVEL", "\"-Onone\""),
    ]
    project_release = project_common + [
        ("DEBUG_INFORMATION_FORMAT", "\"dwarf-with-dsym\""),
        ("ENABLE_NS_ASSERTIONS", "NO"),
        ("MTL_ENABLE_DEBUG_INFO", "NO"),
        ("SWIFT_COMPILATION_MODE", "wholemodule"),
        ("SWIFT_OPTIMIZATION_LEVEL", "\"-O\""),
        ("VALIDATE_PRODUCT", "YES"),
    ]

    app_common = [
        ("ASSETCATALOG_COMPILER_APPICON_NAME", "AppIcon"),
        ("CODE_SIGN_STYLE", "Automatic"),
        ("CURRENT_PROJECT_VERSION", "1"),
        ("ENABLE_PREVIEWS", "YES"),
        ("GENERATE_INFOPLIST_FILE", "NO"),
        ("INFOPLIST_FILE", "App/Info.plist"),
        ("IPHONEOS_DEPLOYMENT_TARGET", "17.0"),
        ("LD_RUNPATH_SEARCH_PATHS", "(\n\t\t\t\t\t\"$(inherited)\",\n\t\t\t\t\t\"@executable_path/Frameworks\",\n\t\t\t\t)"),
        ("MARKETING_VERSION", "1.0"),
        ("PRODUCT_BUNDLE_IDENTIFIER", BUNDLE_APP),
        ("PRODUCT_NAME", "\"$(TARGET_NAME)\""),
        ("SWIFT_EMIT_LOC_STRINGS", "YES"),
        ("SWIFT_VERSION", "5.0"),
        ("TARGETED_DEVICE_FAMILY", "1"),
    ]
    widget_common = [
        ("CODE_SIGN_STYLE", "Automatic"),
        ("CURRENT_PROJECT_VERSION", "1"),
        ("ENABLE_PREVIEWS", "YES"),
        ("GENERATE_INFOPLIST_FILE", "NO"),
        ("INFOPLIST_FILE", "Widget/Info.plist"),
        ("IPHONEOS_DEPLOYMENT_TARGET", "17.0"),
        ("LD_RUNPATH_SEARCH_PATHS",
         "(\n\t\t\t\t\t\"$(inherited)\",\n\t\t\t\t\t\"@executable_path/Frameworks\",\n\t\t\t\t\t\"@executable_path/../../Frameworks\",\n\t\t\t\t)"),
        ("MARKETING_VERSION", "1.0"),
        ("PRODUCT_BUNDLE_IDENTIFIER", BUNDLE_WIDGET),
        ("PRODUCT_NAME", "\"$(TARGET_NAME)\""),
        ("SKIP_INSTALL", "YES"),
        ("SWIFT_EMIT_LOC_STRINGS", "YES"),
        ("SWIFT_VERSION", "5.0"),
        ("TARGETED_DEVICE_FAMILY", "1"),
    ]

    w("/* Begin XCBuildConfiguration section */")
    for cfg_name, settings in (("Debug", project_debug), ("Release", project_release)):
        w(f"\t\t{proj_cfg[cfg_name]} /* {cfg_name} */ = {{")
        w("\t\t\tisa = XCBuildConfiguration;")
        w("\t\t\tbuildSettings = {")
        for key, value in settings:
            w(f"\t\t\t\t{key} = {value};")
        w("\t\t\t};")
        w(f"\t\t\tname = {cfg_name};")
        w("\t\t};")
    for cfg_name in ("Debug", "Release"):
        w(f"\t\t{app_cfg[cfg_name]} /* {cfg_name} */ = {{")
        w("\t\t\tisa = XCBuildConfiguration;")
        w("\t\t\tbuildSettings = {")
        for key, value in app_common:
            w(f"\t\t\t\t{key} = {value};")
        w("\t\t\t};")
        w(f"\t\t\tname = {cfg_name};")
        w("\t\t};")
        w(f"\t\t{widget_cfg[cfg_name]} /* {cfg_name} */ = {{")
        w("\t\t\tisa = XCBuildConfiguration;")
        w("\t\t\tbuildSettings = {")
        for key, value in widget_common:
            w(f"\t\t\t\t{key} = {value};")
        w("\t\t\t};")
        w(f"\t\t\tname = {cfg_name};")
        w("\t\t};")
    w("/* End XCBuildConfiguration section */")
    w("")

    w("/* Begin XCConfigurationList section */")
    for lid, label, debug_id, release_id in (
        (proj_cfg_list, f"PBXProject \"{PROJ_NAME}\"", proj_cfg["Debug"], proj_cfg["Release"]),
        (app_cfg_list, f"PBXNativeTarget \"{APP_TARGET}\"", app_cfg["Debug"], app_cfg["Release"]),
        (widget_cfg_list, f"PBXNativeTarget \"{WIDGET_TARGET}\"", widget_cfg["Debug"], widget_cfg["Release"]),
    ):
        w(f"\t\t{lid} /* Build configuration list for {label} */ = {{")
        w("\t\t\tisa = XCConfigurationList;")
        w("\t\t\tbuildConfigurations = (")
        w(f"\t\t\t\t{debug_id} /* Debug */,")
        w(f"\t\t\t\t{release_id} /* Release */,")
        w("\t\t\t);")
        w("\t\t\tdefaultConfigurationIsVisible = 0;")
        w("\t\t\tdefaultConfigurationName = Release;")
        w("\t\t};")
    w("/* End XCConfigurationList section */")
    w("")

    w("\t};")
    w(f"\trootObject = {proj} /* Project object */;")
    w("}")
    w("")

    pbxproj_path = os.path.join(PROJECT_DIR, f"{PROJ_NAME}.xcodeproj", "project.pbxproj")
    with open(pbxproj_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))

    # ------------------------------------------------------------- scheme
    scheme = f"""<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion = "1600" version = "1.7">
   <BuildAction parallelizeBuildables = "YES" buildImplicitDependencies = "YES">
      <BuildActionEntries>
         <BuildActionEntry buildForTesting = "YES" buildForRunning = "YES" buildForProfiling = "YES" buildForArchiving = "YES" buildForAnalyzing = "YES">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "{app_target_id}"
               BuildableName = "{APP_TARGET}.app"
               BlueprintName = "{APP_TARGET}"
               ReferencedContainer = "container:{PROJ_NAME}.xcodeproj">
            </BuildableReference>
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction buildConfiguration = "Debug" selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv = "YES">
      <Testables>
      </Testables>
   </TestAction>
   <LaunchAction buildConfiguration = "Debug" selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB" launchStyle = "0" useCustomWorkingDirectory = "NO" ignoresPersistentStateOnLaunch = "NO" debugDocumentVersioning = "YES" debugServiceExtension = "internal" allowLocationSimulation = "YES">
      <BuildableProductRunnable runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{app_target_id}"
            BuildableName = "{APP_TARGET}.app"
            BlueprintName = "{APP_TARGET}"
            ReferencedContainer = "container:{PROJ_NAME}.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </LaunchAction>
   <ProfileAction buildConfiguration = "Release" shouldUseLaunchSchemeArgsEnv = "YES" savedToolIdentifier = "" useCustomWorkingDirectory = "NO" debugDocumentVersioning = "YES">
      <BuildableProductRunnable runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{app_target_id}"
            BuildableName = "{APP_TARGET}.app"
            BlueprintName = "{APP_TARGET}"
            ReferencedContainer = "container:{PROJ_NAME}.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </ProfileAction>
   <AnalyzeAction buildConfiguration = "Debug">
   </AnalyzeAction>
   <ArchiveAction buildConfiguration = "Release" revealArchiveInOrganizer = "YES">
   </ArchiveAction>
</Scheme>
"""
    scheme_path = os.path.join(PROJECT_DIR, f"{PROJ_NAME}.xcodeproj", "xcshareddata",
                               "xcschemes", f"{APP_TARGET}.xcscheme")
    with open(scheme_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(scheme)

    print("written:", pbxproj_path)
    print("written:", scheme_path)


if __name__ == "__main__":
    main()
