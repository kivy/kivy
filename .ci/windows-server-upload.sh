#!/usr/bin/env bash
pacman -S --noconfirm git rsync openssl

if [ ! -d ~/.ssh ]; then
  mkdir ~/.ssh
fi
printf "%s" "$UBUNTU_UPLOAD_KEY" > ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519

echo -e "Host $1\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config
echo "copying $3 from $2 to root@$1:/web/downloads/$4"
rsync -avh -e "ssh -p 2458" --include="*/" --include="$3" --exclude="*" "$2/" "root@$1:/web/downloads/$4"
