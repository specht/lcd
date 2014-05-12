#!/usr/bin/env python

# http://www.soundjay.com/button-sounds-1.html

import copy
import datetime
import threading
import time
import json
import os
import string
import sys
from scroller import Scroller
from evdev import InputDevice, categorize, ecodes, events
from select import select
from fcntl import ioctl
from mpd import MPDClient

HOST = 'localhost'


mpd = MPDClient()
mpd.timeout = 10
mpd.idletimeout = None
while True:
    try:
        mpd.connect(HOST, 6600)
        break
    except:
        print("Trying again...")

#print("\n".join(dir(mpd)))
#print(mpd.status())
#print(mpd.list('album', 'Tocotronic'))
#exit(0)
    
mpd_lock = threading.Lock()

playlists = []
playlists_index = 0
mouse_movement = [0, 0]
mouse_movement_lock = threading.Lock()

launch_playlist = False
launch_playlist_lock = threading.Lock()

menu_showing = None
last_menu_showing = None
menu_showing_lock = threading.Lock()

hotkey_map = {}
hotkey_map_lock = threading.Lock()

hotkey_down = {}
store_next_hotkey = False

needs_sync = threading.Event()
syncing = False

def load_hotkeys():
    global hotkey_map
    try:
        with open('hotkeys.json', 'r') as f:
            hotkey_map = json.loads(f.read())
    except IOError:
        pass

def save_hotkeys():
    global hotkey_map
    with open('hotkeys.json', 'w') as f:
        f.write(json.dumps(hotkey_map))

load_hotkeys()

last_volume = int(mpd.status()['volume'])

hotkeys = ['KEY_MAIL', 'KEY_HOMEPAGE', 'KEY_LEFTALT/KEY_F4',
    'KEY_LEFTCTRL/KEY_LEFTALT/KEY_A', 'KEY_LEFTCTRL/KEY_LEFTALT/KEY_B',
    'KEY_LEFTCTRL/KEY_LEFTALT/KEY_C', 'KEY_LEFTCTRL/KEY_LEFTALT/KEY_D',
    'KEY_LEFTALT/KEY_ENTER', 'KEY_BACKSPACE', 'KEY_PAGEUP', 'KEY_PAGEDOWN',
    'KEY_LEFTMETA/KEY_E', 'KEY_LEFTMETA/KEY_D']

def sync_files():
    global syncing, needs_sync
    while True:
        needs_sync.wait()
        print("Starting sync_files...")
        syncing = True
        time.sleep(5.0)
        print("Finished sync_files.")
        syncing = False
        needs_sync.clear()
    
def seekcur(delta):    
    status = mpd.status()
    if 'elapsed' in status:
        newpos = int(float(status['elapsed'])) + delta
        if newpos < 0:
            newpos = 0
        mpd.seekid(status['songid'], newpos)
        
def cycle_menu_showing(force = None):
    global playlists, playlists_index, menu_showing, mpd
    
    menu_showing_lock.acquire()
    if force == None:
        if menu_showing == None:
            menu_showing = 'playlist'
        elif menu_showing == 'playlist':
            menu_showing = 'artist'
        elif menu_showing == 'artist':
            menu_showing = 'album'
        elif menu_showing == 'album':
            menu_showing = 'playlist'
        elif menu_showing[0:13] == 'artist-album-':
            menu_showing = 'album'
    else:
        menu_showing = force
    menu_showing_lock.release()
    # ----------------------------------------
    # mpd_lock is already acquire()
    items = []
    if menu_showing == 'playlist':
        items = [x['playlist'] for x in mpd.listplaylists()]
    elif menu_showing == 'artist':
        items = mpd.list('artist')
    elif menu_showing == 'album':
        items = mpd.list('album')
    elif menu_showing[0:13] == 'artist-album-':
        items = mpd.list('album', menu_showing[13:])
        items.append('(all titles)')
    # mpd_lock is already release()'d
    # ----------------------------------------
    items = [x for x in items if len(x) > 0]
    if len(items) == 0:
        items.append('(none)')
    playlists = sorted(items, cmp = sorter)
    playlists_index = 0
    
