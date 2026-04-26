# Phase 2 — iOS ThorVG XCFramework

Personal design note. Not for circulation. Captures the iOS plan after
Phase 1 desktop is done.

> **Reading this on the Mac**: this file is in the Windows `KivyPRs/`
> workspace and won't transfer with a fresh clone. Either copy via
> cloud / USB, or just re-read it from the Cursor chat history (it's
> rendered inline in the conversation that made it).

---

## 1. State of the world (entering Phase 2)

### Phase 1 — done, all four PRs green
| PR | Branch | Status |
|---|---|---|
| #9297 | `feature/thorvg-cython` | green, merge first |
| #9273 | `feature/svg-image-provider` | green, rebased on #9297 |
| #9284 | `feature/svg-widget` | green, rebased on #9297 |
| #9293 | `feature/lottie-provider` | green, rebased on #9297 |

Maintainer (`@misl6`) has confirmed merge order.

### Phase 1 → Phase 2 contract
Phase 1 deliberately produced two reusable pieces specifically for
Phase 2:

1. **`tools/build_thorvg.sh`** — Meson build script with a
   `THORVG_SHARED=1` knob, universal-arch handling, and bundled
   PNG / JPG codecs via `-Dstatic=true`. Already proven to produce
   `libthorvg-1.dylib` on macOS universal2.
2. **`tools/macos_framework_wrapper.sh`** — wraps a Mach-O dylib into a
   non-versioned `.framework` bundle. Already built with iOS reuse
   in mind: accepts `FRAMEWORK_MIN_OS_VERSION` env var and rewrites
   `LC_ID_DYLIB` to `@rpath/<Name>.framework/<Name>`.

Phase 2's job is to wire these two into Kivy's existing iOS pipeline.

### What's already in `kivy/kivy` (we don't have to build it)
Read these to understand the existing iOS pipeline before extending:

- `tools/build_ios_dependencies.sh` — single canonical iOS dep
  builder, runs once before cibuildwheel. Builds SDL3 / SDL3_image /
  SDL3_mixer / SDL3_ttf and unpacks ANGLE. Each output is an
  **`.xcframework`** under `ios-kivy-dependencies/dist/Frameworks/`.
- `.github/workflows/ios_wheels.yml` — gated on `[build wheel]` /
  `[build wheel ios]` / tag / schedule. Builds three slices via
  cibuildwheel (`CIBW_ARCHS: "arm64_iphoneos arm64_iphonesimulator x86_64_iphonesimulator"`).
  Cache key is `hashFiles('tools/build_ios_dependencies.sh')` — adding
  ThorVG to that script automatically invalidates the cache exactly
  once.
- `tools/add-ios-frameworks.py` — runs **after** cibuildwheel.
  Auto-discovers every `*.xcframework` under
  `$KIVY_DEPS_ROOT/dist/Frameworks/` and packs each into the wheel
  under `.frameworks/`. **No allowlist update needed** — once we
  produce `KivyThorVG.xcframework` in that directory, it's picked up
  for free.
- `setup.py` lines 201–269 — `plat_options['ios']['frameworks']` dict.
  Each entry points at the per-slice `.framework` directly under the
  xcframework via the `plat_arch` key
  (`ios-arm64` for device, `ios-arm64_x86_64-simulator` for sim). This is
  what `setup.py` actually links against during cibuildwheel.

### Pattern to copy: SDL3
SDL3 is the closest analogue (it's a real C lib, not a CMake-based
download like ANGLE). Its `tools/build_ios_dependencies.sh` block is:

```bash
for platform in "iOS" "iOS Simulator"; do
  platform_arg=$([ "$platform" = "iOS" ] && echo "iphoneos" || echo "iphonesimulator")
  xcodebuild archive -scheme SDL3 ... -destination "generic/platform=$platform" ...
done
xcodebuild -create-xcframework \
  -framework Xcode/SDL/build/Release-iphoneos.xcarchive/Products/Library/Frameworks/SDL3.framework \
  -framework Xcode/SDL/build/Release-iphonesimulator.xcarchive/Products/Library/Frameworks/SDL3.framework \
  -output ../../dist/Frameworks/SDL3.xcframework
```

