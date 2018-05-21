import pygame
import random
import operator
import os

from datetime import datetime
from glob import glob
from sys import exit

from picturelist import *

from extratransforms import *

class IntroAnimation:

    def __init__(self, gd, w, h, pl):
        self.gameDisplay = gd
        self.disp_w = w
        self.disp_h = h 
        self.pictures = pl

        #Initialize ani_q
        self.ani_q = []

        #Generate ani points
        pnt_s = 5
        self.ani_points = [ ( (w/pnt_s)*(i%pnt_s)-50, (h/pnt_s)*(i/pnt_s)-50 ) for i in range (0,pnt_s**2) ]

        #Generate intro info
        self.__gen_intro_info()

    def __gen_intro_info(self):
        #Film Strip Background
        surf = pygame.Surface( (400,self.disp_h+200), pygame.SRCALPHA)
        surf.fill((40,40,40))
    
        #Create Film strip Holes
        x1 = 15
        x2 = surf.get_rect().size[0] - 2*x1 
        y = 0
        while y < surf.get_rect().size[1]:
            for i in range (0, x1):
                for j in range (0, x1):
                    surf.set_at( (x1+j,y+i), (255,255,255,0))
                    surf.set_at( (x2+j,y+i), (255,255,255,0))
            y += 2*x1
        
        #Rotate Film Strip
        surf = pygame.transform.rotozoom(surf, 10, 1)
        
        #Create Info Text
        font = pygame.font.Font("springtime_in_april.ttf", 100)
        radius = 90
        l0 = font.render("Press", 1, (255,255,255))
        l1 = font.render("To Begin!", 1, (255,255,255))
        surf.blit(l0, (150, 300))
        #Generate Gradient Button Image
        for i in [float(x)/20 for x in range(10,21)]:
           pygame.draw.circle(surf, (71*i, 211*i, 59*i), (282,505), radius)
           radius -= 2
        surf.blit(l1, (175, 600))
        self.intro_info = surf

    def __ani_q_rand_push(self):
        rand_xy = self.ani_points[random.randint(0, len(self.ani_points)-1)]
        rand_tilt = random.randint(-30,30)
        photo_list = self.pictures.get_list()
        rand_path = photo_list[random.randint(0, len(photo_list)-1)]
        self.ani_q.append( {'path' : rand_path, 
                            'alpha' : 0, 
                            'xy' : rand_xy, 
                            'tilt': rand_tilt,
                            'scale': 0.3})

    def __ani_q_pop(self):
        if len(self.ani_q) > 0:
            item = self.ani_q.pop(0)
            xy = item['xy']
            t = item['tilt']
            s = item['scale']
            img = pygame.image.load(item['path']).convert_alpha()
            shadow = pygame.Surface( tuple(map(operator.add, img.get_rect().size, (14,14))) , pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 70))

            img = ExtraTransforms.aa_rotozoom(img,t, s)
            shadow = ExtraTransforms.aa_rotozoom(shadow,t, s)
            item['alpha'] += 2
            img_cpy = ExtraTransforms.set_alpha( img.copy(), item['alpha'] )
            self.gameDisplay.blit(shadow, tuple(map(operator.add, xy, (4,4))) )
            self.gameDisplay.blit(img_cpy, xy)
            self.gameDisplay.blit(self.intro_info, (0,-100))
            
            self.c_ani_q_item = item
            self.c_ani_img = img
            self.c_ani_img_xy = xy

    def __ani_draw_next(self):
        img = ExtraTransforms.set_alpha( self.c_ani_img.copy(), self.c_ani_q_item['alpha'] )
        self.gameDisplay.blit(img, self.c_ani_img_xy)
        self.gameDisplay.blit(self.intro_info, (0,-100))
        self.c_ani_q_item['alpha'] += 2
        if self.c_ani_q_item['alpha'] >= 60:
            self.c_ani_q_item = None

    def start(self):
        self.gameDisplay.fill((200,200,200))
        self.c_ani_q_item = None
        self.next()

    def stop(self):
        pass

    def next(self):
        if self.c_ani_q_item == None and len(self.ani_q) > 0 :
            self.__ani_q_pop()
        elif self.c_ani_q_item != None:
            self.__ani_draw_next()
        else:
            self.__ani_q_rand_push()
