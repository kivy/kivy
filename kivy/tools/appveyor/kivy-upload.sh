pacman -S --noconfirm git rsync
if [ ! -d "~/.ssh" ]; then
  mkdir "~/.ssh"
fi
echo -e "Host 159.203.106.198\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config
cp $(cygpath -u "C:\projects\kivy\kivy\tools\appveyor\id_rsa.enc") ~/.ssh/id_rsa.enc
rsync -avh -n -e "ssh -p 2458" "/c/kivy_wheels/" root@159.203.106.198:/web/downloads/appveyor/kivy
