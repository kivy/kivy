#!/bin/bash
# Builds ThorVG and installs it into Kivy's shared dependencies tree so
# that setup.py can link ``kivy.lib.thorvg._thorvg`` against it. Produces
# a static archive by default; set ``THORVG_SHARED=1`` for a shared
# library (used by Linux + macOS desktop wheels).
#
# This script is the single source of truth for:
#   * the pinned ThorVG version,
#   * the Meson build options (engine / loaders / extras / static-vs-shared)
#     that the ``kivy.lib.thorvg._thorvg`` Cython wrapper expects, and
#   * the ugly platform-specific glue (Windows link.exe collision, macOS
#     universal2 via multi-arch Apple Clang, Ubuntu multiarch libdir)
#     that we previously had to duplicate in multiple CI workflows.
#
# Inputs (all optional):
#   THORVG_VERSION              ThorVG git tag to build (default 1.0.4)
#   THORVG_BUILD_ROOT           Source/build scratch dir
#                               (default: $(pwd)/kivy-dependencies/build/thorvg)
#   THORVG_INSTALL_PREFIX       Final install prefix
#                               (default: $(pwd)/kivy-dependencies/dist)
#   THORVG_SHARED               "1" to build a shared library
#                               (``--default-library=shared -Dstatic=false``)
#                               instead of the default static archive. Kivy's
#                               desktop wheels use shared on Linux (bundled
#                               into ``kivy.libs/`` by ``auditwheel repair``)
#                               and on macOS (wrapped as ``KivyThorVG.framework``
#                               and embedded by ``delocate-wheel``). Windows
#                               stays on the static default because Kivy's
#                               Windows pipeline does not run a wheel-repair
#                               step. Default: "0".
#   THORVG_MACOS_UNIVERSAL      "1" to build a universal2 (x86_64 + arm64)
#                               archive/dylib on macOS by passing both
#                               ``-arch`` flags to Apple Clang in a single
#                               meson invocation (same trick libpng uses via
#                               ``CMAKE_OSX_ARCHITECTURES="x86_64;arm64"``).
#                               Ignored on non-macOS. Default: "1" on macOS
#                               (matches libpng in the same tree).
#
# Requires ``meson``, ``ninja``, ``curl``, ``tar``, and a working C++14
# toolchain on PATH. On Windows, the caller must have already sourced the
# MSVC environment (e.g. via ``ilammy/msvc-dev-cmd``).

set -e -x

THORVG_VERSION="${THORVG_VERSION:-1.0.4}"
THORVG_BUILD_ROOT="${THORVG_BUILD_ROOT:-$(pwd)/kivy-dependencies/build/thorvg}"
THORVG_INSTALL_PREFIX="${THORVG_INSTALL_PREFIX:-$(pwd)/kivy-dependencies/dist}"
THORVG_SHARED="${THORVG_SHARED:-0}"

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
# 3. Configure + compile + install.
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
#   -Dloaders=...      svg + lottie + ttf for vector content, plus png +
#                      jpg so that raster assets *embedded* in SVG
#                      data-URIs and Lottie ``<image>`` layers decode.
#                      ThorVG ships two implementations per raster
#                      format (see thorvg/src/loaders/meson.build):
#                        * ``-Dstatic=true`` (our Windows path): always
#                          uses the **bundled** self-contained codecs -
#                          LodePNG for PNG, JPGd for JPEG - with no
#                          external library deps.
#                        * ``-Dstatic=false`` (our Linux + macOS shared
#                          path): tries pkg-config for ``libpng`` +
#                          ``libturbojpeg`` first, else **falls back
#                          to the same bundled codecs**. The
#                          ``PKG_CONFIG_LIBDIR`` isolation below
#                          prevents Meson from discovering Homebrew's
#                          arm64-only ``libpng.pc`` on Apple Silicon
#                          runners (which would otherwise break the
#                          universal2 x86_64 slice with ``found
#                          architecture 'arm64', required architecture
#                          'x86_64'``), so the fallback kicks in and
#                          we get self-contained bundled codecs on
#                          every desktop platform.
#                      Net effect: embedded raster assets decode
#                      identically on Linux / macOS / Windows, with
#                      zero extra dependency pins to track / audit.
#   --libdir=lib       Meson on Debian/Ubuntu defaults to
#                      ``lib/x86_64-linux-gnu/`` multiarch, which setup.py
#                      does not probe. Force a flat install.
# ---------------------------------------------------------------------------
if [ "$THORVG_SHARED" = "1" ]; then
  _THORVG_DEFAULT_LIBRARY="shared"
  _THORVG_STATIC_OPT="false"
else
  _THORVG_DEFAULT_LIBRARY="static"
  _THORVG_STATIC_OPT="true"
fi

