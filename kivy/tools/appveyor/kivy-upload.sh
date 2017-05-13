pacman -S --noconfirm git rsync
ls /c
ls /c/kivy_wheels
$p=$(cygpath -u "$WHEEL_DIR")
ls $p
rsync -azvh -n -e "ssh -p 2458 StrictHostKeyChecking=no" "$(cygpath -u '$WHEEL_DIR')" root@159.203.106.198:/web/downloads/appveyor/kivy