def handle_keys(tag, state):
    global last_volume, launch_playlist, hotkeys, menu_showing, hotkey_map, hotkey_down, store_next_hotkey
    if tag == 'KEY_ENTER':
        if state == events.KeyEvent.key_down:
            hotkey_down[tag] = datetime.datetime.now()
        elif state == events.KeyEvent.key_hold:
            if tag in hotkey_down:
                delta = (datetime.datetime.now() - hotkey_down[tag]).seconds
                if delta >= 1:
                    os.system("aplay button-30.wav")
                    store_next_hotkey = True
                    del hotkey_down[tag]
    elif tag in hotkeys and state == events.KeyEvent.key_down:
        if store_next_hotkey:
            os.system("aplay button-17.wav")
            store_next_hotkey = False
            playlist = []
            for entry in mpd.playlistinfo():
                playlist.append(entry['file'])
                hotkey_map_lock.acquire()
                hotkey_map[tag] = playlist
                save_hotkeys()
                hotkey_map_lock.release()
        else:
            hotkey_map_lock.acquire()
            if tag in hotkey_map:
                mpd.clear()
                for item in hotkey_map[tag]:
                    mpd.add(item)
                mpd.play()
            hotkey_map_lock.release()
    elif state == events.KeyEvent.key_down or state == events.KeyEvent.key_hold:
        if tag == 'KEY_STOPCD':
            mpd.clear()
        elif tag == 'KEY_PLAYPAUSE':
            mpd.pause()
        elif tag == 'KEY_PREVIOUSSONG':
            status = mpd.status()
            if 'elapsed' in status:
                pos = int(float(status['elapsed']))
                if pos < 2:
                    mpd.previous()
                else:
                    mpd.seekid(status['songid'], 0)
            else:
                mpd.previous()
                    
        elif tag == 'KEY_NEXTSONG':
            status = mpd.status()
            if 'song' in status:
                if int(status['song']) < int(status['playlistlength']) - 1:
                    mpd.next()
        elif tag == 'KEY_LEFTSHIFT/KEY_LEFTCTRL/KEY_B':
            seekcur(-5)
        elif tag == 'KEY_LEFTSHIFT/KEY_LEFTCTRL/KEY_F':
            seekcur(5)
        elif tag == 'KEY_VOLUMEDOWN':
            last_volume = max(int(mpd.status()['volume']) - 2, 0)
            mpd.setvol(last_volume)
        elif tag == 'KEY_VOLUMEUP':
            last_volume = min(int(mpd.status()['volume']) + 2, 100)
            mpd.setvol(last_volume)
        elif tag == 'KEY_MUTE':
            if int(mpd.status()['volume']) == 0:
                mpd.setvol(last_volume)
            else:
                mpd.setvol(0)
        elif tag == 'BTN_LEFT':
            # if we're in choose playlist mode, launch this playlist
            launch_playlist_lock.acquire()
            launch_playlist = True
            launch_playlist_lock.release()
        elif tag == 'BTN_RIGHT':
            cycle_menu_showing()
        
