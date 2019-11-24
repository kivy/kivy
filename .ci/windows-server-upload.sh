#!/usr/bin/env bash
pacman -S --noconfirm git rsync
if [ ! -d "$HOME/.ssh" ]; then
  mkdir "$HOME/.ssh"
fi

mv .ci/id_rsa ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

echo -e "Host $1\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config
echo "copying $3 from $2 to root@$1:/web/downloads/$4"
rsync -avh -e "ssh -p 2458" --include="*/" --include="$3" --exclude="*" "$2/" "root@$1:/web/downloads/$4"
