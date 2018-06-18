import pygame
import operator

import math
from PIL import Image

from extratransforms import *


class State:

    def __init__(self, cfg, gd, w, h, fps, gpio):
        self.cfg = cfg
        self.gameDisplay = gd
        self.disp_w = w
        self.disp_h = h
        self.fps = fps
        self.gpio = gpio

        self.reset()

    def ani_q_img_push(self, obj, xy, secs, fadeIn=False, overlay=False, forceSurfaceAlpha=True, tilt=0):
        alpha = 0 if fadeIn else 255
        num = int(math.ceil(secs*self.fps)) if fadeIn else 1
        for _ in range( num ):
            alpha += ( 255.0/(secs*self.fps) ) if fadeIn else 0
            alpha = min(255, alpha)
            self.ani_q.append( {'type' : 'IMG',
                                'obj' : obj, 
                                'alpha' : int(alpha), 
                                'xy' : xy, 
                                'tilt': tilt,
                                'scale': 1,
                                'overlay': False,
                                'fsa': forceSurfaceAlpha} )
        if overlay:
            self.ani_q.append( {'type' : 'IMG',
                                'obj' : obj, 
                                'alpha' : int(alpha), 
                                'xy' : xy, 
                                'tilt': tilt,
                                'scale': 1,
                                'overlay': True,
                                'fsa':forceSurfaceAlpha } )
    
    def ani_q_txt_push(self, txt, col, size, xy, secs, fadeIn=False, overlay=False):
        font = pygame.font.Font(self.cfg.get("display__font"), size)
        alpha = 0 if fadeIn else 255
        num = int(math.ceil(secs*self.fps)) if fadeIn else 1
        for _ in range( num ):
            alpha += ( 255.0/(secs*self.fps) ) if fadeIn else 0
            alpha = min(255, alpha)
            t = font.render(txt, 1, (col[0], col[1], col[2], int(alpha)))
            self.ani_q.append( {'type' : 'TXT',
                                'txt' : t,
                                'xy' : xy, 
                                'tilt': 0,
                                'scale': 1,
                                'overlay':False} )
        if overlay:
            t = font.render(txt, 1, (col[0], col[1], col[2], int(alpha)))
            self.ani_q.append( {'type' : 'TXT',
                                'txt' : t,
                                'xy' : xy, 
                                'tilt': 0,
                                'scale': 1,
                                'overlay':True} )
    
    def ani_q_cmd_push(self, cmd ):
        self.ani_q.append( {'type' : 'CMD',
                            'cmd': cmd } )

    def ani_q_pause_push(self, sec):
        for _ in range( int(sec*self.fps) ):
            self.ani_q_cmd_push("NOP")


    def handle_q_item(self, item):
        if item['type'] == 'IMG':
            xy = item['xy']
            t = item['tilt']
            s = item['scale']
            img = item['obj']

            if img.get_flags() & 0x00010000 and not item['fsa']: #Per Pixel Alpha
                dimg = ExtraTransforms.set_alpha( img.copy(), item['alpha'] )
            else:
                dimg = img
                dimg.set_alpha(item['alpha'])

            if t:
                dimg = pygame.transform.rotozoom(dimg, t, 1)

            self.gameDisplay.blit(dimg, xy)

            if item['overlay']:
                self.overlay_buffer.append(item)

        elif item['type'] == 'TXT':
            self.gameDisplay.blit(item['txt'], item['xy'] )
            if item['overlay']:
                self.overlay_buffer.append(item)

        elif item['type'] == 'CMD':
            if item['cmd'] == 'NOP':
                pass
            elif item['cmd'] == 'COMPLETE':
                self.state_complete = True
            else:
                self.state_cmd(item)

    def ani_q_pop(self):
        if len(self.ani_q) > 0:
            item = self.ani_q.pop(0)
            self.handle_q_item(item)

    def state_cmd(self, item):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def ani_draw(self):
        if len(self.ani_q) > 0 :
            self.ani_q_pop()
        
    def ovr_draw(self):
        if len(self.overlay_buffer) >0:
            for item in self.overlay_buffer:
                item['overlay'] = False
                self.handle_q_item(item)

    def next(self):
        #ANNIMATION DRAW / HANDLE CMD
        self.ani_draw()
        #OVERLAY DRAW
        self.ovr_draw()
        

    def reset(self):
        self.ani_q = []
        self.overlay_buffer = []
        self.state_complete = False
        self.gpio.set("green_led", 0)
        self.gpio.set("red_led", 0)

    def is_done(self):
        return self.state_complete
