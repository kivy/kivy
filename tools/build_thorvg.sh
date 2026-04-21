#!/bin/bash
# Builds ThorVG as a static library and installs it into Kivy's shared
# dependencies tree so that setup.py can statically link ``kivy.lib.thorvg``.
#
# This script is the single source of truth for:
#   * the pinned ThorVG version,
#   * the Meson build options (engine / loaders / extras / static) that the
#     ``kivy.lib.thorvg._thorvg`` Cython wrapper expects, and
#   * the ugly platform-specific glue (Windows link.exe collision, macOS
#     universal2 via lipo, Ubuntu multiarch libdir) that we previously had
#     to duplicate in multiple CI workflows.
#
# Inputs (all optional):
#   THORVG_VERSION              ThorVG git tag to build (default 1.0.4)
#   THORVG_BUILD_ROOT           Source/build scratch dir
#                               (default: $(pwd)/kivy-dependencies/build/thorvg)
#   THORVG_INSTALL_PREFIX       Final install prefix
#                               (default: $(pwd)/kivy-dependencies/dist)
#   THORVG_MACOS_UNIVERSAL      "1" to build a universal2 (x86_64 + arm64)
#                               static archive on macOS via two meson builds
#                               + lipo. Ignored on non-macOS. Default: "1"
#                               on macOS (matches libpng in the same tree).
#
# Requires ``meson``, ``ninja``, ``curl``, ``tar``, and a working C++14
# toolchain on PATH. On Windows, the caller must have already sourced the
# MSVC environment (e.g. via ``ilammy/msvc-dev-cmd``).

set -e -x

THORVG_VERSION="${THORVG_VERSION:-1.0.4}"
THORVG_BUILD_ROOT="${THORVG_BUILD_ROOT:-$(pwd)/kivy-dependencies/build/thorvg}"
THORVG_INSTALL_PREFIX="${THORVG_INSTALL_PREFIX:-$(pwd)/kivy-dependencies/dist}"

# Detect Windows (git-bash / msys / cygwin) so we can keep the rest of the
# script POSIX-style while still emitting .lib / handling link.exe.
IS_WINDOWS=0
case "${OSTYPE:-}" in
  msys*|cygwin*|win32*) IS_WINDOWS=1 ;;
esac
if [ "${OS:-}" = "Windows_NT" ] && [ "$IS_WINDOWS" = "0" ]; then
  IS_WINDOWS=1
fi

IS_MACOS=0
if [ "$(uname -s 2>/dev/null || echo)" = "Darwin" ]; then
  IS_MACOS=1
fi

# Fast-fail with an actionable message if the tooling is missing. This is
# cheaper than parsing meson/ninja output later.
_missing=""
for tool in meson ninja curl tar; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    _missing="$_missing $tool"
  fi
done
if [ -n "$_missing" ]; then
  echo "FATAL: build_thorvg.sh requires these tools on PATH:$_missing" >&2
  echo "  On CI, install them in the workflow step that precedes this" >&2
  echo "  script, e.g.:" >&2
  echo "    pip install --upgrade meson ninja      # cross-platform" >&2
  echo "    apt-get install -y meson ninja-build   # Ubuntu / Debian" >&2
  echo "    brew install meson ninja               # macOS" >&2
  exit 1
fi

# Default to universal2 on macOS so the static archive matches the other
# dependencies (SDL3, libpng) that ``build_macos_dependencies.sh`` already
# produces universal2. The caller can opt out for a single-arch local
# build via ``THORVG_MACOS_UNIVERSAL=0``.
if [ "$IS_MACOS" = "1" ]; then
  THORVG_MACOS_UNIVERSAL="${THORVG_MACOS_UNIVERSAL:-1}"
else
  THORVG_MACOS_UNIVERSAL=0
fi

mkdir -p "$THORVG_BUILD_ROOT"
mkdir -p "$THORVG_INSTALL_PREFIX"

