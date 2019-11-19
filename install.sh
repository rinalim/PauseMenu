# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

sudo cp ./libraspidmx.so.1 /usr/lib

rm -rf /opt/retropie/configs/all/PauseMenu/
mkdir /opt/retropie/configs/all/PauseMenu/
cp -f -r ./PauseMenu /opt/retropie/configs/all/

sudo chmod 755 /opt/retropie/configs/all/PauseMenu/omxiv-pause

sudo sed -i '/PauseMenu.py/d' /opt/retropie/configs/all/autostart.sh
sudo sed -i '1i\\/usr/bin/python /opt/retropie/configs/all/PauseMenu/PauseMenu.py /dev/input/js0 &' /opt/retropie/configs/all/autostart.sh

python ./PauseMenu/setup.py /dev/input/js0

echo
echo "Setup Completed. Reboot after 3 Seconds."
sleep 3
reboot
