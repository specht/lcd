import os
import random

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
        
    def set_elapsed(self, elapsed):
        self.elapsed = elapsed
            
    def render(self):
        os.system("clear")
        
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
                print(part)
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
                    
                print(cropped)
                
        
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