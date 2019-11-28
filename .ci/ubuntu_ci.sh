#!/bin/bash
set -e -x

install_kivy_test_run_apt_deps() {
  sudo apt-get update
  sudo apt-get -y install libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev libsdl2-mixer-dev
  sudo apt-get -y install libgstreamer1.0-dev gstreamer1.0-alsa gstreamer1.0-plugins-base
  sudo apt-get -y install libsmpeg-dev libswscale-dev libavformat-dev libavcodec-dev libjpeg-dev libtiff5-dev libx11-dev libmtdev-dev
  sudo apt-get -y install build-essential libgl1-mesa-dev libgles2-mesa-dev
  sudo apt-get -y install xvfb pulseaudio xsel
}

install_python() {
  sudo apt-get -y install python3 python3-dev python3-setuptools
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

prepare_env_for_unittest() {
  /sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background \
  --exec /usr/bin/Xvfb -- :99 -screen 0 1280x720x24 -ac +extension GLX
}

install_kivy() {
  path="$(pwd)"
  ln -s "$path" ~/base_kivy
  cd ~/base_kivy
  python3 -m pip install -e "$(pwd)[dev,full,full_src]"
  cd "$path"
}

test_kivy() {
  rm -rf kivy/tests/build || true
  KIVY_NO_ARGS=1 python3 -m pytest --cov=kivy --cov-report term --cov-branch "$(pwd)/kivy/tests"
}

upload_coveralls() {
  python3 -m coveralls
}

validate_pep8() {
  make style
}

generate_docs() {
  make html
}

upload_docs_to_server() {
  versions=$1
  branch=$2
  ip=$3

  if [ ! -d ~/.ssh ]; then
    mkdir ~/.ssh
  fi
  printf "%s" "$UBUNTU_UPLOAD_KEY" > ~/.ssh/id_rsa
  chmod 600 ~/.ssh/id_rsa
  echo -e "Host $ip\n\tStrictHostKeyChecking no\n" >>~/.ssh/config

  for version in $versions; do
    if [ "$version" == "${branch}" ]; then
      echo "[$(echo $versions | tr ' ' ', ' | sed -s 's/\([^,]\+\)/"\1"/g')]" > versions.json
      rsync --force -e "ssh -p 2457" versions.json root@$ip:/web/doc/
      rsync --delete --force -r -e "ssh -p 2457" ./doc/build/html/ root@$ip:/web/doc/$version
    fi
  done
}

generate_manylinux2010_wheels() {
  image=$1

  mkdir dist
  chmod +x .ci/build-wheels-linux.sh
  docker run --rm -v "$(pwd):/io" "$image" "/io/.ci/build-wheels-linux.sh"
  sudo rm dist/*-linux*
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

  printf "%s" "$UBUNTU_UPLOAD_KEY" > ~/.ssh/id_rsa
  chmod 600 ~/.ssh/id_rsa

  echo -e "Host $ip\n\tStrictHostKeyChecking no\n" >>~/.ssh/config
  rsync -avh -e "ssh -p 2458" --include="*/" --include="$file_pat" --exclude="*" "$file_path/" "root@$ip:/web/downloads/ci/$server_path"
}
