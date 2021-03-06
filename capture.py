import pygame
import random
import operator
import os

from datetime import datetime
from glob import glob
from sys import exit
import sys

from state import *

from picturelist import *
from camera import CameraException, Camera_gPhoto as CameraModule
from logger import *

import math
from PIL import Image

from extratransforms import *

class Capture(State):

    def __init__(self, cfg, gd, w, h, fps, gpio, cam):
        self.cam = cam
        State.__init__(self, cfg, gd, w, h, fps, gpio)

        #Generate ani points
        self.cap_num = 4
        self.cap_s = 30
        self.cap_w = (w - ((self.cap_num+1) * self.cap_s)) / self.cap_num
        self.cap_h = 250
        
        self.cap_points = [ ( ((self.cap_w+self.cap_s)*i)+self.cap_s, h - self.cap_h - 10 ) for i in range (0,self.cap_num) ]
        self.gen_info()
        self.gen_instr_bars()

        #Preview Camera
        #self.preview_size = (1280,720)
        self.preview_size = (928,616)
        self.prev_c = (self.disp_w/2, self.preview_size[1]/2)
        
        self.snapshot = pygame.surface.Surface(self.preview_size, 0, self.gameDisplay)
        
        #Capture State
        self.cap_cnt = 0
        self.cap_path = ["","","",""]
        self.cap_thumbs = []
        self.cap_complete = False
   
    def schedule_capture(self):
        self.ani_q_txt_push("5", (255,255,255), 200, self.prev_cnt_c, 0.8, True)
        self.ani_q_txt_push("4", (255,255,255), 200, self.prev_cnt_c, 0.8, True)
        self.ani_q_txt_push("3", (255,255,255), 200, self.prev_cnt_c, 0.8, True)
        self.ani_q_txt_push("2", (255,255,255), 200, self.prev_cnt_c, 0.8, True)
        self.ani_q_txt_push("1", (255,255,255), 200, self.prev_cnt_c, 0, False)
        self.ani_q_cmd_push("CAPTURE")

    def gen_info(self):
        #Film Strip Background
        surf = pygame.Surface( (self.disp_w+10,self.cap_h+(4*15) ), pygame.SRCALPHA)
        surf.fill((40,40,40))
    
        #Create Film strip Holes
        y1 = 15
        y2 = surf.get_size()[1] - 2*y1 
        x = 0
        while x < surf.get_size()[0]:
            for i in range (0, y1):
                for j in range (0, y1):
                    surf.set_at( (x+j,y1+i), (255,255,255,0))
                    #surf.set_at( (x+j,y2+i), (255,255,255,0))
            x += 2*y1
        
        self.info_bar = surf
    
    def gen_instr_bars(self):
        film_h = 200
        instr_bars_txt = self.cfg.get("display__capture_instrs") 
        self.instr_bars_ang = [3,-3,3,-2]
        self.instr_bars_pos = [(-10,-50), (-10,film_h+40), (-10,2*film_h+40), (-10,3*film_h+120)]
        self.instr_bars = [] #Will be 4 objects.

        surf = pygame.Surface( (self.disp_w+10, film_h ), pygame.SRCALPHA)
        surf.fill((40,40,40))
    
        #Create Film strip Holes
        y1 = 15
        y2 = surf.get_size()[1] - 2*y1 
        x = 0
        while x < surf.get_size()[0]:
            for i in range (0, y1):
                for j in range (0, y1):
                    surf.set_at( (x+j,y1+i), (255,255,255,0))
                    surf.set_at( (x+j,y2+i), (255,255,255,0))
            x += 2*y1
        
        for txt in instr_bars_txt:
            bar = surf.copy()
            font = pygame.font.Font(self.cfg.get("display__font"), 75)
            t = font.render(txt, 1, (255,255,255))
            bar.blit( t,(50,50))
            self.instr_bars.append(bar)


    def state_cmd(self, item):
        if item['cmd'] == 'INSTRUCT':
            self.gameDisplay.fill((200,200,200))
            for idx,bar in enumerate(self.instr_bars):
                self.ani_q_img_push ( bar, self.instr_bars_pos[idx],
                                     0.5, True, 
                                     tilt=self.instr_bars_ang[idx],
                                     forceSurfaceAlpha=False )
                self.ani_q_pause_push(2)
            self.ani_q_pause_push(1)
            self.ani_q_cmd_push("CAPTURE_START")
        
        elif item['cmd'] == 'CAPTURE_START':
            self.gameDisplay.fill((200,200,200))
            self.preview_enabled = True
            self.ani_q_img_push( self.info_bar, (0, self.disp_h - self.info_bar.get_size()[1]), 0, False, True)
        
            prev_txt_c = tuple(map(operator.add, self.prev_c, (-300,-100)))
            self.ani_q_txt_push("Get Ready!", (255,255,255), 180, prev_txt_c, 1.5 , True)
        
            self.prev_cnt_c = tuple(map(operator.add, self.prev_c, (-50,-100)))
            self.schedule_capture()
            self.next()
       
        elif item['cmd'] == 'CAPTURE':
            self.cam.set_idle() #Seems to be no auto focus without this!!
            try:
                snap = self.cam.take_picture(self.cfg.get("tmp_dir") + "/photob_%02d.jpg" % self.cap_cnt)
            except:
                Logger.error(__name__,'Camera Error, Try taking lens cap off? ')
                self.stop()
                Logger.warning(__name__,'Restarting... ')
                os.execv(sys.executable, ['python'] + sys.argv)

            self.cap_path[self.cap_cnt] = snap
                
            snap_obj = pygame.image.load(snap)
            ratio = min(float(self.cap_w)/snap_obj.get_size()[0], float(self.cap_h)/snap_obj.get_size()[1])
            thumb = ( int(snap_obj.get_size()[0]*ratio), int(snap_obj.get_size()[1]*ratio) )
            snap_obj = pygame.transform.scale( snap_obj, thumb )
            
            self.ani_q_img_push(snap_obj, self.cap_points[self.cap_cnt], 0.3, True, True)

            self.cap_thumbs.append(snap_obj)
            self.cap_cnt += 1

            if self.cap_cnt < 4:
                self.schedule_capture()
            else:
                self.preview_enabled = False
                self.ani_q_pause_push(0.5)
                self.ani_q_cmd_push("COMPLETE")


    def start(self, retake=False):
        self.gpio.set('green_led', 0)
        self.gpio.set('red_led', 0)
        self.gameDisplay.fill((200,200,200))

        if retake:
            self.ani_q_cmd_push("CAPTURE_START")
        else:
            self.ani_q_cmd_push("INSTRUCT")
        self.next()

    def next(self):

        #WEBCAM UPDATE
        if self.preview_enabled:
            self.snapshot = self.cam.get_fast_preview(self.snapshot)
            self.gameDisplay.blit(self.snapshot, (int((self.disp_w - self.preview_size[0])/2), 30))

        #Special case reverse overlay and animation draw
        State.ovr_draw(self)
        State.ani_draw(self)

    def reset(self):
        State.reset(self)
        self.cap_cnt = 0
        self.cap_thumbs = []
        self.preview_enabled = False
        self.cam.end_fast_preview()
    
    def stop(self):
        self.gpio.set('green_led', 0)
        self.gpio.set('red_led', 0)
        self.cam.set_idle()
        self.cam.end_fast_preview()
