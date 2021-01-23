pip3 install pyudev

cp -f -r ./PauseMenu /opt/

#sudo sed -i '/PauseMenu.py/d' /opt/retropie/configs/all/runcommand-onstart.sh
#echo 'sudo /usr/bin/python3 /opt/retropie/configs/all/PauseMenu/PauseMenu.py /dev/input/js0 &' >> /opt/retropie/configs/all/runcommand-onstart.sh
#sudo sed -i '/PauseMenu.py/d' /opt/retropie/configs/all/runcommand-onend.sh
#echo 'sudo pkill -ef PauseMenu.py' >> /opt/retropie/configs/all/runcommand-onend.sh

/opt/bin/python3 ./PauseMenu/setup-emu.py /dev/input/js0
