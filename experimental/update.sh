# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

mkdir ./backup
cp -f -r /opt/retropie/configs/all/PauseMenu/image/save/* ./backup

rm -rf /opt/retropie/configs/all/PauseMenu/
mkdir /opt/retropie/configs/all/PauseMenu/
cp -f -r ./PauseMenu /opt/retropie/configs/all/

cp -f -r ./backup/* /opt/retropie/configs/all/PauseMenu/image/save

sudo chmod 755 /opt/retropie/configs/all/PauseMenu/omxiv-pause

chgrp -R -v pi /opt/retropie/configs/all/PauseMenu/ > /dev/null 2>&1
chown -R -v pi /opt/retropie/configs/all/PauseMenu/ > /dev/null 2>&1