Notes:
- **Two slices in the xcframework**, not three. iOS device
  (`iphoneos`, arm64) + iOS Simulator (`iphonesimulator`,
  arm64+x86_64 universal). cibuildwheel still expands to three
  wheels because the simulator slice is universal but the wheel
  ABI tags are per-arch.
- SDL3 ships an Xcode project, so `xcodebuild` does it directly.
  ThorVG only ships Meson, so we have to drive Meson manually with
  per-platform SDK + `-arch` flags. Same shape, different tooling.

---

## 2. Phase 2 architecture

### Deliverable layout
```
ios-kivy-dependencies/dist/Frameworks/
├── SDL3.xcframework/         (existing, unchanged)
├── SDL3_image.xcframework/   (existing, unchanged)
├── SDL3_mixer.xcframework/   (existing, unchanged)
├── SDL3_ttf.xcframework/     (existing, unchanged)
├── libEGL.xcframework/       (existing, unchanged — from ANGLE)
├── libGLESv2.xcframework/    (existing, unchanged — from ANGLE)
└── KivyThorVG.xcframework/   (new)
    ├── ios-arm64/
    │   └── KivyThorVG.framework/
    │       ├── KivyThorVG     (libthorvg-1.dylib renamed, LC_ID_DYLIB rewritten)
    │       ├── Headers/       (thorvg_capi.h)
    │       └── Info.plist
    └── ios-arm64_x86_64-simulator/
        └── KivyThorVG.framework/
            ├── KivyThorVG     (universal libthorvg-1.dylib for sim)
            ├── Headers/
            └── Info.plist
```

### Build pipeline (extension to `tools/build_ios_dependencies.sh`)

```bash
# After SDL3_ttf block — add this:
echo "-- Build ThorVG (universal iOS XCFramework)"

# Per-slice build via existing tools/build_thorvg.sh
# (drives Meson with -arch flags + iOS SDK paths via THORVG_IOS env)
for slice in iphoneos iphonesimulator; do
  THORVG_IOS=$slice \
  THORVG_SHARED=1 \
  THORVG_INSTALL_PREFIX="$(pwd)/../dist/thorvg-$slice" \
  bash $REPO/tools/build_thorvg.sh

  bash $REPO/tools/macos_framework_wrapper.sh \
    --dylib "$(pwd)/../dist/thorvg-$slice/lib/libthorvg-1.1.dylib" \
    --name KivyThorVG \
    --output-dir "$(pwd)/../dist/thorvg-$slice/Frameworks" \
    --headers "$(pwd)/../dist/thorvg-$slice/include/thorvg-1"
  # FRAMEWORK_MIN_OS_VERSION=14.0 already supported by the wrapper
done

xcodebuild -create-xcframework \
  -framework "$(pwd)/../dist/thorvg-iphoneos/Frameworks/KivyThorVG.framework" \
  -framework "$(pwd)/../dist/thorvg-iphonesimulator/Frameworks/KivyThorVG.framework" \
  -output ../../dist/Frameworks/KivyThorVG.xcframework
```

### Meson cross-file approach (in `tools/build_thorvg.sh`)

ThorVG's universal2 macOS path passes `-arch x86_64 -arch arm64`
directly to Apple Clang via `-Dc_args` / `-Dcpp_args`. iOS needs the
same idea plus the right SDK and deployment target:

| Slice | `-arch` | SDK | Deployment target |
|---|---|---|---|
| `iphoneos` | `arm64` | `iphoneos` (`xcrun --sdk iphoneos --show-sdk-path`) | `-mios-version-min=14.0` |
| `iphonesimulator` | `arm64 x86_64` | `iphonesimulator` | `-mios-simulator-version-min=14.0` |

Meson invocation per slice (rough):

