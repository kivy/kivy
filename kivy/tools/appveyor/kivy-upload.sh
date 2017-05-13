pacman -S --noconfirm git rsync
rsync -azvhen "ssh -p 2458 StrictHostKeyChecking=no" "$WHEEL_DIR/" root@159.203.106.198:/web/downloads/appveyor/kivy
