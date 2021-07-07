pip3 install pyudev

cp -f -r ./PauseMenu /opt/

if [[ ! -f /usr/bin/fbdump ]]; then
    echo "Copy fbdump"
    cp /opt/PauseMenu/fbdump-v1 /opt/bin/fbdump
    chmod 755 /opt/bin/fbdump
fi
/opt/bin/python3 ./PauseMenu/setup-emu.py /dev/input/js0

echo "Add the follwing line to /storage/.config/custom_start.sh"
echo "/opt/bin/python3 /opt/PauseMenu/PauseMenu4Emu.py /dev/input/js0 &"
echo ""
