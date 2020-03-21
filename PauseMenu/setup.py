#!/usr/bin/python

import os, sys, struct, time, fcntl, termios, signal
import curses, errno, re
from pyudev import Context
from subprocess import *
import xml.etree.ElementTree as ET


#    struct js_event {
#        __u32 time;     /* event timestamp in milliseconds */
#        __s16 value;    /* value */
#        __u8 type;      /* event type */
#        __u8 number;    /* axis/button number */
#    };

JS_MIN = -32768
JS_MAX = 32768
JS_REP = 0.02

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

if os.path.isdir('/opt/retropie') == True:
    OPT = '/opt/retropie'
elif os.path.isdir('/opt/retroarena') == True:
    OPT = '/opt/retroarena'
PATH_PAUSEMENU = OPT+'/configs/all/PauseMenu/'
ES_INPUT = OPT+'/configs/all/emulationstation/es_input.cfg'
RETROARCH_CFG = OPT+'/configs/all/retroarch-joypads/'

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []

def load_es_cfg():
    doc = ET.parse(ES_INPUT)
    root = doc.getroot()
    #tag = root.find('inputConfig')
    tags = root.findall('inputConfig')
    num = 1
    print '\n'
    for i in tags:
        print str(num) + ". " + i.attrib['deviceName']
        num = num+1
    dev_select = input('\nSelect your joystick: ')

    return tags[dev_select-1].attrib['deviceName']

def set_layout():
    print '\n -(1)-----  -(2)-----  -(3)----- '
    print ' | X Y L |  | Y X L |  | L Y X | '
    print ' | A B R |  | B A R |  | R B A | '
    print ' ---------  ---------  --------- '

    es_conf = input('\nSelect your joystick layout: ')
    
    f = open(PATH_PAUSEMENU + "images/control/layout.cfg", 'w')
    f.write(str(es_conf)+'\n')
    f.close()
    

def load_retroarch_cfg(dev_name):
    print 'Device Name: ', dev_name, '\n'
    
    retroarch_key = {}
    f = open(RETROARCH_CFG + dev_name + '.cfg', 'r')
    while True:
        line = f.readline()
        if not line: 
            break
        if '_btn' in line or '_axis' in line:
            line = line.replace('\n','')
            line = line.replace('input_','')
            line = line.replace('_btn','')
            line = line.replace('_axis','')
            words = line.split()
            retroarch_key[words[0]] = words[2].replace('"','')
    f.close()

    use_pause = input('Use an extra Pause button? (1=No, 2=Yes): ')
    if use_pause == 2:
        btn_pause = -1
        js_devs, js_fds = open_devices()
        print "\nPush a button for PauseMenu"
        while btn_pause == -1:
            for fd in js_fds:
                event = read_event(fd)
                if event:
                    btn_pause = process_event(event)
            time.sleep(0.1)
        retroarch_key['pausemenu'] = str(btn_pause)
    else:
        print "\n"
    
    f = open(PATH_PAUSEMENU + "button.cfg", 'w')
    f.write(str(retroarch_key)+'\n')
    f.close()

def signal_handler(signum, frame):
    close_fds(js_fds)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def get_devices():
    devs = []
    if sys.argv[1] == '/dev/input/jsX':
        for dev in os.listdir('/dev/input'):
            if dev.startswith('js'):
                devs.append('/dev/input/' + dev)
    else:
        devs.append(sys.argv[1])

    return devs

def open_devices():
    devs = get_devices()

    fds = []
    for dev in devs:
        try:
            fds.append(os.open(dev, os.O_RDONLY | os.O_NONBLOCK ))
        except:
            pass

    return devs, fds


def close_fds(fds):
    for fd in fds:
        os.close(fd)

def read_event(fd):
    while True:
        try:
            event = os.read(fd, event_size)
        except OSError, e:
            if e.errno == errno.EWOULDBLOCK:
                return None
            return False
        else:
            return event

def process_event(event):

    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return -1

    if js_type == JS_EVENT_BUTTON and js_value == 1:
        print ">> button index:", js_number
        return js_number

    return -1