```bash
SDK_PATH=$(xcrun --sdk $THORVG_IOS --show-sdk-path)
ARCHS=$([ "$THORVG_IOS" = "iphoneos" ] && echo "-arch arm64" || echo "-arch arm64 -arch x86_64")
MINVER=$([ "$THORVG_IOS" = "iphoneos" ] \
  && echo "-mios-version-min=14.0" \
  || echo "-mios-simulator-version-min=14.0")

meson setup build-$THORVG_IOS \
  --cross-file <(generate_ios_cross_file) \
  --buildtype=release --default-library=shared \
  --prefix="$THORVG_INSTALL_PREFIX" --libdir=lib \
  -Dlog=false -Dstatic=true -Dthreads=false \
  -Dtests=false -Dbindings=capi \
  -Dloaders=svg,lottie,png,jpg,ttf -Dengines=cpu -Dextra= \
  -Dc_args="-isysroot $SDK_PATH $ARCHS $MINVER" \
  -Dcpp_args="-isysroot $SDK_PATH $ARCHS $MINVER" \
  -Dc_link_args="-isysroot $SDK_PATH $ARCHS $MINVER" \
  -Dcpp_link_args="-isysroot $SDK_PATH $ARCHS $MINVER -lc++"
```

The cross-file is needed because iOS is a different host than the
build machine; without it Meson assumes macOS conventions and the
SDK path won't bind to the right libc++ headers / sysroot.

**Decision point** for the cross-file: ThorVG upstream doesn't ship
any. Two options:

- **2A**: Generate the cross-file inline in `tools/build_thorvg.sh`
  via heredoc (single source of truth, no extra files).
- **2B**: Add a static `tools/meson-cross-ios-{device,sim}.ini` pair.
  Cleaner, but adds two files. Probably better long-term.

Lean toward **2B**. Two-file overhead is small and Meson cross-files
are way easier to read as standalone INI than embedded heredoc.

### `setup.py` extension

Mirror SDL3 in `plat_options['ios']`:

```python
thorvg_xc = join(KIVY_DEPS_ROOT, 'dist', 'Frameworks', 'KivyThorVG.xcframework')
thorvg_fw = join(thorvg_xc, plat_arch, 'KivyThorVG.framework')
thorvg_headers = join(thorvg_fw, 'Headers')

ios_data['frameworks']['KivyThorVG'] = {
    'path': thorvg_fw,
    'headers': thorvg_headers,
    'xc': thorvg_xc,
}
```

Then in `determine_thorvg_flags()`, add an `ios` branch that mirrors
the existing `darwin + use_osx_frameworks` branch:

```python
if platform == 'ios':
    ios_frameworks = plat_options['ios']['frameworks']
    thorvg_fw = ios_frameworks['KivyThorVG']
    return {
        'include_dirs': [thorvg_fw['headers']],
        'extra_link_args': [
            '-F', dirname(thorvg_fw['path']),
            '-framework', 'KivyThorVG',
            '-Wl,-rpath,@executable_path/Frameworks',
        ],
        'libraries': [],
        'define_macros': [],
    }
```

No `TVG_STATIC` — same as macOS desktop. The `@executable_path/Frameworks`
rpath matches what Kivy's iOS bundle layout uses (look at how SDL3 does
it; should be identical).

**Important**: `setup.py:971` currently bundles `'ios'` in with
`('win32', 'android', 'ios')` as a "static linking" platform.
That branch needs to keep `'win32'` and `'android'` but remove
`'ios'` once the framework path lands. **Verify before changing**:
read the surrounding `_thorvg.pyx` extension block to confirm there
isn't another `'ios'` static-only path I'm missing.

### `tools/add-ios-frameworks.py`
**No change.** Auto-discovery picks up `KivyThorVG.xcframework` from
`$KIVY_DEPS_ROOT/dist/Frameworks/` once it exists.

---

## 3. Implementation order

Single PR, single branch (`feature/thorvg-ios-wheel`). Six commits,
in this order. Every commit should leave the tree green for desktop —
iOS CI is gated on `[build wheel ios]` so it only runs when we ask.

1. **Add iOS cross-files** — `tools/meson-cross-ios-{device,sim}.ini`.
   Standalone, no integration. Sanity check: `meson setup --cross-file`
   succeeds on a hello-world meson project.
