import pygame
import random
import operator
import os
import shutil

from datetime import datetime
from glob import glob
from sys import exit

from picturelist import *

import math
from PIL import Image

from extratransforms import *


class Process:

    def __init__(self, gd, w, h, pic, fps):
        #Generate info
        self.gameDisplay = gd
        self.disp_w = w
        self.disp_h = h
        self.pictures = pic
        self.fps = fps

        #Initialize ani_q
        self.ani_q = []
        self.overlay_buffer = []

        #Generate ani points
        #self.cap_num = 4
        #self.cap_s = 30
        #self.cap_w = (w - ((self.cap_num+1) * self.cap_s)) / self.cap_num
        #self.cap_h = 250
        
        #self.cap_points = [ ( ((self.cap_w+self.cap_s)*i)+self.cap_s, h - self.cap_h - 10 ) for i in range (0,self.cap_num) ]
        self.__gen_info()

        #Image Quality Config
        self.image_size = (2352, 1568)
        
        
        self.preview_size = (1600,896)
        self.prev_c = (self.disp_w/2, self.preview_size[1]/2)
        self.preview_drawn = False
        
        #self.snapshot = pygame.surface.Surface(self.preview_size, 0, self.gameDisplay)
        
        #Process State
        self.photo_set = [None,None,None,None]
        self.photo_set_thumbs = [None,None,None,None]
        self.process_complete = False
    
    def __gen_info(self):
        pass
        #Film Strip Background
        #surf = pygame.Surface( (self.disp_w+10,self.cap_h+(4*15) ), pygame.SRCALPHA)
        #surf.fill((40,40,40))
    
        #Create Film strip Holes
        #y1 = 15
        #y2 = surf.get_size()[1] - 2*y1 
        #x = 0
        #while x < surf.get_size()[0]:
        #    for i in range (0, y1):
        #        for j in range (0, y1):
        #            surf.set_at( (x+j,y1+i), (255,255,255,0))
                    #surf.set_at( (x+j,y2+i), (255,255,255,0))
        #    x += 2*y1
        
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
        #self.info_bar = surf


    def __ani_q_img_push(self, obj, xy, secs, fadeIn=False, overlay=False):
        alpha = 255 * (not fadeIn)
        num = int(math.ceil(secs*self.fps)) if fadeIn else 1
        for _ in range( num ):
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
        num = int(math.ceil(secs*self.fps)) if fadeIn else 1
        for _ in range( num ):
            alpha += ( 255.0/(secs*self.fps) ) * fadeIn
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
            if item['cmd'] == 'PROCESS':
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
                outer_border = 50
                inner_border = 20
                thumb_box = ( int( self.image_size[0] / 2 ) ,
                              int( self.image_size[1] / 2 ) )
                thumb_size = ( thumb_box[0] - outer_border - inner_border ,
                               thumb_box[1] - outer_border - inner_border )

                # Create output image with white background
                output_image = Image.new('RGB', self.image_size, (255, 255, 255))
                #Create Image With Template
                #TODO TODO TODO

                # Image 0
                img = Image.open(self.photo_set[0])
                img.thumbnail(thumb_size)
                offset = ( thumb_box[0] - inner_border - img.size[0] ,
                           thumb_box[1] - inner_border - img.size[1] )
                output_image.paste(img, offset)

                # Image 1
                img = Image.open(self.photo_set[1])
                img.thumbnail(thumb_size)
                offset = ( thumb_box[0] + inner_border,
                           thumb_box[1] - inner_border - img.size[1] )
                output_image.paste(img, offset)

                # Image 2
                img = Image.open(self.photo_set[2])
                img.thumbnail(thumb_size)
                offset = ( thumb_box[0] - inner_border - img.size[0] ,
                           thumb_box[1] + inner_border )
                output_image.paste(img, offset)

                # Image 3
                img = Image.open(self.photo_set[3])
                img.thumbnail(thumb_size)
                offset = ( thumb_box[0] + inner_border ,
                           thumb_box[1] + inner_border )
                output_image.paste(img, offset)

                # Save assembled image
                output_filename = self.pictures.get_next()
                output_image.save(output_filename, "JPEG")
                self.final_photos= [output_filename]
                #Save files that make up assembled
                for i,photo in enumerate(self.photo_set):
                    newname = output_filename.replace(".","."+str(i)+".")
                    shutil.copy2( photo, newname )
                    self.final_photos.append(newname)
                self.__ani_q_cmd_push("COMPLETE")
            
            elif item['cmd'] == "NOP":
                pass
            elif item['cmd'] == "COMPLETE":
                self.process_complete = True


    def __ani_q_pop(self):
        if len(self.ani_q) > 0:
            item = self.ani_q.pop(0)
            self.__handle_q_item(item)

    def start(self, photo_set, photo_set_thumbs):
        self.gameDisplay.fill((200,200,200))
        #self.__ani_q_img_push( self.info_bar, (0, self.disp_h - self.info_bar.get_size()[1]), 0, False, True)
       
        self.photo_set = photo_set
        self.photo_set_thumbs = photo_set_thumbs
        
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

        self.__ani_q_img_push( surf, (0,((self.disp_h-film_h)/2)), 0.1, False, False)
        self.__ani_q_txt_push( "Processing....", (255,255,255), 200, (50, ((self.disp_h-film_h)/2) +20 ), 0.9, True)
        self.__ani_q_cmd_push("PROCESS")
        self.next()

    def stop(self):
        pass

    def next(self):

        if self.process_complete and not self.preview_drawn: 
            self.gameDisplay.fill((200,200,200))
            img = pygame.image.load(self.final_photos[0])
            ratio = 0.55
            shrink = ( int(img.get_size()[0]*ratio), int(img.get_size()[1]*ratio))
            img = pygame.transform.scale(img, shrink) 

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
            l0 = font.render("Print", 1, (255,255,255))
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
            
            self.__ani_q_img_push( surf, (-50,-100), 0.1, False, True)
            self.__ani_q_img_push( img, ((self.disp_w-img.get_size()[0])/2+180,65), 0.3, True)

            self.preview_drawn = True
        
        #ANNIMATION DRAW
        if len(self.ani_q) > 0 :
            self.__ani_q_pop()

        #OVERLAY DRAW
        if len(self.overlay_buffer) >0:
            for item in self.overlay_buffer:
                item['overlay'] = False
                self.__handle_q_item(item)
        

    def reset(self):
        self.photo_set = None
        self.photo_set_thumbs = None
        self.final_photos = []
        self.process_complete = False
        self.preview_drawn = False
        self.ani_q = []
        self.overlay_buffer = []

    def is_done(self):
        return self.process_complete

    def get_result(self):
        if self.process_complete:
            return self.final_photos
        else:
            return None
