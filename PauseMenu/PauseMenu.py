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
JS_REP = 0.20

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

CONFIG_DIR = '/opt/retropie/configs/'
RETROARCH_CFG = CONFIG_DIR + 'all/retroarch.cfg'
PATH_VOLUMEJOY = '/opt/retropie/configs/all/VolumeJoy/'	

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []
btn_up = -1
btn_down = -1

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

    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return False

    if js_type == JS_EVENT_BUTTON and js_value == 1:
        #print "Button " + "number:" + str(js_number)
        #vol = int(run_cmd("amixer get PCM|grep -o [0-9]*%|sed 's/%//'"))
        #print vol

        vol = int(run_cmd("amixer get PCM|grep -o [0-9]*%|sed 's/%//'"))
        if js_number == btn_down:
            vol = (vol/6-1)*6+4
            if vol < 5:
                vol = 0
            #print "Decrease volume... " + str(vol)
        elif js_number == btn_up:
            vol = (vol/6+1)*6+4
            if vol > 95:
                vol = 100
            #print "Increase volume... " + str(vol)
        else:
            return False
 
        #vol = int(run_cmd("amixer get PCM|grep -o [0-9]*%|sed 's/%//'"))
        run_cmd("amixer set PCM -- " + str(vol) + "%")
        #lines = run_cmd("ps -aux | grep pngvolume").splitlines()
        #if len(lines) > 2:
        #    run_cmd("killall -9 pngvolume")
        kill_proc("pngvolume")
        os.system(PATH_VOLUMEJOY + "pngvolume -b0x0000 -l30000 -t1000 " + PATH_VOLUMEJOY + "volume" + str(vol/6) + ".png &")

    return True

def main():
    
    global btn_up, btn_down
    
    if os.path.isfile(PATH_VOLUMEJOY + "button.cfg") == False:
        return False

    f = open(PATH_VOLUMEJOY + "button.cfg", 'r')
    line = f.readline()
    words = line.split()
    btn_up = int(words[0])
    btn_down = int(words[1])

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
                    if time.time() - js_last[i] > JS_REP:
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