def input_handler():
    
    MODIFIERS = ['KEY_LEFTSHIFT', 'KEY_LEFTCTRL', 'KEY_LEFTMETA', 'KEY_LEFTALT',
        'KEY_RIGHTALT', 'KEY_RIGHTCTRL', 'KEY_RIGHTSHIFT']
    modifier_state = {x: False for x in MODIFIERS}
    global mouse_movement
    mouse_movement_counter = 0
    
    while True:
        try:
            devices = map(InputDevice, (
                 '/dev/input/by-id/usb-1d57_ad02-event-kbd', 
                 '/dev/input/by-id/usb-1d57_ad02-if01-event-mouse'
            ))
            devices = {dev.fd : dev for dev in devices}

            for dev in devices.values():
                dev.grab()
                
            #print(devices.values()[0].capabilities(verbose=True))
            while True:
                r,w,x = select(devices, [], [])
                for fd in r:
                    for event in devices[fd].read():
                        #print(event.type)
                        if event.type == ecodes.EV_KEY:
                            data = categorize(event)
                            if data.keycode in MODIFIERS:
                                if data.keystate == data.key_down:
                                    modifier_state[data.keycode] = True
                                elif data.keystate == data.key_up:
                                    modifier_state[data.keycode] = False
                            else:
                                keycode = data.keycode
                                if type(keycode) != list:
                                    keycode = [keycode]
                                for k in keycode:
                                    tag = '/'.join([x for x in MODIFIERS if modifier_state[x]] + [k])
                                    # -----------------------------------------
                                    mpd_lock.acquire()
                                    try:
                                        handle_keys(tag, data.keystate)
                                    except:
                                        raise
                                        pass
                                    finally:
                                        mpd_lock.release()
                                    # -----------------------------------------
                        elif event.type == ecodes.EV_REL:
                            axis = event.code
                            delta = event.value
                            
                            fire_this = True
                            if abs(delta) == 4:
                                mouse_movement_counter = 3
                            elif abs(delta) == 26:
                                if mouse_movement_counter > 0:
                                    mouse_movement_counter -= 1
                                    fire_this = False
                                else:
                                    mouse_movement_counter = 3
                            else:
                                fire_this = False

                            if fire_this:
                                delta = 1 if delta > 0 else -1
                                mouse_movement_lock.acquire()
                                mouse_movement = [axis, delta]
                                mouse_movement_lock.release()
                            
        except:
            print("Darn!")
            raise
            time.sleep(5.0)
            
def sorter(a, b):
    a = a.lower()
    b = b.lower()
    a_alpha = a[0] in string.ascii_lowercase
    b_alpha = b[0] in string.ascii_lowercase
    if a_alpha != b_alpha:
        if a_alpha == True and b_alpha == False:
            return -1
        elif a_alpha == False and b_alpha == True:
            return 1
    else:
        if a < b:
            return -1
        elif a > b:
            return 1
        else:
            return 0
            
