import pygame
import random
import operator
import os
import shutil

from datetime import datetime
from glob import glob
from sys import exit

from state import *
from picturelist import *

import math
#from PIL import Image
import cv2 as cv
import numpy as np

from extratransforms import *


class Process(State):

    def __init__(self, cfg, gd, w, h, fps, gpio, pic):
        State.__init__(self, cfg, gd, w, h, fps, gpio)  
        self.pictures = pic

        self.gen_processing_bar()
        self.gen_processing_menu("Upload")

        #Image Quality Config
        self.image_size = ( self.cfg.get("camera__image_size_x"), self.cfg.get("camera__image_size_y"))
        self.preview_drawn = False
        
    def gen_processing_bar(self):
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
        self.processing_bar = surf
        self.processing_bar_pos = (0,((self.disp_h-film_h)/2))
        self.processing_bar_txt_pos = (50, ((self.disp_h-film_h)/2) +20 )

    def gen_processing_menu(self ,next_str):
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
        font = pygame.font.Font(self.cfg.get("display__font"), 100)
        radius = 90
        l0 = font.render(next_str, 1, (255,255,255))
        l1 = font.render("Retake", 1, (255,255,255))
        surf.blit(l0, (150, 220))
        #Generate Gradient Button Image
        for i in [float(x)/20 for x in range(10,21)]:
           pygame.draw.circle(surf, (71*i, 211*i, 59*i), (282,425), radius)
           radius -= 2

        surf.blit(l1, (200, 650))
        #Generate Gradient Button Image
        radius = 90
        for i in [float(x)/20 for x in range(10,21)]:
           pygame.draw.circle(surf, (211*i, 71*i, 59*i), (350,850), radius)
           radius -= 2
        self.processing_menu = surf
        self.processing_menu_pos = (-50,-100)


    def state_cmd(self, item):
        if item['cmd'] == 'PROCESS':
            
            output_filename = self.pictures.get_next()
            offset =[]
            photos = []
            if self.cfg.get("image__format") == "fancy":
                
                #Create Image With Template
                if self.cfg.get("image__background"):
                    out_img = cv.imread(self.cfg.get("image__background"))
                else:
                    out_img = np.ones([self.image_size[1],self.image_size[0],3], dtype=np.uint8)*255
            
                dpi = float(self.image_size[0])/6
                dpm = int(dpi/25.4)

                lr_off = dpm*20

                new_w = int( (self.image_size[0] - (2*lr_off)) / 2 )
                new_h = int( float(new_w)/1.5 )

                thumb_size = ( new_w, new_h )

                v_space = (self.image_size[1] - (2*new_h))
                top_off = int(0.33*v_space)
                mid_off = int(0.16*v_space)
                bot_off = int(0.5 *v_space)
               
                m = int(dpm)

                offset.append( ( lr_off - m ,top_off ))
            
                offset.append( ( lr_off + new_w +m, top_off ))
                
                offset.append( ( lr_off - m , top_off + new_h + mid_off ) )

                offset.append( ( lr_off + new_w + m , top_off + new_h + mid_off ) )
                
                Logger.info(__name__, "fancy print thumb_size: {0}".format(thumb_size))
                Logger.info(__name__, "fancy print thumb coords: {0}".format(offset))

            else:
                """Assembles four pictures into a 2x2 grid

                It assumes, all original pictures have the same aspect ratio as
                the resulting image.

                For the thumbnail sizes we have:
                h = (H - 2 * a - 2 * b) / 2
                w = (W - 2 * a - 2 * b) / 2

                                            W
                       |---------------------------------------|

                  ---  +---+-------------+---+-------------+---+  ---
                   |   |                                       |   |  a
                   |   |   +-------------+   +-------------+   |  ---
                   |   |   |             |   |             |   |   |
                   |   |   |      0      |   |      1      |   |   |  h
                   |   |   |             |   |             |   |   |
                   |   |   +-------------+   +-------------+   |  ---
                 H |   |                                       |   |  2*b
                   |   |   +-------------+   +-------------+   |  ---
                   |   |   |             |   |             |   |   |
                   |   |   |      2      |   |      3      |   |   |  h
                   |   |   |             |   |             |   |   |
                   |   |   +-------------+   +-------------+   |  ---
                   |   |                                       |   |  a
                  ---  +---+-------------+---+-------------+---+  ---

                       |---|-------------|---|-------------|---|
                         a        w       2*b       w        a
                """
            
                # Thumbnail size of pictures
                outer_border = 100
                inner_border = 20
                thumb_box = ( int( self.image_size[0] / 2 ) ,
                              int( self.image_size[1] / 2 ) )
            
                thumb_size = ( thumb_box[0] - outer_border - inner_border ,
                               thumb_box[1] - outer_border - inner_border )
            
                offset.append( ( thumb_box[0] - inner_border - img.size[0] ,
                                 thumb_box[1] - inner_border - img.size[1] ))
            
                offset.append( ( thumb_box[0] + inner_border,
                                 thumb_box[1] - inner_border - img.size[1] ))
                
                offset.append( ( thumb_box[0] - inner_border - img.size[0] ,
                                 thumb_box[1] + inner_border ) )
                
                offset.append( ( thumb_box[0] + inner_border ,
                                 thumb_box[1] + inner_border ) )

            for i in range(4):
                o = offset[i] 
                img = cv.imread(self.photo_set[i])
                lar_thumb = cv.resize(img, self.image_size, interpolation=cv.INTER_AREA )
                cv.imwrite( self.photo_set[i], lar_thumb, [int(cv.IMWRITE_JPEG_QUALITY), 90]   )
                
                sma_thumb = cv.resize(lar_thumb, thumb_size, interpolation=cv.INTER_AREA )
                out_img[o[1]:o[1]+sma_thumb.shape[0], o[0]:o[0]+sma_thumb.shape[1]] = sma_thumb

                newname = output_filename.replace(".","."+str(i)+".")
                shutil.move( self.photo_set[i], newname )
                photos.append(newname)

            # Save assembled image
            cv.imwrite( output_filename, out_img, [int(cv.IMWRITE_JPEG_QUALITY), 90] )
            
            thumb_filename = output_filename.replace("/pic","/thumb.pic")
            thumb = cv.resize(out_img, ( int(self.image_size[0]/6), int(self.image_size[1]/6)),
                              interpolation=cv.INTER_AREA )
            cv.imwrite( thumb_filename, thumb, [int(cv.IMWRITE_JPEG_QUALITY), 90] )
            
            self.final_photos= {'primary': output_filename, 
                                'primary_thumb': thumb_filename, 
                                'secondary' : photos }

            self.ani_q_cmd_push("PROCESSPREVIEW")

        elif item['cmd'] == 'PROCESSPREVIEW':
            self.gpio.set('green_led', 1)
            self.gpio.set('red_led', 1)
            
            self.gameDisplay.fill((200,200,200))
            img = pygame.image.load(self.final_photos['primary'])
            ratio = 0.275
            #ratio = 0.55
            shrink = ( int(img.get_size()[0]*ratio), int(img.get_size()[1]*ratio))
            img = pygame.transform.scale(img, shrink) 
            img_pos = ((self.disp_w-img.get_size()[0])/2+180,65)

            if self.cfg.get("upload__enabled"):
                pass
            elif self.cfg.get("printer__enabled"): 
                self.gen_processing_menu("Print") #Regen with Print
            else:
                self.gen_processing_menu("Finish") #Regen with finish
            
            self.ani_q_img_push( self.processing_menu, self.processing_menu_pos, 0.1, False, True)
            self.ani_q_img_push( img, img_pos, 0.3, True, False)
            self.ani_q_cmd_push("COMPLETE")

    def start(self, photo_set, photo_set_thumbs):
        self.gpio.set('green_led', 0)
        self.gpio.set('red_led', 0)
        self.gameDisplay.fill((200,200,200))
       
        self.photo_set = photo_set
        self.photo_set_thumbs = photo_set_thumbs
        
        self.ani_q_img_push( self.processing_bar, self.processing_bar_pos, 0.1, False, False)
        self.ani_q_txt_push( "Processing....", (255,255,255), 200, self.processing_bar_txt_pos, 0.9, True)
        self.ani_q_cmd_push("PROCESS")
        self.next()

    def stop(self):
        pass

    def reset(self):
        State.reset(self)
        self.photo_set = [None,None,None,None]
        self.photo_set_thumbs = [None,None,None,None]
        self.process_complete = False
        self.final_photos = {}

    def get_result(self):
        return self.final_photos
