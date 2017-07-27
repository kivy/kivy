#!/usr/bin/env sh

# ImageMagickFormat:extension
FMT_OPAQUE="TIFF:tiff BMP:bmp BMP3:bmp PNG:png GIF87:gif CUR:cur"
FMT_BINARY="BMP:bmp GIF:gif PNG8:png PNG24:png PNG48:png ICO:ico"
FMT_ALPHA="PNG32:png PNG64:png TGA:tga SGI:sgi DPX:dpx"

usage() { cat <<EOM
Usage: $0 <target-directory>

Creates test images in many formats using ImageMagick 'convert'
utility. The pixel values are encoded in the filename, so they
can be reconstructed and verified.

v0_<W>x<H>_<pattern>_<alpha>_<format>_<info>.<extension>

  Example: "v0_3x1_rgb_FF_PNG24_OPAQUE.png" is a 3x1 image with
  red, green and blue pixels. Alpha is FF, the ImageMagick
  format is PNG24. <info> is used to distinguish tests that
  use the same pattern but differ in other parameters
  (currently _OPAQUE, _BINARY and _ALPHA)

  The leading 'v0_' indicates version 0 of the test protocol,
  which is defined by this implementation. All v0 images are
  either a single row or single column of pixels with values:

Pattern legend:

  w: White  (#fff)    x: Black (#000)** t: Transp (#0000)**
  r: Red    (#f00)    g: Green (#0f0)   b: Blue   (#00f)
  y: Yellow (#ff0)    c: Cyan  (#0ff)   p: Purple (#f0f)

  ** 't' and 'x' cannot be combined in the same pattern for
     testing binary transparency (all black pixels become
     transparent for some formats, causing tests to fail).

EOM
}

# Outputs command line arguments for convert to draw pixels from the
# specifed pattern in the specified direction. It is always 1 in w or h.
draw_pattern() {
    pattern=$1
    direction="${2:-x}"
    alpha=${3:-FF}
    pos=0
    for char in $(echo $pattern | fold -w1); do
        case $char in
            t) fill="#00000000" ;;
            w) fill="#FFFFFF${alpha}" ;;
            x) fill="#000000${alpha}" ;;
            r) fill="#FF0000${alpha}" ;;
            g) fill="#00FF00${alpha}" ;;
            b) fill="#0000FF${alpha}" ;;
            y) fill="#FFFF00${alpha}" ;;
            c) fill="#00FFFF${alpha}" ;;
            p) fill="#FF00FF${alpha}" ;;
            *) (>&2 echo "Error: Invalid pattern char: $char"); exit 100 ;;
        esac
        case $direction in
            y|height) echo -n "-draw 'fill $fill color 0, $pos point' " ;;
            x|width)  echo -n "-draw 'fill $fill color $pos, 0 point' " ;;
        esac
        pos=$((pos+1))
    done
}

# Creates 1xN and Nx1 test images from the given pattern, in the given
# format. Only use alpha != FF if you are actually testing alpha.
make_images() {
    pattern=$1
    format=$2
    ext=$3
    alpha=${4:-FF}
    name=$5
    len=${#pattern}

    if [ -z $pattern ] || [ -z $format ] || [ -z $ext ]; then
        (>&2 echo "make_images() missing required arguments")
        exit 101
    fi
    if [ ${#alpha} != 2 ]; then
        (>&2 echo "make_images() invalid alpha: $alpha")
        exit 102
    fi

    # Nx1
    outfile="v0_${len}x1_${pattern}_${alpha}_${format}${name}.${ext}"
    eval convert -size ${len}x1 xc:none -quality 100% -alpha on \
        $(draw_pattern "$pattern" "x" "$alpha") \
        "${format}:$destdir/$outfile"

    # 1xN - don't create duplicates for single pixel
    if [ $len -ne 1 ]; then
        outfile="v0_1x${len}_${pattern}_${alpha}_${format}${name}.${ext}"
        eval convert -size 1x${len} xc:none -quality 100% -alpha on \
            $(draw_pattern "$pattern" "y" "$alpha") \
            "${format}:$destdir/$outfile"
    fi
}

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if [ "$#" -ne 1 ] || [ -z "$1" ]; then
    echo "Usage: $0 <target-directory>  (or -h for help)"
    exit 1
fi

case $1 in
    -h|--help) usage; exit 1 ;;
esac

if [ ! -d "$1" ]; then
    (>&2 echo "Error: Destination directory '$1' does not exist")
    exit 2
elif [ ! -w "$1" ]; then
    (>&2 echo "Error: Destination directory '$1' not writeable")
    exit 2
fi
destdir=$(cd "$1"; echo $(pwd))

if [ ! -x "$(command -v convert)" ]; then
    (2>&1 echo "Required ImageMagick 'convert' not found in path")
    exit 3
fi

# Make a random pattern from given characters $1 at length $2
# FIXME: portability?
mkpattern() {
    < /dev/urandom LC_ALL=C tr -dc "$1" | head -c $2
}

# Opaque patterns only include solid colors, alpha is fixed at FF
PAT_opaque="w x r g b y c p wx cy cp xyx rgb rgbw rgbwx cyp cypw cypwx"
for i in $(seq 2 9) $(seq 14 17) $(seq 31 33); do
    new=$(mkpattern "wxrgbcyp" "$i")
    PAT_opaque="${PAT_opaque} ${new}"
done
for rawfmt in $FMT_OPAQUE $FMT_BINARY $FMT_ALPHA; do
    fmt=${rawfmt%:*}
    ext=${rawfmt#*:}
    echo "[OPAQUE] Creating ${fmt} test images ..."
    for pat in $PAT_opaque; do
        make_images "$pat" "$fmt" "$ext" "FF" "_OPAQUE"
    done
done

# Binary patterns MUST include 't' pixels and MUST NOT include 'x'
PAT_binary="t tw tr tg tb tc ty tp tt twrt trgb trgbt tcypt rtg rttg rtttg"
for i in $(seq 2 9) $(seq 14 17) $(seq 31 33); do
    new=$(mkpattern "twrgbcyp" "$i")
    PAT_binary="${PAT_binary} t${new}"
done
for rawfmt in $FMT_BINARY $FMT_ALPHA; do
    fmt=${rawfmt%:*}
    ext=${rawfmt#*:}
    echo "[BINARY] Creating ${fmt} test images ..."
    for pat in $PAT_binary; do
        make_images "$pat" "$fmt" "$ext" "FF" "_BINARY"
    done
done

# Reuse binary/opaque for alpha patterns. These are generated with the
# same pixel values, but differeent (per-pixel) alpha. Also test
# white, black and fully-transparent pixels in one pattern.
PAT_alpha="${PAT_opaque} ${PAT_binary} twx wtx xwt xxttww"
for rawfmt in $FMT_ALPHA; do
    fmt=${rawfmt%:*}
    ext=${rawfmt#*:}
    echo "[ALPHA] Creating ${fmt} test images ..."
    for alpha in 7F F0; do
        for pat in $PAT_alpha; do
            make_images "$pat" "$fmt" "$ext" "$alpha" "_ALPHA"
        done
    done
done

