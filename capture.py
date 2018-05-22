import pygame
import pygame.camera
import random
import operator
import os

from datetime import datetime
from glob import glob
from sys import exit

from state import *

from picturelist import *
from camera import CameraException, Camera_gPhoto as CameraModule

import math
from PIL import Image

from extratransforms import *


pygame.camera.init()

class Capture(State):

    def __init__(self, gd, w, h, fps, cam):
        State.__init__(self, gd, w, h, fps)
        self.cam = cam

        #Generate ani points
        self.cap_num = 4
        self.cap_s = 30
        self.cap_w = (w - ((self.cap_num+1) * self.cap_s)) / self.cap_num
        self.cap_h = 250
        
        self.cap_points = [ ( ((self.cap_w+self.cap_s)*i)+self.cap_s, h - self.cap_h - 10 ) for i in range (0,self.cap_num) ]
        self.gen_info()

        #Preview Camera
        self.preview_size = (1280,720)
        self.prev_c = (self.disp_w/2, self.preview_size[1]/2)
        

        self.clist = pygame.camera.list_cameras()
        if not self.clist:
            raise ValueError("Sorry, no preview cameras detected.")
        self.precam = pygame.camera.Camera(self.clist[0], self.preview_size)
        self.precam.start()

        self.snapshot = pygame.surface.Surface(self.preview_size, 0, self.gameDisplay)
        
        #Capture State
        self.cap_cnt = 0
        self.cap_path = ["","","",""]
        self.cap_thumbs = []
        self.cap_complete = False
   
    def schedule_capture(self):
        self.ani_q_txt_push("3", (255,255,255), 200, self.prev_cnt_c, 1, True)
        self.ani_q_txt_push("2", (255,255,255), 200, self.prev_cnt_c, 1, True)
        self.ani_q_txt_push("1", (255,255,255), 200, self.prev_cnt_c, 0.5, True)
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

    def state_cmd(self, item):
       
        if item['cmd'] == 'CAPTURE':
            snap = self.cam.take_picture("/tmp/photob_%02d.jpg" % self.cap_cnt)
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
                self.ani_q_pause_push(0.5)
                self.ani_q_cmd_push("COMPLETE")


    def start(self):
        self.gameDisplay.fill((200,200,200))
        self.ani_q_img_push( self.info_bar, (0, self.disp_h - self.info_bar.get_size()[1]), 0, False, True)
        
        self.ani_q_pause_push(3)
        
        self.prev_cnt_c = tuple(map(operator.add, self.prev_c, (-50,-100)))
        self.schedule_capture()
        self.next()

    def next(self):

        #WEBCAM UPDATE
        if self.precam.query_image():
            self.snapshot = self.precam.get_image(self.snapshot)
            self.snapshot = pygame.transform.flip( self.snapshot, False, True)
            # blit it to the display surface.  simple!
            self.gameDisplay.blit(self.snapshot, (int((self.disp_w - self.preview_size[0])/2), 0))
        
        #Special case reverse overlay and animation draw
        State.ovr_draw(self)
        State.ani_draw(self)

    def reset(self):
        State.reset(self)
        self.cap_cnt = 0
        self.cap_thumbs = []
