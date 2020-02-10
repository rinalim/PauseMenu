# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

sudo apt-get install libjpeg8 -y

rm -rf /opt/retropie/configs/all/PauseMenu/
mkdir /opt/retropie/configs/all/PauseMenu/
cp -f -r ./PauseMenu /opt/retropie/configs/all/

sudo chmod 755 /opt/retropie/configs/all/PauseMenu/omxiv-pause

sudo sed -i '/PauseMenu.py/d' /opt/retropie/configs/all/runcommand-onstart.sh
echo '/usr/bin/python /opt/retropie/configs/all/PauseMenu/PauseMenu.py /dev/input/js0 &' >> /opt/retropie/configs/all/runcommand-onstart.sh

chgrp -R -v pi /opt/retropie/configs/all/PauseMenu/
chown -R -v pi /opt/retropie/configs/all/PauseMenu/

python ./PauseMenu/setup.py /dev/input/js0