# ---------------------------------------------------------------------------
# 1. Fetch + extract the ThorVG source tarball (cache-friendly).
# ---------------------------------------------------------------------------
_THORVG_SRC_DIR="$THORVG_BUILD_ROOT/thorvg-$THORVG_VERSION"
_THORVG_TARBALL="$THORVG_BUILD_ROOT/thorvg-$THORVG_VERSION.tar.gz"

if [ ! -d "$_THORVG_SRC_DIR" ]; then
  if [ ! -f "$_THORVG_TARBALL" ]; then
    curl -fsSL \
      -o "$_THORVG_TARBALL" \
      "https://github.com/thorvg/thorvg/archive/refs/tags/v${THORVG_VERSION}.tar.gz"
  fi
  tar -xzf "$_THORVG_TARBALL" -C "$THORVG_BUILD_ROOT"
fi

# ---------------------------------------------------------------------------
# 2. Windows: hide Git-for-Windows's GNU link.exe so Meson picks up MSVC's.
#
# ``ilammy/msvc-dev-cmd`` prepends MSVC's link.exe to cmd/pwsh PATH, but
# steps that run under ``shell: bash`` (including this script) resolve
# Git-for-Windows's ``/usr/bin/link.exe`` (GNU ld-wrapper) first. Meson
# probes link.exe during MSVC detection and bails with
# ``Found GNU link.exe instead of MSVC link.exe``.
# ---------------------------------------------------------------------------
if [ "$IS_WINDOWS" = "1" ]; then
  for candidate in \
    "/c/Program Files/Git/usr/bin/link.exe" \
    "/usr/bin/link.exe" \
    "/usr/bin/link"; do
    if [ -f "$candidate" ] && [ ! -f "${candidate}.disabled" ]; then
      mv "$candidate" "${candidate}.disabled"
      echo "Disabled $candidate"
    fi
  done
fi

# ---------------------------------------------------------------------------
# 3. Configure + compile + install. A helper so we can run the whole thing
#    twice on macOS universal2.
#
# Meson option notes (keep in sync with .github/workflows/test_thorvg_wrapper.yml):
#   -Dextra=           disables the two defaulted ``extra`` features
#                      (``lottie_exp``, ``openmp``). The CPU renderer
#                      unconditionally ``#include <omp.h>`` when the
#                      ``openmp`` extra is enabled, but Apple Clang does
#                      not ship libomp, and the wrapper already calls
#                      ``tvg_engine_init(SW, threads=0)``, so OpenMP is
#                      dead code for Kivy. ``lottie_exp`` pulls in the
#                      JerryScript JS engine for Lottie expression support
#                      (~130 extra compile units); none of the Kivy
#                      providers (svg / svg-image / lottie) need it.
#   --libdir=lib       Meson on Debian/Ubuntu defaults to
#                      ``lib/x86_64-linux-gnu/`` multiarch, which setup.py
#                      does not probe. Force a flat install.
# ---------------------------------------------------------------------------
_thorvg_configure_and_install() {
  local build_dir="$1"
  local prefix="$2"
  shift 2

  pushd "$_THORVG_SRC_DIR"

  # Clean stale build dir from previous invocations (idempotent CI reruns).
  rm -rf "$build_dir"

  meson setup "$build_dir" \
    --buildtype=release \
    --default-library=static \
    --prefix="$prefix" \
    --libdir=lib \
    -Dlog=false \
    -Dstatic=true \
    -Dthreads=false \
    -Dtests=false \
    -Dbindings=capi \
    -Dloaders=svg,lottie,png,jpg,ttf \
    -Dengines=cpu \
    -Dextra= \
    "$@"

  meson compile -C "$build_dir"
  meson install -C "$build_dir"

  popd
}

