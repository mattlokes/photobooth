import pygame
import pygame.camera
import random
import operator
import os

from datetime import datetime
from glob import glob
from sys import exit

from picturelist import *
from camera import CameraException, Camera_gPhoto as CameraModule

import math
from PIL import Image

from extratransforms import *


pygame.camera.init()

class Capture:

    def __init__(self, gd, w, h, cam, fps):
        #Generate info
        self.gameDisplay = gd
        self.disp_w = w
        self.disp_h = h
        self.cam = cam
        self.fps = fps
        
        
        

        #Initialize ani_q
        self.ani_q = []
        self.overlay_buffer = []

        #Generate ani points
        self.cap_num = 4
        self.cap_s = 30
        self.cap_w = (w - ((self.cap_num+1) * self.cap_s)) / self.cap_num
        self.cap_h = 250
        
        self.cap_points = [ ( ((self.cap_w+self.cap_s)*i)+self.cap_s, h - self.cap_h - 10 ) for i in range (0,self.cap_num) ]
        print self.cap_points
        self.__gen_info()

        #Preview Camera
        #self.preview_size = (640,480)
        self.preview_size = (1280,720)
        #self.preview_size = (1600,896)
        
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
    
    def __gen_info(self):
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
        
        #Create Info Text
        #font = pygame.font.Font("springtime_in_april.ttf", 100)
        #radius = 90
        #l0 = font.render("Press", 1, (255,255,255))
        #l1 = font.render("To Begin!", 1, (255,255,255))
        #surf.blit(l0, (150, 300))
        #Generate Gradient Button Image
        #for i in [float(x)/20 for x in range(10,21)]:
        #   pygame.draw.circle(surf, (71*i, 211*i, 59*i), (282,505), radius)
        #   radius -= 2
        #surf.blit(l1, (175, 600))
        self.info_bar = surf


    def __ani_q_img_push(self, obj, xy, secs, fadeIn=False, overlay=False):
        alpha = 255 * (not fadeIn)
        for _ in range( int(math.ceil(secs*self.fps)) ):
            alpha += ( 255.0/(secs*self.fps) ) * fadeIn
            self.ani_q.append( {'type' : 'IMG',
                                'obj' : obj, 
                                'alpha' : int(alpha), 
                                'xy' : xy, 
                                'tilt': 0,
                                'scale': 1,
                                'overlay': False} )
        if overlay:
            self.ani_q.append( {'type' : 'IMG',
                                'obj' : obj, 
                                'alpha' : int(alpha), 
                                'xy' : xy, 
                                'tilt': 0,
                                'scale': 1,
                                'overlay': True} )
    
    def __ani_q_txt_push(self, txt, col, size, xy, secs, fadeIn=False, overlay=False):
        font = pygame.font.Font("springtime_in_april.ttf", size)
        alpha = 255 * (not fadeIn)
        for _ in range( int(math.ceil(secs*self.fps)) ):
            alpha += ( 255.0/(secs*self.fps) ) * fadeIn
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
    
    def __ani_q_cmd_push(self, cmd ):
        self.ani_q.append( {'type' : 'CMD',
                            'cmd': cmd } )


    def __handle_q_item(self, item):
        if item['type'] == 'IMG':
            xy = item['xy']
            t = item['tilt']
            s = item['scale']
            img = item['obj']
            img.set_alpha(item['alpha'])
            self.gameDisplay.blit(img, xy)

            if item['overlay']:
                self.overlay_buffer.append(item)

        elif item['type'] == 'TXT':
            self.gameDisplay.blit(item['txt'], item['xy'] )
            if item['overlay']:
                self.overlay_buffer.append(item)

        elif item['type'] == 'CMD':
            if item['cmd'] == 'CAPTURE':
                
                snap = self.cam.take_picture("/tmp/photob_%02d.jpg" % self.cap_cnt)
                self.cap_path[self.cap_cnt] = snap
                
                snap_obj = pygame.image.load(snap)
                ratio = min(float(self.cap_w)/snap_obj.get_size()[0], float(self.cap_h)/snap_obj.get_size()[1])
                thumb = ( int(snap_obj.get_size()[0]*ratio), int(snap_obj.get_size()[1]*ratio) )
                snap_obj = pygame.transform.scale( snap_obj, thumb )
                self.__ani_q_img_push(snap_obj, self.cap_points[self.cap_cnt], 0.3, True, True)

                self.cap_thumbs.append(snap_obj)
                self.cap_cnt += 1

            elif item['cmd'] == "NOP":
                pass
            elif item['cmd'] == "COMPLETE":
                self.cap_complete = True


    def __ani_q_pop(self):
        if len(self.ani_q) > 0:
            item = self.ani_q.pop(0)
            self.__handle_q_item(item)

    def start(self):
        self.gameDisplay.fill((200,200,200))
        self.__ani_q_img_push( self.info_bar, (0, self.disp_h - self.info_bar.get_size()[1]), 0, False, True)
        for _ in range( 3*self.fps ):
            self.__ani_q_cmd_push("NOP")
        self.next()

    def stop(self):
        pass

    def next(self):

        #CAPTURE SCHEDULE
        if   self.cap_cnt == 0 and len(self.ani_q) == 0:
            self.prev_cnt_c = tuple(map(operator.add, self.prev_c, (-50,-100)))
            self.__ani_q_txt_push("3", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("2", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("1", (255,255,255), 200, self.prev_cnt_c, 0.5)
            self.__ani_q_cmd_push("CAPTURE")
        elif self.cap_cnt == 1 and len(self.ani_q) == 0:
            self.__ani_q_txt_push("3", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("2", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("1", (255,255,255), 200, self.prev_cnt_c, 0.5)
            self.__ani_q_cmd_push("CAPTURE")
        elif self.cap_cnt == 2 and len(self.ani_q) == 0:
            self.__ani_q_txt_push("3", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("2", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("1", (255,255,255), 200, self.prev_cnt_c, 0.5)
            self.__ani_q_cmd_push("CAPTURE")
        elif self.cap_cnt == 3 and len(self.ani_q) == 0:
            self.__ani_q_txt_push("3", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("2", (255,255,255), 200, self.prev_cnt_c, 1)
            self.__ani_q_txt_push("1", (255,255,255), 200, self.prev_cnt_c, 0.5)
            self.__ani_q_cmd_push("CAPTURE")
        elif self.cap_cnt == 4 and len(self.ani_q) == 0:
            for _ in range( int(0.5*self.fps) ):
                self.__ani_q_cmd_push("NOP")
            self.__ani_q_cmd_push("COMPLETE")

        #WEBCAM UPDATE
        if self.precam.query_image():
            self.snapshot = self.precam.get_image(self.snapshot)
            self.snapshot = pygame.transform.flip( self.snapshot, False, True)
            # blit it to the display surface.  simple!
            self.gameDisplay.blit(self.snapshot, (int((self.disp_w - self.preview_size[0])/2), 0))
        

        #OVERLAY DRAW
        if len(self.overlay_buffer) >0:
            for item in self.overlay_buffer:
                item['overlay'] = False
                self.__handle_q_item(item)
        
        #ANNIMATION DRAW
        if len(self.ani_q) > 0 :
            self.__ani_q_pop()

    def reset(self):
        self.cap_cnt = 0
        self.cap_thumbs = []
        self.cap_complete = False
        self.ani_q = []
        self.overlay_buffer = []

    def is_done(self):
        return self.cap_complete
