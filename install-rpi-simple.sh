# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

sudo apt install libjpeg8 -y
sudo apt install python3-pyudev -y

rm -rf /opt/retropie/configs/all/PauseMenu/
mkdir /opt/retropie/configs/all/PauseMenu/
cp -f -r ./PauseMenu /opt/retropie/configs/all/

sudo chmod 755 /opt/retropie/configs/all/PauseMenu/omxiv-pause

sudo sed -i '/PauseMenu.py/d' /opt/retropie/configs/all/runcommand-onstart.sh
echo 'sudo /usr/bin/python3 /opt/retropie/configs/all/PauseMenu/PauseMenu.py /dev/input/js0 &' >> /opt/retropie/configs/all/runcommand-onstart.sh
sudo sed -i '/PauseMenu.py/d' /opt/retropie/configs/all/runcommand-onend.sh
echo 'sudo pkill -ef PauseMenu.py' >> /opt/retropie/configs/all/runcommand-onend.sh

chgrp -R -v pi /opt/retropie/configs/all/PauseMenu/ > /dev/null 2>&1
chown -R -v pi /opt/retropie/configs/all/PauseMenu/ > /dev/null 2>&1

sudo python3 ./PauseMenu/setup.py /dev/input/js0
