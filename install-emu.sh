pip3 install pyudev

cp -f -r ./PauseMenu /opt/

if [[ ! -f /usr/bin/fbdump ]]; then
    cp /opt/PauseMenu/fbdump /opt/bin/fbdump
else
    cp /usr/bin/fbdump /opt/bin/fbdump
fi
chmod 755 /opt/bin/fbdump

/opt/bin/python3 ./PauseMenu/setup-emu.py /dev/input/js0

echo "Add the follwing line to /storage/.config/custom_start.sh"
echo "/opt/bin/python3 /opt/PauseMenu/PauseMenu4Emu.py /dev/input/js0 &"
echo ""
