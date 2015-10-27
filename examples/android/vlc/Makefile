NDK_PATH=$(HOME)/android-ndk-r10c
ADK_PATH=$(HOME)/android-sdk-linux_r23.0.2
API=17
PKG=org.test.NativeVlcPlayer
LIBVLC_AAR=$(HOME)/libvlc-3.0.0.aar

apk: dist
	export ANDROIDAPI=$(API) && \
	export ANDROIDNDK=$(NDK_PATH) && \
	export ANDROIDSDK=$(ADK_PATH) && \
	p4a apk \
			--dir=$(abspath .) \
			--dist_name=kivy-vlc-android \
			--sdk_dir=$(ADK_PATH) \
			--ndk_dir=$(NDK_PATH) \
			--android_api=$(API) \
			--package $(PKG) \
			--version 1.0 \
			--name "Native Vlc Player" \
			--orientation sensor \
			--meta-data surface.transparent=1 \
			--meta-data surface.depth=16 \
			--meta-data android.background_color=0
dist:
	export LIBVLC_AAR=$(LIBVLC_AAR) && \
	export ANDROIDAPI=$(API) && \
	export ANDROIDNDK=$(NDK_PATH) && \
	export ANDROIDSDK=$(ADK_PATH) && \
	p4a create \
			--dist_name=kivy-vlc-android \
			--bootstrap=pygame \
			--requirements=kivy,vlc,android \
			--sdk_dir=$(ADK_PATH) \
			--ndk_dir=$(NDK_PATH) \
			--android_api=$(API)
.PHONY: dist_vlc

#kivy 1.9 fix - downgrade cython to 0.20
CYTHONVER=0.20
GETTEXTVER=0.19.5.1
install_ubuntu_requirements:
	sudo apt-get update
	sudo apt-get -y install \
			build-essential ccache git make gcc python python-dev python-pip ant
			pkg-config autoconf automake libtool \
			unzip p7zip-full zlib1g-dev \
			openjdk-7-jdk android-tools-adb android-tools-fastboot \
			autoconf automake autopoint cmake gawk gcc g++ yasm libtool m4 patch \
			pkg-config ragel subversion unzip ant acl \
			protobuf-compiler libprotobuf-dev libprotobuf-c0-dev protobuf-c-compiler
	if ! cython -V 2>&1|grep 'Cython version $(CYTHONVER)'; then \
		echo y | sudo pip uninstall cython ; \
		sudo pip install cython==$(CYTHONVER) ; \
	fi
	sudo pip install markupsafe
	sudo pip install virtualenv
	if ! gettext -V | grep $(GETTEXTVER); then \
		wget http://ftp.gnu.org/pub/gnu/gettext/gettext-$(GETTEXTVER).tar.gz -O - | tar xz && \
		cd gettext-$(GETTEXTVER)/ && ./configure --prefix=/usr/local && make && sudo make install && cd .. && \
		rm -Rf gettext-$(GETTEXTVER) && \
		echo "package gettext updated. REBOOT REQUIRED. pls start make again after reboot" && \
		sudo reboot \
	fi
.PHONY: install_ubuntu_requirements

ACTIVITY=org.renpy.android.PythonActivity
test:
	adb install -r NativeVlcPlayer-0.1-debug.pygame.apk
	adb logcat -c
	adb shell am start -n $(PKG)/$(ACTIVITY) -a $(ACTIVITY)
	adb logcat | findstr /B "./python ./VLC"
ACTIVITY_SDL2=org.kivy.android.PythonActivity
test_sdl2:
	adb install -r NativeVlcPlayer-0.1-debug.sdl2.apk
	adb logcat -c
	adb shell am start -n $(PKG)/$(ACTIVITY_SDL2) -a $(ACTIVITY_SDL2)
	adb logcat | findstr /B "./python ./Python ./VLC ./SDL"
