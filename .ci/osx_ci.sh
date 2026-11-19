#!/bin/bash
set -e -x

# macOS Platypus version
MACOS__PLATYPUS__VERSION=5.4.1

download_cache_curl() {
  fname="$1"
  key="$2"
  url="$3"

  if [ ! -f $key/$fname ]; then
    if [ ! -d $key ]; then
      mkdir "$key"
    fi
    curl -L "$url" -o "$fname"
    cp "$fname" "$key"
  else
    cp "$key/$fname" .
  fi
}

install_platypus() {
  download_cache_curl "platypus$MACOS__PLATYPUS__VERSION.zip" "osx-cache" "https://github.com/sveinbjornt/Platypus/releases/download/v$MACOS__PLATYPUS__VERSION/platypus$MACOS__PLATYPUS__VERSION.zip"

  unzip "platypus$MACOS__PLATYPUS__VERSION.zip"
  gunzip Platypus.app/Contents/Resources/platypus_clt.gz
  gunzip Platypus.app/Contents/Resources/ScriptExec.gz

  mkdir -p /usr/local/bin
  sudo mkdir -p /usr/local/share/platypus
  cp Platypus.app/Contents/Resources/platypus_clt /usr/local/bin/platypus
  sudo cp Platypus.app/Contents/Resources/ScriptExec /usr/local/share/platypus/ScriptExec
  sudo cp -a Platypus.app/Contents/Resources/MainMenu.nib /usr/local/share/platypus/MainMenu.nib
  sudo chmod -R 755 /usr/local/share/platypus
}

generate_osx_app_bundle() {
  app_ver=$(PYTHONPATH=. KIVY_NO_CONSOLELOG=1 python3 -c 'import kivy; print(kivy.__version__)')

  cd ../
  git clone https://github.com/kivy/kivy-sdk-packager.git
  cd kivy-sdk-packager/osx

  ./create-osx-bundle.sh -k ../../kivy -v "$app_ver"
}

generate_osx_app_dmg_from_bundle() {
  pushd ../kivy-sdk-packager/osx
  ./create-osx-dmg.sh build/Kivy.app Kivy
  popd

  mkdir app

  mv ../kivy-sdk-packager/osx/Kivy.dmg "app/Kivy.dmg"
}

rename_osx_app() {
  py_version=${1:0:3}

  app_date=$(python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y%m%d'))")
  git_tag=$(git rev-parse --short HEAD)
  app_ver=$(PYTHONPATH=. KIVY_NO_CONSOLELOG=1 python3 -c 'import kivy; print(kivy.__version__)')

  cp app/Kivy.dmg "app/Kivy-$app_ver-$git_tag-$app_date-python$py_version.dmg"
}

mount_osx_app() {
  pushd app
  hdiutil attach Kivy.dmg -mountroot .
  cp -R Kivy/Kivy.app Kivy.app
  popd
}

activate_osx_app_venv() {
  pushd app/Kivy.app/Contents/Resources/venv/bin
  source activate
  source kivy_activate
  popd
}

install_osx_app_test_dependencies() (
  root="$(pwd -P)"
  app="$root/app/Kivy.app"
  app_python="$app/Contents/Resources/venv/bin/python3"
  requirements=$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/kivy-app-test-deps.XXXXXX")
  trap 'rm -f "$requirements"' EXIT

  # Keep source imports out of app probes; app activation's PYTHONHOME is needed.
  unset PYTHONPATH
  cd "$HOME"

  app_identity() {
    "$app_python" - "$app" <<'PY'
from importlib import metadata, util
from pathlib import Path
import sys
import sysconfig

venv = (Path(sys.argv[1]) / "Contents/Resources/venv").resolve()
if (Path(sys.prefix).resolve() != venv
        or not Path(sysconfig.get_path("purelib")).resolve().is_relative_to(venv)):
    sys.exit("App Python must install into the copied venv")
spec = util.find_spec("kivy")
if spec is None or spec.origin is None:
    sys.exit("Kivy is missing from the copied app")
origin = Path(spec.origin).resolve()
if not origin.is_relative_to(venv):
    sys.exit(f"Kivy imports from outside the copied venv: {origin}")
print(origin, metadata.version("Kivy"))
PY
  }

  before=$(app_identity)
  printf 'App Python: %s\nBundled Kivy: %s\n' "$app_python" "$before"
  "$app_python" - "$root/pyproject.toml" > "$requirements" <<'PY'
import sys
import tomllib

with open(sys.argv[1], "rb") as stream:
    print("\n".join(tomllib.load(stream)["project"]["optional-dependencies"]["dev"]))
PY

  # These wheels only serve the current runner's disposable test app.
  PIP_CONFIG_FILE=/dev/null "$app_python" -m pip --isolated install \
    --only-binary=:all: -r "$requirements"
  after=$(app_identity)
  if [ "$before" != "$after" ]; then
    printf 'Bundled Kivy changed: %s -> %s\n' "$before" "$after" >&2
    exit 1
  fi
  PIP_CONFIG_FILE=/dev/null "$app_python" -m pip --isolated check
  PIP_CONFIG_FILE=/dev/null "$app_python" -m pip --isolated list --format=freeze
)