2. **Extend `tools/build_thorvg.sh` with `THORVG_IOS` mode** — when
   set, picks the right cross-file, SDK, archs, min-version flags.
   Other code paths (Linux shared, macOS universal2, Windows static)
   unchanged. **Sanity check on the Mac**: run
   `THORVG_IOS=iphoneos THORVG_SHARED=1 ./tools/build_thorvg.sh`
   manually, `lipo -info` the output dylib, `otool -L` to verify
   `LC_ID_DYLIB` and rpath.
3. **Extend `tools/build_ios_dependencies.sh` with the ThorVG block**
   — per-slice Meson build, framework wrap, xcframework merge.
   **Sanity check**: run the whole script clean
   (`rm -rf ios-kivy-dependencies && ./tools/build_ios_dependencies.sh`),
   inspect the produced `KivyThorVG.xcframework`, run
   `xcrun xcodebuild -checkFirstLaunchStatus` on it (or
   `plutil -p */Info.plist`).
4. **Extend `setup.py::plat_options['ios']` and `determine_thorvg_flags()`**
   — wire the framework into the iOS link line. Verify
   `setup.py:971` static-platform list updated correctly.
5. **Local `cibuildwheel` for one slice** — run
   `CIBW_PLATFORM=ios CIBW_ARCHS=arm64_iphoneos python -m cibuildwheel`,
   inspect the produced wheel:
   - `unzip -l <wheel>` — `.frameworks/KivyThorVG.xcframework/...`
     present?
   - `unzip -p <wheel> kivy/lib/thorvg/_thorvg*.so | otool -L -` —
     `@rpath/KivyThorVG.framework/KivyThorVG` resolves?
   - Run `add-ios-frameworks.py` on it manually if cibuildwheel
     doesn't run that step locally.
6. **Push `[build wheel ios]` commit** — let CI build all three
   slices, download all three wheels, repeat the same inspection.
   When green, open PR.

---

## 4. Open questions to resolve on the Mac

These are deliberate gaps. Resolve when you have your hands on the
actual artifact, not from the spec.

### Q1. iOS deployment target
Kivy probably has a canonical minimum iOS version. **Find it before
choosing**. Check:
- `tools/build_ios_dependencies.sh` (xcodebuild invocations may
  inherit it from the upstream Xcode project — check
  `IPHONEOS_DEPLOYMENT_TARGET` overrides),
- any `.xcconfig` files in the kivy tree,
- `cibuildwheel` defaults for iOS (it has its own minimum).

If you can't find a canonical answer, **iOS 14.0** is a safe pick —
matches CPython 3.13's iOS Tier 3 floor. Don't pick higher than
whatever SDL3 / ANGLE were built with, or our framework will have a
higher minimum than the rest of the iOS Kivy bundle and refuse to
load on older devices.

### Q2. Bitcode
Apple deprecated bitcode in Xcode 14. ThorVG's Meson build doesn't
emit bitcode by default. Verify SDL3 / ANGLE in the same wheel are
also bitcode-free; if everyone agrees, no flags needed. If anyone
emits it, we'll have to either match or strip. Likely a non-issue
in 2026 Xcode.

