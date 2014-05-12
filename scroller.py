# -*- coding: utf-8 -*- 
import os
import random
from Adafruit_CharLCD import Adafruit_CharLCD

class Scroller:
    def __init__(self):
        random.seed()
        self.width = 40
        self.height = 2
        self.timeoutmin = 20
        self.timeoutmax = 100
        self.wait_time = 40
        self.separator = ' +++ '
        self.paused = False
        self.paused_loop = 0
        self.busy = False
        self.busy_loop = 0
        self.elapsed = ''
        
        self.lines = []
        self.offset = []
        self.tag = []
        for i in range(self.height):
            self.lines.append('')
            self.offset.append(0)
            self.tag.append('')
            
        self.ascii_art = {}
        self.load_ascii_art()
        
        # 0   - animation running
        # > 0 - animation countdown
        # -1  - animation and countdown disabled
        self.easter_egg_countdown = -1
        
        self.animation_index = self.ascii_art.keys()[random.randrange(0, len(self.ascii_art))]
        self.animation_phase = 0

        self.lcd = Adafruit_CharLCD()
        self.lcd.begin(40, 2)
        self.lcd.define_char(1, [0, 0x10, 0x08, 0x04, 0x02, 0x01, 0, 0])
        self.current_lines = ["", ""]
    
    def tr(self, s):
        result = ''.encode('latin-1')
        for c in unicode(s, 'UTF-8'):
            #print(c, ord(c))
            if ord(c) == 92:
                result += u'\x01'.encode('latin-1')
            elif ord(c) < 128:
                result += c.encode('latin-1')
            elif ord(c) == 246:
                result += u'\xef'.encode('latin-1')
            elif ord(c) == 252:
                result += u'\xf5'.encode('latin-1')
            elif ord(c) == 228:
                result += u'\xe1'.encode('latin-1')
            elif ord(c) == 223:
                result += u'\xe2'.encode('latin-1')
            elif ord(c) == 169:
                result += '(c)'.encode('latin-1')
            else:
                print(c)
                print(ord(c))
        return result
            
    def load_ascii_art(self):
        with open('ascii-art.txt') as f:
            while True:
                tag = f.readline().strip()
                if len(tag) == 0:
                    break
                self.ascii_art[tag] = []
                while True:
                    line1 = f.readline().rstrip()
                    if len(line1) == 0:
                        break
                    line2 = f.readline().rstrip()
                    line1 = self.tr(line1)
                    line2 = self.tr(line2)
                    if len(line1) > len(line2):
                        line2 += ' ' * (len(line1) - len(line2))
                    if len(line2) > len(line1):
                        line1 += ' ' * (len(line2) - len(line1))
                    self.ascii_art[tag].append(line1)
                    self.ascii_art[tag].append(line2)

    def set_line(self, i, s = '', tag = ''):
        if s == None:
            s = ''
        if tag == self.tag[i]:
            if self.offset[i] > 0:
                return
        s = self.tr(s)
        if s != self.lines[i]:
            self.lines[i] = s
            self.offset[i] = -self.wait_time
        self.tag[i] = tag
        if self.lines[0] == '' and self.lines[1] == '':
            if self.easter_egg_countdown < 0:
                self.easter_egg_countdown = random.randrange(self.timeoutmin, self.timeoutmax)
                self.animation_index = self.ascii_art.keys()[random.randrange(0, len(self.ascii_art))]
                self.animation_phase = 0
        else:
            self.easter_egg_countdown = -1
        
    def set_paused(self, paused):
        self.paused = paused
        
    def set_busy(self, busy):
        self.busy = busy
        
    def set_elapsed(self, elapsed):
        self.elapsed = elapsed
            
    def render(self):
        result_lines = []
        
        if self.easter_egg_countdown > 0:
            self.easter_egg_countdown -= 1
            
        if self.easter_egg_countdown == 0:
            # animation
            
            for i in range(2):
                offset = -len(self.ascii_art[self.animation_index][i]) + self.animation_phase
                frames = len(self.ascii_art[self.animation_index]) / 2
                part = self.ascii_art[self.animation_index][i + (2 * (self.animation_phase % frames))]
                if offset < 0:
                    part = part[-offset:]
                else:
                    part = (' ' * offset) + part
                part += ' ' * self.width
                part = part[:self.width]
                result_lines.append(part)
                if (offset > self.width):
                    self.easter_egg_countdown = random.randrange(self.timeoutmin, self.timeoutmax)
                    self.animation_index = self.ascii_art.keys()[random.randrange(0, len(self.ascii_art))]
                    self.animation_phase = 0
                    
            self.animation_phase = self.animation_phase + 1
        else:
            # print lines
            for i in range(self.height):
                line = self.lines[i]
                cropped = line
                if len(line) > self.width:
                    cropped += self.separator
                    cropped += line
                offset = self.offset[i]
                if offset < 0:
                    offset = 0
                cropped += ' ' * self.width
                cropped = cropped[offset:(offset + self.width)]
                    
                if i == 0:
                    if self.busy:
                        cropped = cropped[:-2]
                        self.busy_loop = (self.busy_loop + 1) % 4
                        cropped += ' '
                        cropped += '/-\\|'[self.busy_loop]
                if i == 1:
                    if self.paused:
                        cropped = cropped[:-3]
                        self.paused_loop = (self.paused_loop + 1) % 4
                        cropped += '['
                        cropped += '.oOo'[self.paused_loop]
                        cropped += ']'
                    #else:
                        #if self.elapsed != '':
                            #cropped = cropped[:-(len(self.elapsed) + 2)]
                            #cropped += "|%s" % self.elapsed

                result_lines.append(cropped)             
                
        #os.system("clear")
        #self.lcd.clear()
        self.lcd.setCursor(0, 0)
        for index, cropped in enumerate(result_lines):
            #if cropped != self.current_lines[index]:
                self.current_lines[index] = cropped
                self.lcd.message(cropped)
                #print(cropped)
                #print(cropped)
        #print()
        
    def animate(self):
        for i in range(self.height):
            line = self.lines[i]
            if len(line) <= self.width:
                self.offset[i] = 0
            else:
                self.offset[i] += 1
                if self.offset[i] == len(line) + len(self.separator):
                    self.offset[i] = -self.wait_time
                    
    def clear(self):
        for i in range(self.height):
            self.set_line(i, '')
