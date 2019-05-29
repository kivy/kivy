#!/usr/bin/env sh

# ImageMagickFormat:extension
FMT_OPAQUE="TIFF:tiff BMP:bmp BMP3:bmp PNG:png GIF87:gif CUR:cur \
            PPM:ppm FITS:fits RAS:ras"
FMT_BINARY="BMP:bmp GIF:gif PNG8:png PNG24:png PNG48:png ICO:ico"
FMT_ALPHA="PNG32:png PNG64:png TGA:tga SGI:sgi DPX:dpx"

# FIXME: Magick output is not completely predictable. Some images
# become gray+alpha, some palette, some bitonal, and it's not obvious
# how/if this can be controlled better
#FMT_BITONAL=""
FMT_GRAY_OPAQUE="PGM:pgm FITS:fits RAS:ras"
FMT_GRAY_BINARY="PNG8:png"
FMT_GRAY_ALPHA="PNG:png TGA:tga"

# Pixel values used for different tests
PIX_alpha="twxrgbcyp48A"
PIX_opaque="wxrgbcyp48A"
PIX_binary="twrgbcyp48A"
PIX_gray_opaque="0123456789ABCDEF"
PIX_gray_binary="t123456789ABCDEF"
PIX_gray_alpha="t0123456789ABCDEF"


usage() { cat <<EOM
Usage: $0 <target-directory>

  Creates test images in many formats using ImageMagick 'convert'
  utility. The pixel values are encoded in the filename, so they
  can be reconstructed and verified independently. This system
  is referred to as the image test protocol (version 0). 

  More info: kivy/tools/image-testsuite/README.md
EOM
}

