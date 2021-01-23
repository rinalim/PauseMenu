#-*-coding: utf-8 -*-
#!/usr/bin/python3

import os, sys, struct, time, fcntl, termios, signal
import curses, errno
from pyudev import Context
from subprocess import *
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import ast
import fb

JS_MIN = -32768
JS_MAX = 32768
JS_REP = 0.20

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

#RETROARCH_CFG = CONFIG_DIR + 'all/retroarch.cfg'
PATH_PAUSEMENU = '/opt/PauseMenu/'
VIEWER = PATH_PAUSEMENU + "omxiv-pause /tmp/pause.txt -f -t 5 -T blend --duration 20 -l 30001 -a center"

SELECT_BTN_ON = False
START_BTN_ON = False
UP_ON = False
DOWN_ON = False
PAUSE_MODE_ON = False

VIEW_MODE = "default"
MENU_INDEX = 0
STATE_INDEX = 0
LAYOUT_INDEX = 0

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []
btn_select = -1
btn_start = -1
btn_pausemenu = -1
btn_a = -1
btn_x = -1
button_num = 0
layout_num = 0

retroarch_key = {}
user_key = {}
btn_map = {}

es_conf = 1
romname = ""
sysname = ""
corename = ""

def run_cmd(cmd):
    # runs whatever in the cmd variable
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output.decode()

def cmp(a, b):
    return (a > b) - (a < b)
    
def full_arg():
    if len(sys.argv) > 2 and sys.argv[2] == '-full':
        return True
    else:
        return False
        
def load_button():

    global retroarch_key

    f = open(PATH_PAUSEMENU + "button.cfg", 'r')
    retroarch_key = ast.literal_eval(f.readline())
    f.close()

def show_pause():
    os.system('/storage/fbdump > /tmp/fbdump.ppm')
    img_dump = Image.open('/tmp/fbdump.ppm')
    img_pause = Image.open('/opt/PauseMenu/images/pause_emu.png')
    img_dump.paste(img_pause, (0,0), img_pause)
    fb.save_img(img_dump)
    os.system('cat /tmp/fbdump /tmp/fbdump > /dev/fb0')

