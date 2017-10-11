# fix locale
#sudo locale-gen pt_BR
#sudo locale-gen pt_BR.UTF-8
#sudo dpkg-reconfigure locales
#sudo update-locale LANG=pt_BR.UTF-8

sudo apt update && sudo apt upgrade
sudo apt install -y python-pip wbrazilian python-tk
sudo pip install --upgrade pip
sudo pip install psutil
sudo pip install sortedcontainers

git clone https://github.com/lucaspar/scrabble.git
cd scrabble