# Outputs command line arguments for convert to draw pixels from the
# specifed pattern in the specified direction. It is always 1 in w or h.
draw_pattern() {
    pattern=$1
    direction="${2:-x}"
    pos=0
    for char in $(echo $pattern | fold -w1); do
        case $char in
            t) fill="#00000000" ;;
            w) fill="#FFFFFF${TESTALPHA}" ;;
            x) fill="#000000${TESTALPHA}" ;;
            r) fill="#FF0000${TESTALPHA}" ;;
            g) fill="#00FF00${TESTALPHA}" ;;
            b) fill="#0000FF${TESTALPHA}" ;;
            y) fill="#FFFF00${TESTALPHA}" ;;
            c) fill="#00FFFF${TESTALPHA}" ;;
            p) fill="#FF00FF${TESTALPHA}" ;;
            0|1|2|3|4|5|6|7|8|9|A|B|C|D|E|F)
                fill="#${char}${char}${char}${char}${char}${char}${TESTALPHA}"
            ;;
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
    len=${#pattern}

    if [ -z $pattern ] || [ -z $TESTFMT ] || [ -z $TESTEXT ]; then
        (>&2 echo "make_images() missing required arguments/environment")
        exit 101
    fi
    if [ ${#TESTALPHA} != 2 ]; then
        (>&2 echo "make_images() invalid TESTALPHA: $TESTALPHA")
        exit 102
    fi

    # Nx1
    ending="${TESTALPHA}_${TESTFMT}_${TESTNAME}_magick.${TESTEXT}"
    outfile="v0_${len}x1_${pattern}_${ending}"
    eval convert -size ${len}x1 xc:none -quality 100% $TESTARGS \
        $(draw_pattern "$pattern" "x") \
        ${convert_args} \
        "${TESTFMT}:$destdir/$outfile"

    # 1xN - don't create duplicates for single pixel
    if [ $len -ne 1 ]; then
        outfile="v0_1x${len}_${pattern}_${ending}"
        eval convert -size 1x${len} xc:none -quality 100% $TESTARGS \
            $(draw_pattern "$pattern" "y") \
            "${TESTFMT}:$destdir/$outfile"
    fi
}

# Make a random pattern from given characters $1 at length $2
# FIXME: portability?
mkpattern() {
    < /dev/urandom LC_ALL=C tr -dc "$1" | head -c $2
}

# Makes simple permutations and random patterns, optionally with
# prefix and postfix (args are pattern, prefix, postfix)
permutepattern() {
    if [ -z "$1" ]; then
        (>&2 echo "permutepattern() missing required argument")
        exit 200
    fi

    # Individual pixel values + poor permutation FIXME
    for char in $(echo $1 | fold -w1); do
        echo -n "$2${char}$3 "
        if [ ! -z $p1 ]; then echo -n "$2${char}${p1}$3 "; fi
# Uncomment for more data
#        if [ ! -z $p2 ]; then echo -n "$2${char}${p1}${p2}$3 "; fi
#        if [ ! -z $p3 ]; then echo -n "$2${char}${p1}${p2}${p3}$3 "; fi
#        if [ ! -z $p4 ]; then echo -n "$2${char}${p1}${p2}${p3}${p4}$3 "; fi
        p4=$p3 ; p3=$p2 ; p2=$p1 ; p1=$char
    done

    # Random
    for i in $(seq 3 9) $(seq 14 17) $(seq 31 33); do
        echo -n "$2$(mkpattern "$1" "$i")$3 "
    done
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


# - Opaque patterns only include solid colors, alpha is fixed at FF
# - Binary patterns MUST include 't' pixels and MUST NOT include 'x' or '0'
# - Alpha can combine any pixel value and use alpha != FF
PAT_opaque=$(permutepattern "$PIX_opaque")
PAT_binary=$(permutepattern "$PIX_binary" "t")
PAT_alpha="${PAT_binary} $(permutepattern "$PIX_alpha")"

# Grayscale patterns use only grayscale pixel values + 't' and alpha,
# ie #000 #111 #222 .. #EEE #FFF (0 1 2 .. E F in patterns)
PAT_gray_opaque=$(permutepattern "$PIX_gray_opaque")
PAT_gray_binary=$(permutepattern "$PIX_gray_binary" "t")
PAT_gray_alpha="${PAT_gray_binary} $(permutepattern "$PIX_gray_alpha")"

start() {
    TESTNAME="$1"
    TESTARGS="$2"
    TESTALPHA="FF"
    TESTFMT=""
    TESTEXT=""
}

inform() {
    echo "[${TESTNAME}] Creating ${TESTFMT} (.${TESTEXT}) test images..."
}

# OPAQUE / GRAY_OPAQUE
start "OPAQUE" "-alpha off"
for rawfmt in $FMT_OPAQUE $FMT_BINARY $FMT_ALPHA; do
    TESTFMT=${rawfmt%:*}; TESTEXT=${rawfmt#*:}; inform
    for pat in $PAT_opaque; do
        make_images "$pat"
    done
done

start "GRAY-OPAQUE" "-alpha off -colorspace Gray"
for rawfmt in $FMT_GRAY_OPAQUE $FMT_GRAY_BINARY $FMT_GRAY_ALPHA; do
    TESTFMT=${rawfmt%:*}; TESTEXT=${rawfmt#*:}; inform
    for pat in $PAT_gray_opaque; do
        make_images "$pat"
    done
done

# BINARY / GRAY_BINARY
start "BINARY" "-alpha on"
for rawfmt in $FMT_BINARY $FMT_ALPHA; do
    TESTFMT=${rawfmt%:*}; TESTEXT=${rawfmt#*:}; inform
    for pat in $PAT_binary; do
        make_images "$pat"
    done
done

start "GRAY-BINARY" "-alpha on -colorspace Gray"
for rawfmt in $FMT_GRAY_BINARY $FMT_GRAY_ALPHA; do
    TESTFMT=${rawfmt%:*}; TESTEXT=${rawfmt#*:}; inform
    for pat in $PAT_gray_binary; do
        make_images "$pat"
    done
done

# ALPHA / GRAY_ALPHA
start "ALPHA" "-alpha on"
for rawfmt in $FMT_ALPHA; do
    TESTFMT=${rawfmt%:*}; TESTEXT=${rawfmt#*:}; inform
    for alpha in 7F F0; do
        TESTALPHA=$alpha
        for pat in $PAT_alpha; do
            make_images "$pat"
        done
    done
done

start "GRAY-ALPHA" "-alpha on -colorspace Gray"
for rawfmt in $FMT_GRAY_ALPHA; do
    TESTFMT=${rawfmt%:*}; TESTEXT=${rawfmt#*:}; inform
    for alpha in 7F F0; do
        TESTALPHA=$alpha
        for pat in $PAT_gray_alpha; do
            make_images "$pat"
        done
    done
done