def start_viewer():
    if VIEW_MODE == "fba":
        submenu = "fba/"+romname
    else:
        submenu = "libretro"
    if os.path.isfile(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_resume.png") == True :
        update_image(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_resume.png", "/tmp/pause.txt")
        os.system(VIEWER_BG + " &")
        os.system(VIEWER + get_location() + " &")
    if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
        if os.path.isfile(PATH_PAUSEMENU + "images/control/" + submenu + "_layout0.png") == True :
            update_image(PATH_PAUSEMENU + "images/control/" + submenu + "_layout0.png", "/tmp/pause_layout.txt")
        os.system(VIEWER_LAYOUT + get_location() + " &")

def start_viewer_osd():
    if is_running("omxiv-pause") == False:
        if VIEW_MODE == "fba" and os.path.isfile(PATH_PAUSEMENU + "images/control/fba/" + romname + "_osd.png") == True :
            update_image(PATH_PAUSEMENU + "images/control/fba/" + romname + "_osd.png", "/tmp/pause_osd.txt")
            os.system(VIEWER_OSD + get_location() +" &")

def start_viewer_saving():
    if is_running("omxiv-pause") == False:
        if os.path.isfile(PATH_PAUSEMENU + "images/saving.gif") == True :
            fbset = run_cmd("fbset -s | grep mode | grep -v endmode | awk '{print $2}'").replace('"', '')
            res_x = fbset.split("x")[0]
            res_y = fbset.split("x")[1].replace('\n', '')
            params = " --win " + str(int(res_x)-200) + "," + str(int(res_y)-100) + "," + res_x + "," + res_y
            update_image(PATH_PAUSEMENU + "images/saving.gif", "/tmp/pause.txt")
            os.system(VIEWER + params + " " + get_location() +" &")

def start_viewer_failed():
    if is_running("omxiv-pause") == False:
        if os.path.isfile(PATH_PAUSEMENU + "images/failed.png") == True :
            fbset = run_cmd("fbset -s | grep mode | grep -v endmode | awk '{print $2}'").replace('"', '')
            res_x = fbset.split("x")[0]
            res_y = fbset.split("x")[1].replace('\n', '')
            params = " --win " + str(int(res_x)-200) + "," + str(int(res_y)-100) + "," + res_x + "," + res_y
            update_image(PATH_PAUSEMENU + "images/failed.png", "/tmp/pause.txt")
            os.system(VIEWER + params + " " + get_location() +" &")

def stop_viewer():
    if is_running("omxiv-pause") == True:
        os.system("killall omxiv-pause")
    
def change_viewer(menu, index):
    if VIEW_MODE == "fba":
        submenu = "fba/"+romname
    else:
        submenu = "libretro"
    if index == "0":
       state_index = "state"
    else:
       state_index = "state" + index

    if menu == "RESUME":
        update_image(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_resume.png", "/tmp/pause.txt")
        if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
            if index == "0":
                update_image(PATH_PAUSEMENU + "images/control/" + submenu + "_layout0.png", "/tmp/pause_layout.txt")
    elif menu == "STOP":
        update_image(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_stop.png", "/tmp/pause.txt")
        if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
            if index == "0":
                update_image(PATH_PAUSEMENU + "images/control/" + submenu + "_layout0.png", "/tmp/pause_layout.txt")
    elif menu == "RESET":
        update_image(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_reset.png", "/tmp/pause.txt")
        if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
            if index == "0":
                update_image(PATH_PAUSEMENU + "images/control/" + submenu + "_layout0.png", "/tmp/pause_layout.txt")
    elif menu == "SAVE":
        update_image(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png", "/tmp/pause.txt")
        if os.path.isfile(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + "." + state_index + ".png") == True :
            update_image(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + "." + state_index + ".png", "/tmp/pause_layout.txt")
        else:
            update_image(PATH_PAUSEMENU + "images/save/" + state_index + ".png", "/tmp/pause_layout.txt")
    elif menu == "LOAD":
        update_image(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png", "/tmp/pause.txt")
        if os.path.isfile(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + "." + state_index + ".png") == True :
            update_image(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + "." + state_index + ".png", "/tmp/pause_layout.txt")
        else:
            update_image(PATH_PAUSEMENU + "images/save/" + state_index + ".png", "/tmp/pause_layout.txt")
    elif menu == "BUTTON":
        if VIEW_MODE == "fba":
            update_image(PATH_PAUSEMENU + "images/" + sysname + "_button" + str(es_conf) + ".png", "/tmp/pause.txt")
            update_image(PATH_PAUSEMENU + "images/control/" + submenu + "_layout" + index + ".png", "/tmp/pause_layout.txt")

def is_running(pname):
    ps_grep = run_cmd("/usr/bin/ps -ef | grep " + pname + " | grep -v grep | grep -v bash")
    if len(ps_grep) > 1:
        return True
    else:
        return False
    
def kill_proc(name):
    ps_grep = run_cmd("/usr/bin/ps -aux | grep " + name + "| grep -v 'grep'")
    if len(ps_grep) > 1: 
        os.system("killall " + name)

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
        except OSError as e:
            if e.errno == errno.EWOULDBLOCK:
                return None
            return False

        else:
            return event
    
def process_event(event):

    global SELECT_BTN_ON, START_BTN_ON, UP_ON, DOWN_ON
    global PAUSE_MODE_ON, MENU_INDEX, STATE_INDEX, LAYOUT_INDEX
    
    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return False

    if js_type == JS_EVENT_AXIS and js_number <= 7:
        if js_number % 2 == 0:
            UP_ON = False
            DOWN_ON = False
            if js_value <= JS_MIN * JS_THRESH:
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 4:
                        if STATE_INDEX > 0:
                            STATE_INDEX = STATE_INDEX-1
                            change_viewer("SAVE", str(STATE_INDEX))
                    elif MENU_INDEX == 5:
                        if STATE_INDEX > 0:
                            STATE_INDEX = STATE_INDEX-1
                            change_viewer("LOAD", str(STATE_INDEX))
                    elif MENU_INDEX == 6:
                        if LAYOUT_INDEX > 1:
                            LAYOUT_INDEX = LAYOUT_INDEX-1
                            change_viewer("BUTTON", str(LAYOUT_INDEX))
            if js_value >= JS_MAX * JS_THRESH:
                if PAUSE_MODE_ON == True:                     
                    if MENU_INDEX == 4:
                        if STATE_INDEX < 3:
                            STATE_INDEX = STATE_INDEX+1
                            change_viewer("SAVE", str(STATE_INDEX))
                    elif MENU_INDEX == 5:
                        if STATE_INDEX < 3:
                            STATE_INDEX = STATE_INDEX+1
                            change_viewer("LOAD", str(STATE_INDEX))
                    elif MENU_INDEX == 6:
                        if LAYOUT_INDEX < layout_num:
                            LAYOUT_INDEX = LAYOUT_INDEX+1
                            change_viewer("BUTTON", str(LAYOUT_INDEX))
        elif js_number % 2 == 1:
            if js_value <= JS_MIN * JS_THRESH:
                UP_ON = True
                DOWN_ON = False
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 2:
                        MENU_INDEX = 1
                        change_viewer("RESUME", "-1")
                    elif MENU_INDEX == 3:
                        MENU_INDEX = 2
                        change_viewer("STOP", "-1")
                    elif MENU_INDEX == 4:
                        MENU_INDEX = 3
                        change_viewer("RESET", "0")
                    elif MENU_INDEX == 5:
                        MENU_INDEX = 4
                        STATE_INDEX = 0
                        change_viewer("SAVE", "0")
                    elif MENU_INDEX == 6:
                        MENU_INDEX = 5
                        STATE_INDEX = 0
                        change_viewer("LOAD", "0")
                elif SELECT_BTN_ON == True:
                    #print "OSD mode on"
                    start_viewer_osd()
            if js_value >= JS_MAX * JS_THRESH:
                DOWN_ON = True
                UP_ON = False
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 1:
                        MENU_INDEX = 2
                        change_viewer("STOP", "-1")
                    elif MENU_INDEX == 2:
                        if VIEW_MODE != "default":
                            MENU_INDEX = 3
                            change_viewer("RESET", "-1")
                    elif MENU_INDEX == 3:
                        MENU_INDEX = 4
                        STATE_INDEX = 0
                        change_viewer("SAVE", "0")
                    elif MENU_INDEX == 4:
                        MENU_INDEX = 5
                        STATE_INDEX = 0
                        change_viewer("LOAD", "0")
                    elif MENU_INDEX == 5:
                        if VIEW_MODE == "fba":
                            MENU_INDEX = 6
                            LAYOUT_INDEX = 1
                            change_viewer("BUTTON", "1")
                elif SELECT_BTN_ON == True:
                    #print "OSD mode off"
                    stop_viewer()
        if js_value == 0:
            UP_ON = False
            DOWN_ON = False
    
    if js_type == JS_EVENT_BUTTON:
        if js_value == 1:
            if js_number == btn_a:
                if PAUSE_MODE_ON == True:
                    #print "Kill"
                    #stop_viewer()
                    os.system("/usr/bin/ps -ef | grep /usr/bin/retroarch | grep -v grep | awk '{print $1}' | xargs kill -CONT &")
                    os.system("/usr/bin/ps -ef | grep /usr/bin/retroarch | grep -v grep | awk '{print $1}' | xargs kill -INT")
                    PAUSE_MODE_ON = False;
                    #close_fds(js_fds)
                    #sys.exit(0)
            elif js_number == btn_select:
                SELECT_BTN_ON = True
            elif js_number == btn_start:
                START_BTN_ON = True
            elif js_number == btn_pausemenu:
                SELECT_BTN_ON = True
                START_BTN_ON = True
            else:
                return False
        elif js_value == 0:
            if js_number == btn_select:
                SELECT_BTN_ON = False
            elif js_number == btn_start:
                START_BTN_ON = False
            elif js_number == btn_pausemenu:
                SELECT_BTN_ON = False
                START_BTN_ON = False
            else:
                return False

        if START_BTN_ON == True:
            if PAUSE_MODE_ON == True:
                PAUSE_MODE_ON = False
                START_BTN_ON = False
                print("Resume")
                #stop_viewer()
                os.system("/usr/bin/ps -ef | grep /usr/bin/retroarch | grep -v grep | awk '{print $1}' | xargs kill -CONT &")

        if SELECT_BTN_ON == True and START_BTN_ON == True:
            #print "Select+Start Pushed"
            print("Pause")
            if PAUSE_MODE_ON == False:
                PAUSE_MODE_ON = True
                MENU_INDEX = 1    # Resume
                #stop_viewer()
                #start_viewer()
                os.system("/usr/bin/ps -ef | grep /usr/bin/retroarch | grep -v grep | awk '{print $1}' | xargs kill -STOP &")
                show_pause()

    return True

def main():
    
    global btn_select, btn_start, btn_a, btn_x, btn_pausemenu
    global romname, sysname, corename, button_num, layout_num, VIEW_MODE, VIEWER_OSD

    load_button()
    
    btn_select = int(retroarch_key['select'])
    btn_start = int(retroarch_key['start'])
    btn_a = int(retroarch_key['a'])
    btn_x = int(retroarch_key['x'])
    if 'pausemenu' in retroarch_key:
        btn_pausemenu = int(retroarch_key['pausemenu'])
        btn_start = -1
 
    #print "PauseMenu is ready.."

    fb.ready_fb()
    js_fds=[]
    rescan_time = time.time()
    while True:
        if is_running("/usr/bin/retroarch") == False:
            time.sleep(3)
            print('wait for launching game')
            continue
 
        do_sleep = True
        if not js_fds:
            js_devs, js_fds = open_devices()
            if js_fds:
                i = 0
                current = time.time()
                js_last = [None] * len(js_fds)
                for js in js_fds:
                    js_last[i] = current
                    i += 1
            else:
                time.sleep(1)
        else:
            i = 0
            for fd in js_fds:
                event = read_event(fd)
                if event:
                    do_sleep = False
                    #if time.time() - js_last[i] > JS_REP:
                    if time.time() - js_last[i] > 0:                        
                        if process_event(event):
                            js_last[i] = time.time()
                elif event == False:
                    close_fds(js_fds)
                    js_fds = []
                    break
                i += 1

        if time.time() - rescan_time > 2:
            rescan_time = time.time()
            if cmp(js_devs, get_devices()):
                close_fds(js_fds)
                js_fds = []

        if do_sleep:
            time.sleep(0.01)

if __name__ == "__main__":
    import sys

    try:
        main()

    # Catch all other non-exit errors
    except Exception as e:
        sys.stderr.write("Unexpected exception: %s" % e)
        sys.exit(1)

    # Catch the remaining exit errors
    except:
        sys.exit(0)