_thorvg_configure_and_install() {
  local build_dir="$1"
  local prefix="$2"
  shift 2

  pushd "$_THORVG_SRC_DIR"

  # Clean stale build dir from previous invocations (idempotent CI reruns).
  rm -rf "$build_dir"

  # Scope pkg-config's search path to Kivy's own dependency tree so
  # Meson can't discover the host system's / Homebrew's libpng or
  # libturbojpeg. We explicitly *want* no match here: ThorVG's Meson
  # build then falls back to its bundled LodePNG / JPGd codecs (see
  # ``src/loaders/meson.build`` - ``if not png_dep.found(): subdir('png')``),
  # which is the same decoder path the ``-Dstatic=true`` / Windows
  # build already takes.
  #
  # This matters specifically on macOS universal2 builds: Homebrew on
  # Apple Silicon runners ships ``libpng.dylib`` / ``libturbojpeg.dylib``
  # as arm64-only, and Meson's default pkg-config path
  # (``/opt/homebrew/lib/pkgconfig``) would otherwise be picked up,
  # link-time-resolving every symbol and exploding the x86_64 slice of
  # ``libthorvg-1.dylib`` with ``found architecture 'arm64', required
  # architecture 'x86_64'``. ``PKG_CONFIG_LIBDIR`` (not
  # ``PKG_CONFIG_PATH``) is the right env var because it *replaces*
  # the default search path; prepending would still let Homebrew win
  # whenever our dist tree is empty.
  #
  # On Linux the net effect is the same - system pkg-config stays
  # out of the mix - which keeps libthorvg-1.so.* self-contained and
  # reproducible regardless of which manylinux image contains which
  # libpng version.
  export PKG_CONFIG_LIBDIR="$THORVG_INSTALL_PREFIX/lib/pkgconfig"
  echo "-- PKG_CONFIG_LIBDIR=$PKG_CONFIG_LIBDIR (bundled-loader fallback)"

  meson setup "$build_dir" \
    --buildtype=release \
    --default-library="$_THORVG_DEFAULT_LIBRARY" \
    --prefix="$prefix" \
    --libdir=lib \
    -Dlog=false \
    -Dstatic="$_THORVG_STATIC_OPT" \
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
  # Single-invocation universal2 build (matches libpng's CMake
  # ``-DCMAKE_OSX_ARCHITECTURES="x86_64;arm64"`` path in
  # tools/build_macos_dependencies.sh).
  #
  # Passing multiple ``-arch`` flags to Apple Clang produces universal2
  # object files in a single compile; ``ar`` / ``libtool`` then archive
  # them directly into a fat static library - no lipo-merge, no second
  # meson invocation, and critically no arm64 cross-compile sanity check
  # that would fail on Intel runners (``macos-15-intel`` in
  # test_osx_python.yml) where Meson can't execute the freshly built
  # arm64 ``sanitycheckcpp.exe`` binary (``[Errno 86] Bad CPU type in
  # executable``). Universal2 binaries run natively on both arches so
  # the sanity check succeeds regardless of host CPU.
  echo "-- Build ThorVG (universal2 via single meson invocation)"
  _thorvg_configure_and_install "build" "$THORVG_INSTALL_PREFIX" \
    -Dc_args="-arch x86_64 -arch arm64" \
    -Dcpp_args="-arch x86_64 -arch arm64" \
    -Dc_link_args="-arch x86_64 -arch arm64" \
    -Dcpp_link_args="-arch x86_64 -arch arm64"

  # Verify the produced archive / dylib is actually fat. ``lipo -info``
  # covers both ``libthorvg-1.a`` (static path) and
  # ``libthorvg-1.dylib`` (``THORVG_SHARED=1`` path); Apple's linker
  # handles universal2 for both output kinds given the multi-``-arch``
  # flags above.
  _fat_bin=$(find "$THORVG_INSTALL_PREFIX/lib" -maxdepth 2 \
    \( -name 'libthorvg*.a' -o -name 'libthorvg*.dylib' \) | head -n1)
  if [ -n "$_fat_bin" ]; then
    lipo -info "$_fat_bin" || true
  fi
else
  _thorvg_configure_and_install "build" "$THORVG_INSTALL_PREFIX"
fi

# ---------------------------------------------------------------------------
# 4. Post-install: verify and (for static builds) normalise the archive name.
#
# Static builds:
#   Rename the produced archive to ``libthorvg.a`` (Unix) / ``thorvg.lib``
#   (Windows) so that setup.py's ``libraries=['thorvg']`` resolves cleanly
#   without having to know the ThorVG soversion.
#
# Shared builds (``THORVG_SHARED=1``):
#   No renaming - setup.py uses ``-lthorvg-1`` which matches Meson's
#   versioned output (``libthorvg-1.so.X`` on Linux, ``libthorvg-1.dylib``
#   on macOS). ``auditwheel repair`` / ``delocate-wheel`` / the framework
#   wrapper in ``build_macos_dependencies.sh`` take it from there. We still
#   fail fast here if Meson silently produced only a static archive.
# ---------------------------------------------------------------------------
_libdir="$THORVG_INSTALL_PREFIX/lib"
echo "--- Contents of $_libdir ---"
ls -lR "$_libdir" || true

if [ "$THORVG_SHARED" = "1" ]; then
  if [ "$IS_MACOS" = "1" ]; then
    _shared_files=$(find "$_libdir" -maxdepth 3 -name 'libthorvg*.dylib' \
      2>/dev/null)
  else
    _shared_files=$(find "$_libdir" -maxdepth 3 -name 'libthorvg*.so*' \
      2>/dev/null)
  fi
  if [ -z "$_shared_files" ]; then
    echo "FATAL: THORVG_SHARED=1 but no shared ThorVG library found under $_libdir" >&2
    exit 1
  fi
  echo "--- ThorVG shared library (THORVG_SHARED=1) ---"
  echo "$_shared_files"
elif [ "$IS_WINDOWS" = "1" ]; then
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