def output_handler():
    
    scroller = Scroller()
    last_mouse_movement = datetime.datetime(1970, 1, 1)
    last_show_menu = False
    while True:
        try:
            global mouse_movement, launch_playlist, hotkey_map, menu_showing, last_menu_showing, playlists, playlists_index, syncing
            # -----------------------------------------
            mpd_lock.acquire()
            playlist_entries = len(mpd.playlist())
            current_song = copy.copy(mpd.currentsong())
            status = mpd.status()
            mpd_lock.release()
            # -----------------------------------------
            artist = ''
            album = ''
            pos = ''
            title = ''
            name = ''
            tfile = ''
            if 'artist' in current_song:
                artist = current_song['artist']
            if 'album' in current_song:
                album = current_song['album']
            if 'pos' in current_song:
                pos = current_song['pos']
            if 'title' in current_song:
                title = current_song['title']
            if 'name' in current_song:
                name = current_song['name']
            if 'file' in current_song:
                tfile = current_song['file']
            
            if len(current_song) > 0:
                if album == '' and artist == '':
                    scroller.set_line(0, name, tfile)
                else:
                    if artist != '':
                        if album != '':
                            scroller.set_line(0, artist + ': ' + album, tfile)
                        else:
                            scroller.set_line(0, artist, tfile)
                    
                line2 = title
                if playlist_entries > 1 and pos != '':
                    line2 = str(int(pos) + 1) + '. ' + line2
                    
                scroller.set_line(1, line2, tfile)
            else:
                scroller.clear()
            
            if 'state' in status:    
                scroller.set_paused(status['state'] == 'pause')
            scroller.set_busy(syncing)
            elapsed = ''
            if 'elapsed' in status:
                elapsed = float(status['elapsed'])
                minutes = int(elapsed // 60)
                seconds = int(elapsed - minutes * 60)
                elapsed = "%d:%02d" % (minutes, seconds)
            scroller.set_elapsed(elapsed)
                
            #scroller.set_line(0, 'ABCD (E) FGHIJKLMNOPQRSTUVWXYZ')
            #scroller.set_line(1, '-> Eule findet den Beat')
            
            mouse_movement_lock.acquire()
            current_movement = copy.copy(mouse_movement)
            mouse_movement = [0, 0]
            mouse_movement_lock.release()
            
            menu_showing_lock.acquire()
            if current_movement[1] != 0:
                last_mouse_movement = datetime.datetime.now()
            else:
                if (menu_showing != None) and (menu_showing != last_menu_showing):
                    last_mouse_movement = datetime.datetime.now()
            last_menu_showing = menu_showing
            menu_showing_lock.release()
                
            this_show_menu = ((datetime.datetime.now() - last_mouse_movement).seconds < 5)
            if last_show_menu == True and this_show_menu == False:
                menu_showing_lock.acquire()
                menu_showing = None
                menu_showing_lock.release()
                
            if last_show_menu == False and this_show_menu == True:
                mpd_lock.acquire()
                cycle_menu_showing()
                mpd_lock.release()
                current_movement = [0, 0]
                
            last_show_menu = this_show_menu

            launch_playlist_lock.acquire()
            this_launch_playlist = launch_playlist
            launch_playlist = False
            launch_playlist_lock.release()
            
            if this_show_menu:
                if current_movement[1] != 0:
                    if current_movement[0] == 1:
                        playlists_index = (playlists_index + len(playlists) + current_movement[1]) % len(playlists)
                    elif current_movement[0] == 0:
                        first_letter = playlists[playlists_index][0].lower()
                        this_first_letter = first_letter
                        # skip to another letter
                        while first_letter == this_first_letter:
                            playlists_index = (playlists_index + len(playlists) + current_movement[1]) % len(playlists)
                            first_letter = playlists[playlists_index][0].lower()
                        # skip to first entry with this letter
                        while True:
                            temp_playlists_index = (playlists_index + len(playlists) - 1) % len(playlists)
                            test_letter = playlists[temp_playlists_index][0].lower()
                            if test_letter != first_letter:
                                break
                            else:
                                playlists_index = temp_playlists_index
                    
                letters = ''.join([chr(x + 65) for x in range(26)]) + '?'
                letter_index = ord(playlists[playlists_index][0].lower()) - ord('a')
                if letter_index not in range(26):
                    letter_index = 26
                letters = letters[:letter_index] + ' [' + letters[letter_index] + '] ' + letters[(letter_index + 1):]
                letters = ' ~=] ' + letters + ' [=~'
                
                scroller.set_line(0, letters)
                line2 = playlists[playlists_index]
                menu_showing_lock.acquire()
                if menu_showing == 'artist':
                    line2 = '[Artist] ' + line2
                elif menu_showing == 'album':
                    line2 = '[Album] ' + line2
                elif menu_showing[0:13] == 'artist-album-':
                    line2 = '[Album] ' + line2
                menu_showing_lock.release()
                scroller.set_line(1, line2, line2)
                
                if this_launch_playlist:
                    menu_showing_lock.acquire()
                    previous_menu_showing = menu_showing
                    menu_showing = None
                    menu_showing_lock.release()

                    mpd_lock.acquire()
                    if previous_menu_showing == 'playlist':
                        mpd.clear()
                        mpd.load(playlists[playlists_index])
                        mpd.play()
                    elif previous_menu_showing == 'artist':
                        cycle_menu_showing('artist-album-' + playlists[playlists_index])
                        menu_showing_lock.acquire()
                        last_menu_showing = None
                        menu_showing_lock.release()
                    elif previous_menu_showing == 'album':
                        album = playlists[playlists_index]
                        mpd.clear()
                        mpd.findadd('album', album)
                        mpd.play()
                    elif previous_menu_showing[0:13] == 'artist-album-':
                        artist = previous_menu_showing[13:]
                        album = playlists[playlists_index]
                        mpd.clear()
                        if album == '(all titles)':
                            mpd.findadd('artist', artist)
                        else:
                            mpd.findadd('artist', artist, 'album', album)
                        mpd.play()
                        
                    mpd_lock.release()

                    last_mouse_movement = datetime.datetime(1970, 1, 1)
                    
            scroller.render()
            scroller.animate()
            
            #print(current_song)
        except:
            raise
            pass
        time.sleep(0.05)
            

for x in [input_handler, output_handler, sync_files]:
    t = threading.Thread(target = x)
    t.daemon = True
    t.start()
    
needs_sync.set()
    
while True:
    time.sleep(1)

