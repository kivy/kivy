#!/bin/bash
set -e -x

update_version_metadata() {
  current_time=$(python -c "from time import time; from os import environ; print(int(environ.get('SOURCE_DATE_EPOCH', time())))")
  date=$(python -c "from datetime import datetime; print(datetime.utcfromtimestamp($current_time).strftime('%Y%m%d'))")
  echo "Version date is: $date"
  git_tag=$(git rev-parse HEAD)
  echo "Git tag is: $git_tag"

  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/_kivy_git_hash = ''/_kivy_git_hash = '$git_tag'/" kivy/_version.py
    sed -i '' "s/_kivy_build_date = ''/_kivy_build_date = '$date'/" kivy/_version.py
  else
    sed -i "s/_kivy_git_hash = ''/_kivy_git_hash = '$git_tag'/" kivy/_version.py
    sed -i "s/_kivy_build_date = ''/_kivy_build_date = '$date'/" kivy/_version.py
  fi
}

generate_sdist() {
  python3 -m pip install cython packaging
  python3 setup.py sdist --formats=gztar
  python3 -m pip uninstall cython -y
}


install_kivy_test_run_pip_deps() {
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python3 get-pip.py --user

  python3 -m pip install --upgrade pip setuptools wheel
  CYTHON_INSTALL=$(
    KIVY_NO_CONSOLELOG=1 python3 -c \
      "from kivy.tools.packaging.cython_cfg import get_cython_versions; print(get_cython_versions()[0])" \
      --config "kivy:log_level:error"
  )
  python3 -m pip install -I "$CYTHON_INSTALL" coveralls
}

install_kivy_test_wheel_run_pip_deps() {
  python3 -m pip install --upgrade pip setuptools wheel
}

prepare_env_for_unittest() {
  /sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background \
    --exec /usr/bin/Xvfb -- :99 -screen 0 1280x720x24 -ac +extension GLX
}

install_kivy() {
  options=${1:-full,dev}
  python3 -m pip install -e "$(pwd)[$options]"
}


create_kivy_examples_wheel() {
  KIVY_BUILD_EXAMPLES=1 python3 -m pip wheel . -w dist/
}

install_kivy_examples_wheel() {
  options=${1:-full,dev}
  root="$(pwd)"
  cd ~
  python3 -m pip install --pre --no-index --no-deps -f "$root/dist" "kivy_examples"
  python3 -m pip install --pre -f "$root/dist" "kivy_examples[$options]"
}

install_kivy_wheel() {
  options=${1:-full,dev}
  root="$(pwd)"
  cd ~
  version=$(python3 -c "import sys; print('{}{}'.format(sys.version_info.major, sys.version_info.minor))")
  kivy_fname=$(ls "$root"/dist/Kivy-*$version*.whl | awk '{ print length, $0 }' | sort -n -s | cut -d" " -f2- | head -n1)
  python3 -m pip install "${kivy_fname}[$options]"
}

install_kivy_sdist() {
  options=${1:-full,dev}
  root="$(pwd)"
  cd ~

  kivy_fname=$(ls $root/dist/Kivy-*.tar.gz)
  python3 -m pip install "$kivy_fname[$options]"
}

test_kivy() {
  rm -rf kivy/tests/build || true
  # Tests with default environment variables.
  env KIVY_NO_ARGS=1 python3 -m pytest --maxfail=10 --timeout=300 --cov=kivy --cov-branch --cov-report= "$(pwd)/kivy/tests"
  # Logging tests, with non-default log modes
  env KIVY_NO_ARGS=1 KIVY_LOG_MODE=PYTHON python3 -m pytest -m logmodepython --maxfail=10 --timeout=300 --cov=kivy --cov-append --cov-report= --cov-branch "$(pwd)/kivy/tests"
  env KIVY_NO_ARGS=1 KIVY_LOG_MODE=MIXED python3 -m pytest -m logmodemixed --maxfail=10 --timeout=300 --cov=kivy --cov-append --cov-report=term --cov-branch "$(pwd)/kivy/tests"
}

test_kivy_benchmark() {
  env KIVY_NO_ARGS=1 pytest --pyargs kivy.tests --benchmark-only
}

test_kivy_install() {
  cd ~
  python3 -c 'import kivy'
  test_path=$(KIVY_NO_CONSOLELOG=1 python3 -c 'import kivy.tests as tests; print(tests.__path__[0])' --config "kivy:log_level:error")
  cd "$test_path"

  cat >.coveragerc <<'EOF'
[run]
  plugins = kivy.tools.coverage

EOF
  KIVY_TEST_AUDIO=0 KIVY_NO_ARGS=1 python3 -m pytest --maxfail=10 --timeout=300 .
}

upload_coveralls() {
  python3 -m coveralls
}

validate_pep8() {
  python3 -m pip install flake8
  make style
}

