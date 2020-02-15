#!/usr/bin/python

import os, sys
from subprocess import *
import xml.etree.ElementTree as ET

ES_INPUT = '/opt/retropie/configs/all/emulationstation/es_input.cfg'
RETROARCH_CFG = '/opt/retropie/configs/all/retroarch-joypads/'

def load_es_cfg():
    doc = ET.parse(ES_INPUT)
    root = doc.getroot()
    #tag = root.find('inputConfig')
    tags = root.findall('inputConfig')
    num = 1
    for i in tags:
        print str(num) + ". " + i.attrib['deviceName']
        num = num+1
    dev_select = input('\nSelect your joystick: ')

    return tags[dev_select-1].attrib['deviceName']

dev_name = load_es_cfg()

joypad_cfg = "/opt/retropie/configs/all/retroarch-joypads/" + dev_name + ".cfg"
if os.path.isfile(joypad_cfg + ".org") == True :
    os.system("cp " + joypad_cfg + ".org " + joypad_cfg)

retroarch_cfg = [
    "/opt/retropie/configs/all/retroarch.cfg",
    "/opt/retropie/configs/arcade/retroarch.cfg",
    "/opt/retropie/configs/dreamcast/retroarch.cfg",
    "/opt/retropie/configs/fba/retroarch.cfg",
    "/opt/retropie/configs/gba/retroarch.cfg",
    "/opt/retropie/configs/gbc/retroarch.cfg",
    "/opt/retropie/configs/mame-libretro/retroarch.cfg",
    "/opt/retropie/configs/megadrive/retroarch.cfg",
    "/opt/retropie/configs/msx/retroarch.cfg",
    "/opt/retropie/configs/n64/retroarch.cfg",
    "/opt/retropie/configs/nes/retroarch.cfg",
    "/opt/retropie/configs/psp/retroarch.cfg",
    "/opt/retropie/configs/psx/retroarch.cfg",
    "/opt/retropie/configs/snes/retroarch.cfg"
]

for cfg in retroarch_cfg:
    if os.path.isfile(cfg + ".org") == True :
        os.system("cp " + cfg + ".org " + cfg)

'''
os.system("sudo sed -i 's/#input_exit_emulator_btn/input_exit_emulator_btn/g' " 
          + "'/opt/retropie/configs/all/retroarch/autoconfig/"
          + dev_name
          + ".cfg'")
'''