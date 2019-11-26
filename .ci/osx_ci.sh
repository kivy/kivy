#!/bin/bash
set -e -x

download_cache_curl() {
  fname="$1"
  key="$2"
  url_prefix="$3"

  if [ ! -f $key/$fname ]; then
    if [ ! -d $key ]; then
      mkdir "$key"
    fi
    curl -O -L "$url_prefix/$fname"
    cp "$fname" "$key"
  else
    cp "$key/$fname" .
  fi
}

download_cache_aria2() {
  fname="$1"
  key="$2"
  url_prefix="$3"

  if [ ! -f $key/$fname ]; then
    if [ ! -d $key ]; then
      mkdir "$key"
    fi
    /usr/local/aria2/bin/aria2c -x 10 "$url_prefix/$fname"
    cp "$fname" "$key"
  else
    cp "$key/$fname" .
  fi
}

install_kivy_test_run_sys_deps() {
  download_cache_curl "aria2-$ARIAL2-osx-darwin.dmg" "osx-cache" "https://github.com/aria2/aria2/releases/download/release-$ARIAL2"
  hdiutil attach aria2-$ARIAL2-osx-darwin.dmg
  sudo installer -package "/Volumes/aria2 $ARIAL2 Intel/aria2.pkg" -target /

  download_cache_curl "SDL2-$SDL2.dmg" "osx-cache" "https://www.libsdl.org/release"
  download_cache_curl "SDL2_image-$SDL2_IMAGE.dmg" "osx-cache" "https://www.libsdl.org/projects/SDL_image/release"
  download_cache_curl "SDL2_mixer-$SDL2_MIXER.dmg" "osx-cache" "https://www.libsdl.org/projects/SDL_mixer/release"
  download_cache_curl "SDL2_ttf-$SDL2_TTF.dmg" "osx-cache" "https://www.libsdl.org/projects/SDL_ttf/release"

  hdiutil attach SDL2-$SDL2.dmg
  sudo cp -a /Volumes/SDL2/SDL2.framework /Library/Frameworks/
  hdiutil attach SDL2_image-$SDL2_IMAGE.dmg
  sudo cp -a /Volumes/SDL2_image/SDL2_image.framework /Library/Frameworks/
  hdiutil attach SDL2_ttf-$SDL2_TTF.dmg
  sudo cp -a /Volumes/SDL2_ttf/SDL2_ttf.framework /Library/Frameworks/
  hdiutil attach SDL2_mixer-$SDL2_MIXER.dmg
  sudo cp -a /Volumes/SDL2_mixer/SDL2_mixer.framework /Library/Frameworks/

  download_cache_aria2 "gstreamer-1.0-$GSTREAMER-x86_64.pkg" "osx-cache" "https://gstreamer.freedesktop.org/data/pkg/osx/$GSTREAMER"
  download_cache_aria2 "gstreamer-1.0-devel-$GSTREAMER-x86_64.pkg" "osx-cache-gst-devel" "https://gstreamer.freedesktop.org/data/pkg/osx/$GSTREAMER"

  sudo installer -package gstreamer-1.0-$GSTREAMER-x86_64.pkg -target /
  sudo installer -package gstreamer-1.0-devel-$GSTREAMER-x86_64.pkg -target /
}

install_platypus() {
  download_cache_curl "platypus$PLATYPUS.zip" "osx-cache" "http://www.sveinbjorn.org/files/software/platypus"

  unzip platypus$PLATYPUS.zip
  gunzip Platypus.app/Contents/Resources/platypus_clt.gz
  gunzip Platypus.app/Contents/Resources/ScriptExec.gz

  mkdir -p /usr/local/bin
  mkdir -p /usr/local/share/platypus
  cp Platypus.app/Contents/Resources/platypus_clt /usr/local/bin/platypus
  cp Platypus.app/Contents/Resources/ScriptExec /usr/local/share/platypus/ScriptExec
  cp -a Platypus.app/Contents/Resources/MainMenu.nib /usr/local/share/platypus/MainMenu.nib
  chmod -R 755 /usr/local/share/platypus
}

generate_osx_wheels() {
  python3 -m pip install git+http://github.com/tito/osxrelocator
  python3 -m pip install --upgrade delocate
  python3 setup.py bdist_wheel

  delocate-wheel dist/*.whl
  zip_dir="$(basename dist/*.whl .whl)"
  unzip dist/*.whl -d dist/$zip_dir
  rm dist/$zip_dir/kivy/.dylibs/libg*
  rm dist/$zip_dir/kivy/.dylibs/GStreamer

  cp /Library/Frameworks/SDL2_mixer.framework/Versions/A/Frameworks/FLAC.framework/Versions/A/FLAC dist/$zip_dir/kivy/.dylibs/
  cp /Library/Frameworks/SDL2_ttf.framework/Versions/A/Frameworks/FreeType.framework/Versions/A/FreeType dist/$zip_dir/kivy/.dylibs/
  cp /Library/Frameworks/SDL2_mixer.framework/Versions/A/Frameworks/Ogg.framework/Versions/A/Ogg dist/$zip_dir/kivy/.dylibs/
  cp /Library/Frameworks/SDL2_mixer.framework/Versions/A/Frameworks/Vorbis.framework/Versions/A/Vorbis dist/$zip_dir/kivy/.dylibs/
  cp /Library/Frameworks/SDL2_mixer.framework/Versions/A/Frameworks/modplug.framework/Versions/A/modplug dist/$zip_dir/kivy/.dylibs/
  cp /Library/Frameworks/SDL2_mixer.framework/Versions/A/Frameworks/mpg123.framework/Versions/A/mpg123 dist/$zip_dir/kivy/.dylibs/

  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/SDL2.framework/Versions/A/SDL2 @loader_path/SDL2
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/FLAC.framework/Versions/A/FLAC @loader_path/FLAC
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/modplug.framework/Versions/A/modplug @loader_path/modplug
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/mpg123.framework/Versions/A/mpg123 @loader_path/mpg123
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/FreeType.framework/Versions/A/FreeType @loader_path/FreeType
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/webp.framework/Versions/A/webp @loader_path/webp
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/Vorbis.framework/Versions/A/Vorbis @loader_path/Vorbis
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/../../../../SDL2.framework/Versions/A/SDL2 @loader_path/SDL2
  python3 -m osxrelocator.__init__ dist/$zip_dir/kivy/.dylibs @rpath/Ogg.framework/Versions/A/Ogg @loader_path/Ogg

  rm dist/$zip_dir.whl
  pushd dist
  python3 -c "from delocate import delocating; delocating.dir2zip('$zip_dir', '$zip_dir.whl')"
  rm -rf $zip_dir
  popd

  delocate-addplat --rm-orig -x 10_9 -x 10_10 dist/*.whl
}

generate_osx_app() {
  py_version="$1"
  branch_name="$2"
  git clone https://github.com/kivy/kivy-sdk-packager
  pushd kivy-sdk-packager/osx
  app_date=$(python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y%m%d'))")
  git_tag=$(git rev-parse --short HEAD)

  ./create-osx-bundle.sh "$branch_name" "$py_version"
  app_ver=$(KIVY_NO_CONSOLELOG=1 Kivy.app/Contents/Resources/script -c 'import kivy; print(kivy.__version__)')
  mv Kivy.app Kivy3.app
  ./create-osx-dmg.sh Kivy3.app
  mkdir app
  cp Kivy3.dmg "app/Kivy-$app_ver-python$py_version.dmg"
  mv Kivy3.dmg "app/Kivy-$app_ver-$git_tag-$app_date-python$py_version.dmg"
  popd
}