if [ "$THORVG_MACOS_UNIVERSAL" = "1" ]; then
  # Build each arch into its own prefix, then lipo-merge the static
  # archives on top of the primary prefix.
  _arm64_prefix="$THORVG_BUILD_ROOT/install-arm64"
  _x86_64_prefix="$THORVG_BUILD_ROOT/install-x86_64"
  rm -rf "$_arm64_prefix" "$_x86_64_prefix"

  echo "-- Build ThorVG (arm64)"
  _thorvg_configure_and_install "build-arm64" "$_arm64_prefix" \
    -Dc_args="-arch arm64" \
    -Dcpp_args="-arch arm64" \
    -Dc_link_args="-arch arm64" \
    -Dcpp_link_args="-arch arm64"

  echo "-- Build ThorVG (x86_64)"
  _thorvg_configure_and_install "build-x86_64" "$_x86_64_prefix" \
    -Dc_args="-arch x86_64" \
    -Dcpp_args="-arch x86_64" \
    -Dc_link_args="-arch x86_64" \
    -Dcpp_link_args="-arch x86_64"

  # Install the arm64 tree into the final prefix (headers + pkgconfig are
  # arch-independent) and then overwrite the static archive with a
  # lipo-merged universal2 version.
  mkdir -p "$THORVG_INSTALL_PREFIX/include"
  mkdir -p "$THORVG_INSTALL_PREFIX/lib"
  if [ -d "$_arm64_prefix/include" ]; then
    cp -R "$_arm64_prefix/include/"* "$THORVG_INSTALL_PREFIX/include/"
  fi
  # Preserve pkgconfig .pc files (the .pc file points to ``prefix``,
  # which is arch-independent since we merge the .a in place).
  if [ -d "$_arm64_prefix/lib/pkgconfig" ]; then
    mkdir -p "$THORVG_INSTALL_PREFIX/lib/pkgconfig"
    cp -R "$_arm64_prefix/lib/pkgconfig/"* \
      "$THORVG_INSTALL_PREFIX/lib/pkgconfig/"
  fi

  _arm64_a=$(find "$_arm64_prefix/lib" -maxdepth 2 -name 'libthorvg*.a' | head -n1)
  _x86_64_a=$(find "$_x86_64_prefix/lib" -maxdepth 2 -name 'libthorvg*.a' | head -n1)
  [ -n "$_arm64_a" ] && [ -n "$_x86_64_a" ] || {
    echo "FATAL: could not locate per-arch libthorvg*.a archives" >&2
    exit 1
  }

  _fat_a="$THORVG_INSTALL_PREFIX/lib/$(basename "$_arm64_a")"
  lipo -create "$_arm64_a" "$_x86_64_a" -output "$_fat_a"
  lipo -info "$_fat_a"
else
  _thorvg_configure_and_install "build" "$THORVG_INSTALL_PREFIX"
fi

# ---------------------------------------------------------------------------
# 4. Normalise the installed archive name to ``libthorvg.a`` (Unix) /
#    ``thorvg.lib`` (Windows) so that setup.py's ``libraries=['thorvg']``
#    resolves cleanly without having to know the ThorVG soversion.
# ---------------------------------------------------------------------------
_libdir="$THORVG_INSTALL_PREFIX/lib"
echo "--- Contents of $_libdir ---"
ls -lR "$_libdir" || true

if [ "$IS_WINDOWS" = "1" ]; then
  src=$(find "$_libdir" -maxdepth 3 \
    \( -name 'thorvg*.lib' -o -name 'libthorvg*.a' \) 2>/dev/null | head -n1)
  [ -n "$src" ] || {
    echo "FATAL: no ThorVG static archive found under $_libdir" >&2
    exit 1
  }
  cp "$src" "$_libdir/thorvg.lib"
else
  src=$(find "$_libdir" -maxdepth 3 -name 'libthorvg*.a' 2>/dev/null | head -n1)
  [ -n "$src" ] || {
    echo "FATAL: no ThorVG static archive found under $_libdir" >&2
    exit 1
  }
  cp "$src" "$_libdir/libthorvg.a"
fi

echo "--- After normalisation ---"
ls -l "$_libdir"
