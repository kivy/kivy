ARG image=balenalib/armv7hf-debian:buster
FROM $image

COPY . /kivy
WORKDIR /kivy

RUN [ "cross-build-start" ]

# Install dependencies.
RUN /bin/bash -c 'source .ci/ubuntu_ci.sh && \
    export PIP_EXTRA_INDEX_URL="https://www.piwheels.org/simple" && \
    install_kivy_test_run_apt_deps && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install xorg && \
    install_python && \
    install_kivy_test_run_pip_deps'

# Download the Raspberry Pi firmware, so Raspberry Pi 1-3 can use the 'egl_rpi' window provider.
ARG KIVY_CROSS_PLATFORM=""
ARG KIVY_CROSS_SYSROOT=""
RUN if [ "$KIVY_CROSS_PLATFORM" = "rpi" ]; then \
        apt-get -y install git; \
        git clone --depth=1 https://github.com/raspberrypi/firmware "$KIVY_CROSS_SYSROOT"; \
        ln -s "$KIVY_CROSS_SYSROOT"/opt/vc "$KIVY_CROSS_SYSROOT"/usr; \
    fi

# Build the wheel.
RUN KIVY_SPLIT_EXAMPLES=1 USE_X11=1 USE_SDL2=1 USE_PANGOFT2=0 USE_GSTREAMER=0 KIVY_SDL_GL_ALPHA_SIZE=0 KIVY_CROSS_PLATFORM="$KIVY_CROSS_PLATFORM" KIVY_CROSS_SYSROOT="$KIVY_CROSS_SYSROOT" python3 -m pip -v wheel --extra-index-url https://www.piwheels.org/simple . -w /kivy-wheel

RUN [ "cross-build-end" ]
