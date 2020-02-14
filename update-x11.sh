# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

mkdir -p ./backup/save

cp /opt/retropie/configs/all/PauseMenu/button.cfg ./backup
cp /opt/retropie/configs/all/PauseMenu/images/control/layout.cfg ./backup
cp -rf /opt/retropie/configs/all/PauseMenu/images/save/* ./backup/save

rm -rf /opt/retropie/configs/all/PauseMenu/
mkdir /opt/retropie/configs/all/PauseMenu/
cp -rf ./PauseMenu /opt/retropie/configs/all/

cp ./PauseMenu/PauseMenu4X11.py /opt/retropie/configs/all/PauseMenu/PauseMenu.py

cp ./backup/button.cfg /opt/retropie/configs/all/PauseMenu
cp ./backup/layout.cfg  /opt/retropie/configs/all/PauseMenu/images/control
cp -rf ./backup/save/* /opt/retropie/configs/all/PauseMenu/images/save

rm -rf ./backup

sudo chmod 755 /opt/retropie/configs/all/PauseMenu/omxiv-pause

chgrp -R -v pi /opt/retropie/configs/all/PauseMenu/ > /dev/null 2>&1
chown -R -v pi /opt/retropie/configs/all/PauseMenu/ > /dev/null 2>&1
