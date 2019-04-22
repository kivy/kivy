pacman -S --noconfirm git rsync
if [ ! -d "/home/appveyor/.ssh" ]; then
  mkdir "/home/appveyor/.ssh"
fi
echo -e "Host $1\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config
cp "$(dirname "$0")/id_rsa" ~/.ssh/id_rsa
echo "copying $3 from $(cygpath -u "$2") to root@$1:/web/downloads/$4"
rsync -avh -e "ssh -p 2458" --include="*/" --include="$3" --exclude="*" "$(cygpath -u "$2")/" "root@$1:/web/downloads/$4"
