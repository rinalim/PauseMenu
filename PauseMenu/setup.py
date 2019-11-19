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

PATH_PAUSEMODE = '/opt/retropie/configs/all/PauseMode/'

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []

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

btn_up = -1
btn_down = -1
btn_select = -1
btn_start = -1
f = open(PATH_PAUSEMODE + "button.cfg", 'w')
js_devs, js_fds = open_devices()

print "Push a button for UP"
while btn_up == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_up = process_event(event)
    time.sleep(0.1)
    
print "Push a button for DOWN"
while btn_down == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_down = process_event(event)
    time.sleep(0.1)

print "Push a button for SELECT"
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

f.write(str(btn_up) + "\n" + str(btn_down) + "\n" + str(btn_select) + " " + str(btn_start))
f.close()
