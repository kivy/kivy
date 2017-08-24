pacman -S --noconfirm git rsync
if [ ! -d "/home/appveyor/.ssh" ]; then
  mkdir "/home/appveyor/.ssh"
fi
echo -e "Host 159.203.106.198\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config
cp $(cygpath -u "C:\projects\kivy\kivy\tools\appveyor\id_rsa") ~/.ssh/id_rsa
rsync -avh -e "ssh -p 2458" "/c/kivy_wheels/" root@159.203.106.198:/web/downloads/appveyor/kivy
