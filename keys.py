#!/usr/bin/env python

import threading
import time
from scroller import Scroller
from evdev import InputDevice, categorize, ecodes
from select import select
from fcntl import ioctl
from mpd import MPDClient

devices = map(InputDevice, (
        '/dev/input/by-id/usb-1d57_ad02-event-kbd', 
        '/dev/input/by-id/usb-1d57_ad02-if01-event-mouse'
))
devices = {dev.fd : dev for dev in devices}

for dev in devices.values():
    dev.grab()

#print(devices.values()[0].capabilities(verbose=True))
MODIFIERS = ['KEY_LEFTSHIFT', 'KEY_LEFTCTRL', 'KEY_LEFTMETA', 'KEY_LEFTALT',
    'KEY_RIGHTALT', 'KEY_RIGHTCTRL', 'KEY_RIGHTSHIFT']
    
modifier_state = {x: False for x in MODIFIERS}

while True:
    r,w,x = select(devices, [], [])
    for fd in r:
        for event in devices[fd].read():
            if event.type == ecodes.EV_KEY:
                data = categorize(event)
                if data.keycode in MODIFIERS:
                    if data.keystate == data.key_down:
                        modifier_state[data.keycode] = True
                    elif data.keystate == data.key_up:
                        modifier_state[data.keycode] = False
                else:
                    if data.keystate == data.key_down:
                        print('')
                        keycode = data.keycode
                        if type(keycode) != list:
                            keycode = [keycode]
                        for k in keycode:
                            tag = '/'.join([x for x in MODIFIERS if modifier_state[x]] + [k])
                            print(tag)
                        print('')
            elif event.type == ecodes.EV_REL:
                delta = event.value
                axis = event.code
                print(axis, delta)
