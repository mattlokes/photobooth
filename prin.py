import pygame
import random
import operator
import os
import shutil

from datetime import datetime
from glob import glob
from sys import exit
from time import sleep

import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from state import *
from logger import *

from pcloud import PyCloud
import tinyurl
import qrcode
from multiprocessing import Process as Thread
from multiprocessing import Queue


class Prin(State):

    def __init__(self, cfg, gd, w, h, fps, gpio, printer):
        State.__init__(self, cfg, gd, w, h, fps, gpio)
        self.printer = printer

        self.gen_print_bar()
        
    def gen_print_bar(self):
        img = pygame.image.load(self.cfg.get("display__print_icon"))
        ratio = 0.35
        shrink = ( int(img.get_size()[0]*ratio), int(img.get_size()[1]*ratio))
        self.print_img = pygame.transform.scale(img, shrink) 

        film_h = 300
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

        self.print_bar = surf
        self.print_bar_pos = (0,((self.disp_h-film_h)/2))
        self.print_bar_txt_pos = (50, ((self.disp_h-film_h)/2) +20 )
        self.print_bar_img_pos = (1200,((self.disp_h-film_h)/2)+55)
    
    def print_file(self, printer, f, l, ret_q ):
        tmp_img = self.cfg.get("tmp_dir") + '/print_img.jpg'
        img = Image.open(f)
        img.thumbnail(( 2076,1384), Image.ANTIALIAS) #shrink to printer resolution

        if self.cfg.get("printer__link_embed"):
            font = ImageFont.truetype(self.cfg.get("printer__link_font"), 
                                      self.cfg.get("printer__link_size"))
            dr = ImageDraw.Draw(img)
            dr.text( ( self.cfg.get("printer__link_pos_x"), self.cfg.get("printer__link_pos_y")),
                    "Download: " + l, (0,0,0),font=font)
            
        img.save(tmp_img, "JPEG", quality=80 )
        fi = tmp_img

        for _ in range(self.cfg.get("printer__copies")):
            printer.print_image(fi)
        
        sleep(self.cfg.get("printer__wait_time"))
        ret_q.put("Done")
        return
    
    def start(self, photo_set, link ):
        self.gpio.set('green_led', 0)
        self.gpio.set('red_led', 0)
        self.gameDisplay.fill((200,200,200))
        
        self.photo_set = photo_set
        self.link = link
        
        self.ani_q_img_push( self.print_bar, self.print_bar_pos , 0.1, False, False)
        self.ani_q_txt_push( "Printing....", (255,255,255), 200,self.print_bar_txt_pos , 0.1, False)
        self.ani_q_cmd_push("PRINT")
        self.next()
    
    def state_cmd(self, item ):
        if item['cmd'] == 'PRINT':
           self.print_q = Queue()
           self.print_t = Thread(target=self.print_file,\
                                       args=( self.printer,\
                                              self.photo_set['primary'],\
                                              self.link,\
                                              self.print_q ))
           self.print_t.start()
           self.ani_q_cmd_push("PRINTWAIT")

        elif item['cmd'] == 'PRINTWAIT':
            if self.print_t.is_alive(): #While Printing Continue animation
                self.ani_q_img_push( self.print_img, self.print_bar_img_pos, 0.9, True,False,False)
                self.ani_q_img_push( self.print_bar, self.print_bar_pos , 0.1, False)
                self.ani_q_txt_push( "Printing....", (255,255,255), 200,self.print_bar_txt_pos , 0.1, False)
                self.ani_q_cmd_push("PRINTWAIT")
            else:
                self.status = self.print_q.get()
                Logger.info(__name__, "Print Complete with status .. {0}".format(self.status))
                self.ani_q_cmd_push("COMPLETE")


    def reset(self):
        State.reset(self)
        self.photo_set = {}
        self.print_t = None
        self.link = ""
        self.status = ""