generate_docs() {
  make html
}

upload_docs_to_server() {
  branch="docs-$1"
  commit="$2"

  # only upload docs if we have a branch for it
  if [ -z "$(git ls-remote --heads https://github.com/kivy/kivy-website-docs.git "$branch")" ]; then
    return
  fi

  git clone --depth 1 --branch "$branch" https://github.com/kivy/kivy-website-docs.git
  cd kivy-website-docs

  git config user.email "kivy@kivy.org"
  git config user.name "Kivy bot"
  git remote rm origin || true
  git remote add origin "https://x-access-token:${DOC_PUSH_TOKEN}@github.com/kivy/kivy-website-docs.git"

  rsync --delete --force --exclude .git/ --exclude .gitignore -r ../doc/build/html/ .

  git add .
  git add -u
  if ! git diff --cached --exit-code --quiet; then
    git commit -m "Docs for git-$commit"
    git push origin "$branch"
  fi
}

install_manylinux_build_deps() {
  # These are basically copy-pasted from the SDL dependencies
  # (it contains both build tools and libraries development packages)
  # See: https://wiki.libsdl.org/SDL2/README/linux
  yum install -y epel-release;
  yum -y install autoconf automake cmake gcc gcc-c++ git make pkgconfig \
            ninja-build alsa-lib-devel pulseaudio-libs-devel \
            libX11-devel libXext-devel libXrandr-devel libXcursor-devel libXfixes-devel \
            libXi-devel libXScrnSaver-devel dbus-devel ibus-devel fcitx-devel \
            systemd-devel mesa-libGL-devel libxkbcommon-devel mesa-libGLES-devel \
            mesa-libEGL-devel wayland-devel wayland-protocols-devel \
            libdrm-devel mesa-libgbm-devel libsamplerate-devel
}

install_ubuntu_build_deps() {
  # These are basically copy-pasted from the SDL dependencies
  # (it contains both build tools and libraries development packages)
  # See: https://wiki.libsdl.org/SDL2/README/linux
  sudo apt-get update
  sudo apt-get -y install build-essential git make autoconf automake libtool \
          pkg-config cmake ninja-build libasound2-dev libpulse-dev libaudio-dev \
          libjack-dev libsndio-dev libsamplerate0-dev libx11-dev libxext-dev \
          libxrandr-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev libwayland-dev \
          libxkbcommon-dev libdrm-dev libgbm-dev libgl1-mesa-dev libgles2-mesa-dev \
          libegl1-mesa-dev libdbus-1-dev libibus-1.0-dev libudev-dev fcitx-libs-dev
}

generate_rpi_wheels() {
  image=$1

  mkdir dist
  docker build -f .ci/Dockerfile.armv7l -t kivy/kivy-armv7l --build-arg image="$image" .
  docker cp "$(docker create kivy/kivy-armv7l)":/kivy-delocated-wheel .
  cp kivy-delocated-wheel/Kivy-* dist/

  # Create a copy with the armv6l suffix
  for name in dist/*.whl; do
    new_name="${name/armv7l/armv6l}"
    cp -n "$name" "$new_name"
  done
}

rename_wheels() {
  wheel_date=$(python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y%m%d'))")
  echo "wheel_date=$wheel_date"
  git_tag=$(git rev-parse --short HEAD)
  echo "git_tag=$git_tag"
  tag_name=$(KIVY_NO_CONSOLELOG=1 python3 \
    -c "import kivy; _, tag, n = kivy.parse_kivy_version(kivy.__version__); print(tag + n) if n is not None else print(tag or 'something')" \
    --config "kivy:log_level:error")
  echo "tag_name=$tag_name"
  wheel_name="$tag_name.$wheel_date.$git_tag-"
  echo "wheel_name=$wheel_name"

  ls dist/
  for name in dist/*.whl; do
    new_name="${name/$tag_name-/$wheel_name}"
    if [ ! -f "$new_name" ]; then
      cp -n "$name" "$new_name"
    fi
  done
  ls dist/
}

upload_file_to_server() {
  ip="$1"
  server_path="$2"
  file_pat=${3:-*.whl}
  file_path=${4:-dist}

  if [ ! -d ~/.ssh ]; then
    mkdir ~/.ssh
  fi

  printf "%s" "$UBUNTU_UPLOAD_KEY" >~/.ssh/id_ed25519
  chmod 600 ~/.ssh/id_ed25519

  echo -e "Host $ip\n\tStrictHostKeyChecking no\n" >>~/.ssh/config
  rsync -avh -e "ssh -p 2458" --include="*/" --include="$file_pat" --exclude="*" "$file_path/" "root@$ip:/web/downloads/ci/$server_path"
}

upload_artifacts_to_pypi() {
  python3 -m pip install twine
  twine upload dist/*
}
