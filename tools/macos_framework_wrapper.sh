#!/bin/bash
# Wrap a macOS / iOS Mach-O dylib into an Apple ``.framework`` bundle.
#
# Kivy's third-party deps mostly ship as ``.framework`` bundles built
# by CMake (libpng, via ``-DPNG_FRAMEWORK=ON``) or Xcode (SDL3 family,
# via ``xcodebuild``). ThorVG is Meson-based and only produces a plain
# ``libthorvg-1.dylib``; this helper rewraps that dylib so it can be
# linked with ``-framework <Name>`` and embedded into Kivy wheels by:
#
#   * ``delocate-wheel`` on macOS desktop (called from
#     ``.github/workflows/osx_wheels_app.yml`` via
#     ``CIBW_REPAIR_WHEEL_COMMAND_MACOS``), and
#   * ``xcodebuild -create-xcframework`` on iOS (pending
#     STAGE 2 changes to ``tools/build_ios_dependencies.sh``;
#     iOS calls this helper once per slice, then combines
#     the per-slice frameworks into a single XCFramework).
#
# Usage
# -----
# ::
#
#   macos_framework_wrapper.sh <dylib> <framework_name> <output_dir> \
#     <headers_dir> [<short_version>] [<bundle_id>]
#
# Arguments:
#   <dylib>           Path to the input dylib (e.g. ``libthorvg-1.dylib``).
#                     Must already be a valid Mach-O (universal2 on
#                     macOS desktop, single-slice on iOS). Not mutated
#                     in-place; the helper works on a copy.
#   <framework_name>  Name of the produced framework (no suffix), e.g.
#                     ``KivyThorVG``.
#   <output_dir>      Directory to create the framework under. Must
#                     already exist.
#   <headers_dir>     Directory whose contents are copied (recursively)
#                     into ``<Name>.framework/Headers/``. For ThorVG:
#                     ``<prefix>/include/thorvg-1``.
#   <short_version>   Optional ``CFBundleShortVersionString`` (default
#                     ``1.0``).
#   <bundle_id>       Optional ``CFBundleIdentifier`` (default
#                     ``org.kivy.<framework_name>``).
#
# Environment:
#   FRAMEWORK_MIN_OS_VERSION  If set (typically on iOS), adds a
#                             ``MinimumOSVersion`` key to Info.plist so
#                             the resulting framework passes App Store
#                             validation. Ignored on macOS desktop.
#
# Layout
# ------
# Non-versioned bundle (iOS cannot consume versioned bundles, and a
# flat layout also sidesteps delocate-wheel's Versions/ handling
# quirks)::
#
#   <output_dir>/<Name>.framework/
#     <Name>                  # dylib, renamed; LC_ID_DYLIB rewritten to
#                             #   @rpath/<Name>.framework/<Name>
#     Headers/                # public C API headers
#     Resources/Info.plist    # minimal bundle metadata

set -e -u

if [ "$#" -lt 4 ]; then
  echo "Usage: $0 <dylib> <framework_name> <output_dir> <headers_dir> [<short_version>] [<bundle_id>]" >&2
  exit 2
fi

dylib="$1"
framework_name="$2"
output_dir="$3"
headers_dir="$4"
short_version="${5:-1.0}"
bundle_id="${6:-org.kivy.${framework_name}}"

if [ ! -f "$dylib" ]; then
  echo "FATAL: input dylib not found: $dylib" >&2
  exit 1
fi
if [ ! -d "$output_dir" ]; then
  echo "FATAL: output directory does not exist: $output_dir" >&2
  exit 1
fi
if [ ! -d "$headers_dir" ]; then
  echo "FATAL: headers directory does not exist: $headers_dir" >&2
  exit 1
fi

fw_root="$output_dir/$framework_name.framework"

# Rebuild from scratch so stale contents from a previous run do not
# sneak in (e.g. old Info.plist with a different version, or a header
# that upstream ThorVG has since deleted).
rm -rf "$fw_root"
mkdir -p "$fw_root/Headers"
mkdir -p "$fw_root/Resources"

# 1. Install the binary. Using ``cp`` (not ``mv``) so the caller's
#    ``dist/lib`` copy is preserved both for debugging and for the
#    legacy dylib-probing fallback in ``setup.py::determine_thorvg_flags``
#    (used by devs who point ``KIVY_THORVG_LIB_DIR`` directly at a
#    raw Meson install).
cp "$dylib" "$fw_root/$framework_name"
chmod 644 "$fw_root/$framework_name"

# 2. Rewrite ``LC_ID_DYLIB`` so dyld resolves the framework via
#    ``@rpath/<Name>.framework/<Name>``. Without this, an extension
#    that links against this framework would bake the original dylib
#    path (e.g. ``kivy-dependencies/dist/lib/libthorvg-1.dylib``) into
#    its ``LC_LOAD_DYLIB`` and break at import time once the wheel is
#    installed anywhere else.
install_name_tool -id \
  "@rpath/$framework_name.framework/$framework_name" \
  "$fw_root/$framework_name"

# 3. Populate Headers/. ``cp -a`` preserves symlinks, which matters
#    for some upstream include trees (not ThorVG today, but the helper
#    wants to stay generic).
cp -a "$headers_dir/." "$fw_root/Headers/"

# 4. Minimal Info.plist. ``CFBundleExecutable`` must match the binary
#    filename so Launch Services + dyld agree on what to load. On iOS
#    the caller sets ``FRAMEWORK_MIN_OS_VERSION`` so App Store
#    validation passes.
min_os_entry=""
if [ -n "${FRAMEWORK_MIN_OS_VERSION:-}" ]; then
  min_os_entry="
	<key>MinimumOSVersion</key>
	<string>${FRAMEWORK_MIN_OS_VERSION}</string>"
fi

cat > "$fw_root/Resources/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTD/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>en</string>
	<key>CFBundleExecutable</key>
	<string>${framework_name}</string>
	<key>CFBundleIdentifier</key>
	<string>${bundle_id}</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>${framework_name}</string>
	<key>CFBundlePackageType</key>
	<string>FMWK</string>
	<key>CFBundleShortVersionString</key>
	<string>${short_version}</string>
	<key>CFBundleSignature</key>
	<string>????</string>
	<key>CFBundleVersion</key>
	<string>${short_version}</string>${min_os_entry}
</dict>
</plist>
PLIST

echo "-- Wrapped $dylib -> $fw_root"
otool -D "$fw_root/$framework_name" || true
file "$fw_root/$framework_name" || true
