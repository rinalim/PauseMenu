#!/usr/bin/python

import os, sys, struct, time, fcntl, termios, signal
import curses, errno, re
from pyudev import Context
from subprocess import *

#    struct js_event {
#        __u32 time;     /* event timestamp in milliseconds */
#        __s16 value;    /* value */
#        __u8 type;      /* event type */
#        __u8 number;    /* axis/button number */
#    };

JS_MIN = -32768
JS_MAX = 32768
#JS_REP = 0.20
JS_REP = 0.001

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

CONFIG_DIR = '/opt/retropie/configs/all/'
RETROARCH_CFG = CONFIG_DIR + 'retroarch.cfg'
PATH_PAUSEMENU = CONFIG_DIR + 'PauseMenu/'	
VIEWER = PATH_PAUSEMENU + "omxiv-pause /tmp/pause.txt -f -t 5 -T blend --duration 200 -l 30001 -a center &"

SELECT_BTN_ON = False
START_BTN_ON = False
PAUSE_MODE_ON = False
UP_DOWN_ON = False

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []
btn_select = -1
btn_start = -1
btn_a = -1

def start_viewer():
    os.system("sudo fbi /opt/retropie/configs/all/PauseMenu/pause_resume.png -d /dev/fb0")

def stop_viewer():
    os.system("sudo killall fbi")
    
def change_viewer(position):
    if position == "UP":
        os.system("echo " + CONFIG_DIR + "PauseMenu/pause_resume.png > /tmp/pause.txt")
    if position == "DOWN":
        os.system("echo " + CONFIG_DIR + "PauseMenu/pause_stop.png > /tmp/pause.txt")
        
def run_cmd(cmd):
    # runs whatever in the cmd variable
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

def kill_proc(name):
    ps_grep = run_cmd("ps -aux | grep " + name + "| grep -v 'grep'")
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
        except OSError, e:
            if e.errno == errno.EWOULDBLOCK:
                return None
            return False

        else:
            return event

def process_event(event):

    global SELECT_BTN_ON
    global START_BTN_ON
    global PAUSE_MODE_ON
    global UP_DOWN_ON
    
    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return False

    if js_type == JS_EVENT_AXIS and js_number <= 7:
        '''
        if js_number % 2 == 0:
            if js_value <= JS_MIN * JS_THRESH:
                print "Left pushed"
            if js_value >= JS_MAX * JS_THRESH:
                print "Right pushed"
        '''
        if js_number % 2 == 1:
            if js_value <= JS_MIN * JS_THRESH:
                #print "Up pushed"
                if PAUSE_MODE_ON == True:
                    UP_DOWN_ON = True
                    change_viewer("UP")
            if js_value >= JS_MAX * JS_THRESH:
                #print "Down pushed"
                if PAUSE_MODE_ON == True:
                    UP_DOWN_ON = False 
                    change_viewer("DOWN")
    
    if js_type == JS_EVENT_BUTTON:
        if js_value == 1:
            if js_number == btn_a:
                if PAUSE_MODE_ON == True and UP_DOWN_ON == True:
                    print "Resume"
                    stop_viewer()
                    os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                    PAUSE_MODE_ON = False
                if PAUSE_MODE_ON == True and UP_DOWN_ON == False:
                    print "Kill"
                    stop_viewer()
                    os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &");
                    os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGINT");
                    return False
            elif js_number == btn_select:
                SELECT_BTN_ON = True
            elif js_number == btn_start:
                START_BTN_ON = True
            else:
                return False
        elif js_value == 0:
            if js_number == btn_select:
                SELECT_BTN_ON = False
            elif js_number == btn_start:
                START_BTN_ON = False
            else:
                return False
        
        if SELECT_BTN_ON == True and START_BTN_ON == True:
            if PAUSE_MODE_ON == False:
                #print "Select+Start Pushed"
                PAUSE_MODE_ON = True;
                UP_DOWN_ON = True;            # up
                SELECT_BTN_ON = False;
                START_BTN_ON = False;
                start_viewer()
                os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGSTOP &");
    
    return True

def main():
    
    global btn_select, btn_start, btn_a
    
    if os.path.isfile(PATH_PAUSEMENU + "button.cfg") == False:
        return False
   
    f = open(PATH_PAUSEMENU + "button.cfg", 'r')
    line = f.readline()
    words = line.split()
    btn_select = int(words[0])
    btn_start = int(words[1])
    btn_a = int(words[2])

    js_fds=[]
    rescan_time = time.time()
    while True:
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