### Q3. Framework signing
Frameworks bundled into a Python wheel aren't signed; the embedding
app signs everything at app-bundle time (`codesign --deep` /
`codesign --force` on the bundle's `Frameworks/` directory). Verify
this works with our framework structure by checking that SDL3.xcframework
has the same layout (Mach-O at top of `Foo.framework/`, no
`Foo.framework/Versions/A/`) — that's why `macos_framework_wrapper.sh`
emits non-versioned frameworks (the macOS desktop comment in
that file explains).

### Q4. Threads option (`-Dthreads=false`)
We currently disable ThorVG's internal task scheduler on all
platforms because the Cython wrapper calls
`tvg_engine_init(SW, threads=0)`. iOS would benefit from threading
on multi-core devices but the default is fine for parity with
desktop wheels — iOS already pays a Python GIL tax that dwarfs the
single-core ThorVG cost. **Defer turning threads back on** until
someone profiles a real iOS Lottie scene and proves it matters.

### Q5. xcframework slice naming
Apple's xcframework naming convention is finicky. The slice
directory inside the xcframework must be named exactly
`ios-arm64` for device and `ios-arm64_x86_64-simulator` for the
universal simulator slice. `xcodebuild -create-xcframework`
generates these names automatically from the platform/architecture
of each input framework — but verify by `ls` on the produced
xcframework and confirm those exact names match
`plat_options['ios']['platform_arch']` (setup.py line 206).
If they differ, setup.py won't find the per-slice .framework and
the build will fail with a missing-framework error.

---

## 5. Validation checklist (before opening PR)

Run all of these locally on the Mac (Intel) **before** pushing
`[build wheel ios]`:

- [ ] `tools/build_thorvg.sh` (no env vars) — desktop universal2
      build still produces `libthorvg-1.dylib`, `lipo -info` shows
      both arches. Regression guard.
- [ ] `THORVG_IOS=iphoneos tools/build_thorvg.sh` — produces
      arm64-only `libthorvg-1.dylib`, `otool -hv` shows
      `IPHONEOS_VERSION_MIN` matches Q1's chosen target.
- [ ] `THORVG_IOS=iphonesimulator tools/build_thorvg.sh` — produces
      universal arm64+x86_64 dylib, `IPHONEOS_SIMULATOR_VERSION_MIN`
      set.
- [ ] `tools/build_ios_dependencies.sh` end-to-end clean run.
      Cache invalidates correctly (delete `ios-kivy-dependencies/`
      first).
- [ ] `find ios-kivy-dependencies/dist/Frameworks/KivyThorVG.xcframework`
      shows the two expected slice dirs.
- [ ] `cibuildwheel` for `arm64_iphoneos` produces a wheel; unpack
      it; `_thorvg*.so | otool -L` shows `@rpath/KivyThorVG.framework/KivyThorVG`.
- [ ] Run `python ./tools/add-ios-frameworks.py wheelhouse/`;
      re-unzip the wheel; `.frameworks/KivyThorVG.xcframework/`
      present.
- [ ] Optional but valuable: install the wheel into a local Briefcase
      / Toga iOS app, build for simulator, run and import
      `kivy.lib.thorvg`. Catches anything CI misses.

---

## 6. PR submission

- Branch: `feature/thorvg-ios-wheel` (off `master`, NOT off
  `feature/thorvg-cython` — by the time we open this, #9297 will
  have merged).
- Title: `Build KivyThorVG.xcframework for iOS wheels`
- Body: Stack-link to the four merged STAGE 1 PRs. Note that this
  PR does **not** require any Phase 1 changes (#9297 etc. must
  already be on master so the Cython wrapper exists to be linked
  against).
- Reviewers: `@misl6` for the iOS pipeline shape, `@psychowasp`
  for the SVG/Lottie consumer perspective, `@T-Dynamos` cc'd to
  signal that Android comes next.
- CI gate: include `[build wheel ios]` in the first commit message
  so the iOS wheel job runs without waiting for a tag.

---

## 7. Out of scope (Phase 3 candidates)

- **Android**: blocked on `@T-Dynamos` guidance. Open questions:
  output format (.so collection vs `.aar`?), ABI list (`arm64-v8a`,
  `armeabi-v7a`, `x86_64`?), NDK pin, API level. Deliberately not
  speculating until the maintainer weighs in.
- **iOS threading**: see Q4.
- **Framework signing automation**: see Q3.
- **CI cache eviction**: ThorVG version bumps will need to update
  the `tools/build_ios_dependencies.sh` cache key. That's already
  the case (it uses `hashFiles('tools/build_ios_dependencies.sh')`),
  so the version bump in `tools/build_thorvg.sh` may not invalidate
  by itself — consider also hashing `tools/build_thorvg.sh` in the
  cache key on the iOS workflow. Not required for the initial PR
  but worth noting.

---

*Created during STAGE 1 close-out, 2026-04-24.*
