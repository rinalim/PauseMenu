# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

sudo cp ./libraspidmx.so.1 /usr/lib

rm -rf /opt/retropie/configs/all/VolumeJoy/
mkdir /opt/retropie/configs/all/VolumeJoy/
cp -f -r ./VolumeJoy /opt/retropie/configs/all/

sudo chmod 755 /opt/retropie/configs/all/VolumeJoy/pngvolume

sudo sed -i '/volume.py/d' /opt/retropie/configs/all/autostart.sh
sudo sed -i '1i\\/usr/bin/python /opt/retropie/configs/all/VolumeJoy/volume.py /dev/input/js0 &' /opt/retropie/configs/all/autostart.sh

python ./VolumeJoy/setup.py /dev/input/js0

echo
echo "Setup Completed. Reboot after 3 Seconds."
sleep 3
reboot
