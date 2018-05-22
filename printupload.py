import pygame
import random
import operator
import os
import shutil

from datetime import datetime
from glob import glob
from sys import exit

import math
from PIL import Image

from extratransforms import *

from pcloud import PyCloud
import tinyurl
from multiprocessing import Process as Thread


class PrintUpload:

    def __init__(self, gd, w, h, fps, printer):

        self.pcloud_pass_file = ".pcloud_pass"
        self.pcloud_path = "/photobooth/craig_lucy_wedding_2018"

        #Generate info
        self.gameDisplay = gd
        self.disp_w = w
        self.disp_h = h
        self.printer = printer
        self.fps = fps

        self.reset()

        #Generate ani points
        self.__gen_info()
                
        img = pygame.image.load("upload_white.png")
        ratio = 0.40
        shrink = ( int(img.get_size()[0]*ratio), int(img.get_size()[1]*ratio))
        self.upload_img = pygame.transform.scale(img, shrink) 

        #Image Quality Config
        self.image_size = (2352, 1568)
        
        self.preview_size = (1600,896)
        self.prev_c = (self.disp_w/2, self.preview_size[1]/2)
        self.preview_drawn = False

        print "pCloud Login.."
        self.__pcloud_login()
        print "...Success"
        self.pcloud_upload_folder = self.__pcloud_get_uploadfolderid(self.pcloud_path)
        print "pcloud folderid: {0}".format(self.pcloud_upload_folder)
        


    def __pcloud_login( self ):
        f = open(self.pcloud_pass_file, 'r')
        usr = f.readline().rstrip()
        psswd = f.readline().rstrip()
        self.pCloud = PyCloud(usr,psswd)

    def __pcloud_get_uploadfolderid( self, pPath):
        folder_split = filter(None,pPath.split("/"))
        folder_walk = [0]
        for idx,i  in enumerate(folder_split):
            resp = self.pCloud.listfolder(folderid=folder_walk[-1])
            dir_list = resp['metadata']['contents']
            match = False
            for j in dir_list:
                if j['name'] == i and j['isfolder']:
                    folder_walk.append(j['folderid'])
                    match = True
                    break
            if not match: raise Exception("pCloud folder walk: Could not find \"{0}\"".format(i))
        return folder_walk[-1]

    #def __pcloud_uploadfile( self, f ):
    #    resp = self.pCloud.uploadfile(files=[f],folrderid=self.pcloud_upload_folder)
    #    llink = self.pCloud.getfilepublink(fileid=resp['fileids'][0])['link']
    #    slink = self.__get_tinyurl(llink)
    #    return slink
    def __pcloud_uploadfile(self, pc, fid, f, slink ):
        resp = pc.uploadfile(files=[f],folderid=fid)
        llink = pc.getfilepublink(fileid=resp['fileids'][0])['link']
        slink = tinyurl.shorten(llink,"")
    

    def __pcloud_test_conn(self):
        #TODO
        return True

    def __get_tinyurl(self, url):
        return tinyurl.shorten(url, "")

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
            if item['cmd'] == 'UPLOAD':
                if self.pcloud_upload is None: #No Upload, Start one
                    self.upload_link = ""
                    print "pCloud Starting Upload"
                    self.pcloud_upload = Thread(target=self.__pcloud_uploadfile, args=(self.pCloud, self.pcloud_upload_folder,"upload_white.png", self.upload_link))
                    self.pcloud_upload.start()
                    self.__ani_q_img_push( self.upload_img, self.upload_bar_img_pos, 0.5, True)
                    self.__ani_q_img_push( self.upload_bar, self.upload_bar_pos , 0.1, False)
                    self.__ani_q_txt_push( "Uploading....", (255,255,255), 200,self.upload_bar_txt_pos , 0.1, False)
                    self.__ani_q_cmd_push("UPLOAD")
                else:
                    if self.pcloud_upload.is_alive():
                        self.__ani_q_img_push( self.upload_img, self.upload_bar_img_pos, 0.5, True)
                        self.__ani_q_img_push( self.upload_bar, self.upload_bar_pos , 0.1, False)
                        self.__ani_q_txt_push( "Uploading....", (255,255,255), 200,self.upload_bar_txt_pos , 0.1, False)
                        self.__ani_q_cmd_push("UPLOAD")
                    else:
                        print "pCloud Upload Complete"
                        print self.upload_link
                        self.upload_complete = True
            elif item['cmd'] == "PRINT":
            
                self.print_complete = True
            elif item['cmd'] == "NOP":
                pass
            elif item['cmd'] == "COMPLETE":
                pass


    def __ani_q_pop(self):
        if len(self.ani_q) > 0:
            item = self.ani_q.pop(0)
            self.__handle_q_item(item)

    def start(self, photo_set, upload_en, print_en):
        self.upload_complete = False
        self.print_complete = False
        self.gameDisplay.fill((200,200,200))
        
        self.photo_set = photo_set
        
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

        self.upload_bar = surf
        self.upload_bar_pos = (0,((self.disp_h-film_h)/2))
        self.upload_bar_txt_pos = (50, ((self.disp_h-film_h)/2) +20 )
        self.upload_bar_img_pos = (1200,(self.disp_h-film_h)/2)
        self.__ani_q_img_push( self.upload_bar, self.upload_bar_pos , 0.1, False, False)
        self.__ani_q_txt_push( "Uploading....", (255,255,255), 200,self.upload_bar_txt_pos , 0.1, False)
        self.__ani_q_cmd_push("UPLOAD")
        self.next()

    def stop(self):
        pass

    def next(self):
        
        #ANNIMATION DRAW
        if len(self.ani_q) > 0 :
            self.__ani_q_pop()

        #OVERLAY DRAW
        if len(self.overlay_buffer) >0:
            for item in self.overlay_buffer:
                item['overlay'] = False
                self.__handle_q_item(item)
        

    def reset(self):
        self.pcloud_upload = None
        self.photo_set = []
        self.upload_complete = False
        self.print_complete = False
        self.ani_q = []
        self.overlay_buffer = []

    def is_done(self):
        return self.upload_complete and self.print_complete
