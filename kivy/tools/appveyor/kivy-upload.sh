pacman -S --noconfirm git rsync
$p=$(cygpath -u "$WHEEL_DIR")
rsync -azvhen "ssh -p 2458 StrictHostKeyChecking=no" "$p" root@159.203.106.198:/web/downloads/appveyor/kivy
