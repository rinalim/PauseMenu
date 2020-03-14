# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

sudo apt-get install libjpeg8 -y
sudo apt-get install imagemagick -y
sudo apt-get install fonts-nanum -y
sudo apt-get install fonts-nanum-extra -y
sudo apt-get install python-pip python-pil -y
sudo apt-get install fbi -y
sudo pip install keyboard

rm -rf /opt/retroarena/configs/all/PauseMenu/
mkdir /opt/retroarena/configs/all/PauseMenu/
cp -f -r ./PauseMenu /opt/retroarena/configs/all/

cp ./PauseMenu/PauseMenu4FBdev.py /opt/retroarena/configs/all/PauseMenu/PauseMenu.py

sudo sed -i '/PauseMenu.py/d' /opt/retroarena/configs/all/runcommand-onstart.sh
echo 'sudo /usr/bin/python /opt/retroarena/configs/all/PauseMenu/PauseMenu.py /dev/input/js0 -full &' >> /opt/retroarena/configs/all/runcommand-onstart.sh
sudo sed -i '/PauseMenu.py/d' /opt/retroarena/configs/all/runcommand-onend.sh
echo 'sudo pkill -ef PauseMenu.py' >> /opt/retroarena/configs/all/runcommand-onend.sh

chgrp -R -v pi /opt/retroarena/configs/all/PauseMenu/ > /dev/null 2>&1
chown -R -v pi /opt/retroarena/configs/all/PauseMenu/ > /dev/null 2>&1

python ./PauseMenu/setup.py /dev/input/js0 -full