dev_name = load_es_cfg()
load_retroarch_cfg(dev_name)

'''
btn_select = -1
btn_start = -1
btn_a = -1
event = -1

f = open(PATH_PAUSEMENU + "button.cfg", 'w')
js_devs, js_fds = open_devices()

print "\nPush a button for SELECT"
while btn_select == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_select = process_event(event)
    time.sleep(0.1)

print "Push a button for START"
while btn_start == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_start = process_event(event)
    time.sleep(0.1)

print "Push a button for ButtonA"
while btn_a == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_a = process_event(event)
    time.sleep(0.1)

#f.write(str(axis_up) + "\n" + str(axis_down) + "\n" + str(btn_select) + "\n" + str(btn_start))
f.write(str(btn_select) + " " + str(btn_start) + " " + str(btn_a))
f.close()
'''

joypad_cfg = RETROARCH_CFG + dev_name + ".cfg"
if os.path.isfile(joypad_cfg + ".org") == False :
    os.system("cp '" + joypad_cfg + "' '" + joypad_cfg + ".org'")

os.system("sed -i '/input_exit_emulator_btn/d' '" + joypad_cfg + "'")

if len(sys.argv) > 2 and sys.argv[2] == '-full':
    set_layout()
    
    os.system("sed -i '/input_enable_hotkey_btn/d' '" + joypad_cfg + "'")
    os.system("sed -i '/input_reset_btn/d' '" + joypad_cfg + "'")
    os.system("sed -i '/input_menu_toggle_btn/d' '" + joypad_cfg + "'")
    os.system("sed -i '/input_state_slot_increase_btn/d' '" + joypad_cfg + "'")
    os.system("sed -i '/input_state_slot_decrease_btn/d' '" + joypad_cfg + "'")
    
    retroarch_cfg = [
        OPT+"/configs/all/retroarch.cfg",
        OPT+"/configs/arcade/retroarch.cfg",
        OPT+"/configs/dreamcast/retroarch.cfg",
        OPT+"/configs/fba/retroarch.cfg",
        OPT+"/configs/gba/retroarch.cfg",
        OPT+"/configs/gbc/retroarch.cfg",
        OPT+"/configs/mame-libretro/retroarch.cfg",
        OPT+"/configs/megadrive/retroarch.cfg",
        OPT+"/configs/msx/retroarch.cfg",
        OPT+"/configs/n64/retroarch.cfg",
        OPT+"/configs/nes/retroarch.cfg",
        OPT+"/configs/psp/retroarch.cfg",
        OPT+"/configs/psx/retroarch.cfg",
        OPT+"/configs/snes/retroarch.cfg"
    ]
    swap_line = {
        'input_enable_hotkey = ':'"num2"',
        'input_reset = ':'"z"',
        'input_menu_toggle = ':'"s"',
        'input_save_state = ':'"f2"',
        'input_load_state = ':'"f4"',
        'input_state_slot_decrease = ':'"left"',
        'input_state_slot_increase = ':'"right"',
        'video_gpu_screenshot = ':'"true"',
        'savestate_thumbnail_enable = ':'"true"'
    }

    for cfg in retroarch_cfg:
        if os.path.isfile(cfg) == True:
            if os.path.isfile(cfg + ".org") == False :
                os.system("cp " + cfg + " " + cfg + ".org")
            os.system("cp " + cfg + " " + cfg + ".tmp")
            fr = open(cfg + ".tmp", "r")
            fw = open(cfg, "w")
            while True:
                line = fr.readline()
                if not line: break
                for k in swap_line.keys():
                    if k in line:
                        line = k + swap_line[k] + "\n"
                fw.write(line)
            fr.close()
            fw.close()
            os.system("sed -i '/input_player1_turbo_btn/d' '" + cfg + "'")

'''        
os.system("sudo sed -i 's/input_exit_emulator_btn/#input_exit_emulator_btn/g' " 
          + "'/opt/retropie/configs/all/retroarch-joypads/"
          + dev_name
          + ".cfg'")
'''
