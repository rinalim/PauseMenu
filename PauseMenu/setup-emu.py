import os, sys, struct, time, fcntl, termios, signal, errno
from pyudev import Context
from subprocess import *
import xml.etree.ElementTree as ET

JS_MIN = -32768
JS_MAX = 32768
JS_REP = 0.02

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

PATH_PAUSEMENU = '/opt/PauseMenu/'
ES_INPUT = '/storage/.emulationstation/es_input.cfg'
RETROARCH_CFG = '/storage/joypads/'

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []

def load_es_cfg():
    doc = ET.parse(ES_INPUT)
    root = doc.getroot()
    #tag = root.find('inputConfig')
    tags = root.findall('inputConfig')
    num = 1
    print('\n')
    for i in tags:
        print(str(num) + ". " + i.attrib['deviceName'])
        num = num+1
    dev_select = int(input('\nSelect your joystick: '))

    return tags[dev_select-1].attrib['deviceName']

def set_layout():
    print('\n -(1)-----  -(2)-----  -(3)----- ')
    print(' | X Y L |  | Y X L |  | L Y X | ')
    print(' | A B R |  | B A R |  | R B A | ')
    print(' ---------  ---------  --------- ')

    es_conf = input('\nSelect your joystick layout: ')

    f = open(PATH_PAUSEMENU + "images/control/layout.cfg", 'w')
    f.write(str(es_conf)+'\n')
    f.close()

def load_retroarch_cfg(dev_name):
    print('Device Name: ', dev_name, '\n')

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

    use_pause = int(input('Use an extra Pause button? (1=No, 2=Yes): '))
    if use_pause == 2:
        btn_pause = -1
        js_devs, js_fds = open_devices()
        print("\nPush a button for PauseMenu")
        while btn_pause == -1:
            for fd in js_fds:
                event = read_event(fd)
                if event:
                    btn_pause = process_event(event)
            time.sleep(0.1)
        retroarch_key['pausemenu'] = str(btn_pause)
    else:
        print("\n")

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
        #except OSError, e:
        except OSError as e:
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
        print(">> button index:", js_number)
        return js_number

    return -1


dev_name = load_es_cfg()
load_retroarch_cfg(dev_name)

joypad_cfg = RETROARCH_CFG + dev_name + ".cfg"
if os.path.isfile(joypad_cfg + ".org") == False :
    os.system("cp '" + joypad_cfg + "' '" + joypad_cfg + ".org'")

#os.system("sed -i '/input_exit_emulator_btn/d' '" + joypad_cfg + "'")
