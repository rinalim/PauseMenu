# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

mkdir -p ./backup/save

cp /opt/retroarena/configs/all/PauseMenu/button.cfg ./backup
cp /opt/retroarena/configs/all/PauseMenu/images/control/layout.cfg ./backup
cp -rf /opt/retroarena/configs/all/PauseMenu/images/save/* ./backup/save

rm -rf /opt/retroarena/configs/all/PauseMenu/
mkdir /opt/retroarena/configs/all/PauseMenu/
cp -rf ./PauseMenu /opt/retroarena/configs/all/

cp ./PauseMenu/PauseMenu4FBdev.py /opt/retroarena/configs/all/PauseMenu/PauseMenu.py

cp ./backup/button.cfg /opt/retroarena/configs/all/PauseMenu
cp ./backup/layout.cfg  /opt/retroarena/configs/all/PauseMenu/images/control
cp -rf ./backup/save/* /opt/retroarena/configs/all/PauseMenu/images/save

rm -rf ./backup

chgrp -R -v pigaming /opt/retroarena/configs/all/PauseMenu/ > /dev/null 2>&1
chown -R -v pigaming /opt/retroarena/configs/all/PauseMenu/ > /dev/null 2>&1
