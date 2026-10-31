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

  local packager_sha
  packager_sha=$(git rev-parse HEAD)
  printf 'kivy-sdk-packager revision: %s\n' "$packager_sha"
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    printf 'packager_sha=%s\n' "$packager_sha" >> "$GITHUB_OUTPUT"
  fi

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
  if [ "$#" -ne 2 ] || [ -z "$2" ]; then
    printf '%s\n' 'Expected a packager osx directory and its build revision.' >&2
    exit 1
  fi
  root="$(pwd -P)"
  ci_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
  bootstrap_script="$ci_dir/osx_app_test_dependencies.py"
  packager_osx=$(cd "$1" && pwd -P)
  expected_packager_sha="$2"
  packager_sha=$(git -C "$packager_osx" rev-parse HEAD)
  if [ "$packager_sha" != "$expected_packager_sha" ]; then
    printf 'Packager revision mismatch: expected %s, found %s\n' \
      "$expected_packager_sha" "$packager_sha" >&2
    exit 1
  fi
  printf 'Test preparation packager revision: %s\n' "$packager_sha"
  printf 'App-test runner image: %s %s\n' "${ImageOS:-unknown}" "${ImageVersion:-unknown}"
  printf 'Test Kivy checkout: '
  git -C "$root" rev-parse HEAD

  app="$root/app/Kivy.app"
  app_python="$app/Contents/Resources/venv/bin/python3"
  base_python="$app/Contents/Resources/python3/bin/python3"
  test -x "$app_python"
  test -x "$base_python"
  test -r "$bootstrap_script"
  test -r "$root/pyproject.toml"
  test -r "$packager_osx/prepare-wheels.py"
  test -r "$packager_osx/requirements.txt"
  work=$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/kivy-app-test-deps.XXXXXX")
  tools_python="$work/tools/bin/python"
  printf 'App test dependency preparation: %s\n' "$work"

  # Keep source imports out of app probes; app activation's PYTHONHOME is needed.
  unset PYTHONPATH
  cd "$HOME"
  "$app_python" "$bootstrap_script" snapshot-kivy "$app" "$work/kivy-before.json"
  pyver=$("$app_python" -c 'import platform; print(platform.python_version())')
  "$app_python" "$bootstrap_script" write-requirements \
    "$root/pyproject.toml" "$work/dev.in"

  # Resolve using the bundled Python, but keep preparation tools outside the app.
  env -u PYTHONHOME -u PYTHONPATH "$base_python" -m venv "$work/tools"
  env -u PYTHONHOME -u PYTHONPATH "$tools_python" "$bootstrap_script" \
    verify-tools "$work/tools" "$pyver"
  env -u PYTHONHOME -u PYTHONPATH PIP_CONFIG_FILE=/dev/null \
    "$tools_python" -m pip --isolated install \
    --cache-dir "$work/pip-cache" pip-tools -r "$packager_osx/requirements.txt"

  # Match the packager's Intel-compatible constraint, only for these test inputs.
  printf '%s\n' 'cryptography<49' > "$work/constraints.txt"
  env -u PYTHONHOME -u PYTHONPATH "$tools_python" -m piptools compile \
    "$work/dev.in" --constraint "$work/constraints.txt" \
    --allow-unsafe --strip-extras --no-annotate --no-header \
    --no-emit-index-url --no-emit-trusted-host --no-emit-find-links \
    --output-file "$work/dev.txt"
  cert_file=$(env -u PYTHONHOME -u PYTHONPATH "$tools_python" -c \
    'from pip._vendor import certifi; print(certifi.where())')
  env -u PYTHONHOME -u PYTHONPATH SSL_CERT_FILE="${SSL_CERT_FILE:-$cert_file}" \
    "$tools_python" "$packager_osx/prepare-wheels.py" \
    --requirements-file "$work/dev.txt" --python-version "$pyver" \
    --deployment-target 11.0 --output-folder "$work/wheels"
  env -u PYTHONHOME -u PYTHONPATH "$tools_python" "$bootstrap_script" \
    validate-wheels "$work"

  # Ignore inherited pip settings: use only these wheels and the copied venv.
  PIP_CONFIG_FILE=/dev/null "$app_python" -m pip --isolated install \
    --no-index --no-cache-dir --only-binary=:all: --no-deps \
    --find-links "$work/wheels" -r "$work/dev.txt"
  "$app_python" "$bootstrap_script" record-installed "$app" "$work"
  env -u PYTHONHOME -u PYTHONPATH "$tools_python" "$bootstrap_script" \
    verify-installed "$work"
  PIP_CONFIG_FILE=/dev/null "$app_python" -m pip --isolated check
  "$app_python" "$bootstrap_script" snapshot-kivy "$app" "$work/kivy-after.json"
  cmp "$work/kivy-before.json" "$work/kivy-after.json"
  printf '%s\n' 'Bundled Kivy package and compiled extensions are unchanged.'
  "$app_python" "$bootstrap_script" inspect-native "$app" "$work"
  KIVY_NO_CONSOLELOG=1 KIVY_LOG_MODE=PYTHON \
    "$app_python" "$bootstrap_script" verify-tests "$app"
)
