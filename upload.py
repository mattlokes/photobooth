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

from state import *

from pcloud import PyCloud
import tinyurl
import qrcode
from multiprocessing import Process as Thread
from multiprocessing import Queue


class Upload(State):

    def __init__(self, gd, w, h, fps, gpio):
        State.__init__(self, gd, w, h, fps, gpio)
        self.pcloud_pass_file = ".pcloud_pass"
        self.pcloud_path = "/photobooth/craig_lucy_wedding_2018"

        self.gen_upload_bar()
        self.gen_upload_menu()
        self.gen_upload_info()

        print "pCloud Login.."
        self.pcloud_login()
        print "...Success"
        self.pcloud_upload_folder = self.pcloud_get_uploadfolderid(self.pcloud_path)
        print "pcloud folderid: {0}".format(self.pcloud_upload_folder)
        
    def pcloud_login( self ):
        f = open(self.pcloud_pass_file, 'r')
        usr = f.readline().rstrip()
        psswd = f.readline().rstrip()
        self.pCloud = PyCloud(usr,psswd)

    def pcloud_get_uploadfolderid( self, pPath):
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

    def pcloud_uploadfiles(self, pc, fid, f, ret_q ):
        slinks = []
        for i in f:
            retrycnt = 3
            while( retrycnt > 0):
                try:
                    resp = pc.uploadfile(files=[i],folderid=fid)
                    ll = pc.getfilepublink(fileid=resp['fileids'][0])['link']
                    sl = tinyurl.shorten(ll,"")
                    slinks.append(sl)
                    break
                except:
                    print "pCloud Error, retrying login"
                    self.pcloud_login()
                    retrycnt -= 1
            if retrycnt == 0: #Failed Retries
                ret_q.put(None)
                return
        ret_q.put(slinks[0])
        return

    def pcloud_test_conn(self):
        #TODO
        return True

    def get_tinyurl(self, url):
        return tinyurl.shorten(url, "")
    
    def gen_upload_bar(self):
        img = pygame.image.load("upload_white.png")
        ratio = 0.40
        shrink = ( int(img.get_size()[0]*ratio), int(img.get_size()[1]*ratio))
        self.upload_img = pygame.transform.scale(img, shrink) 

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
    
    def gen_upload_menu(self):
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
        surf.blit(l0, (150, 220))
        #Generate Gradient Button Image
        for i in [float(x)/20 for x in range(10,21)]:
           pygame.draw.circle(surf, (71*i, 211*i, 59*i), (282,425), radius)
           radius -= 2

        self.upload_menu = surf
        self.upload_menu_pos = (-50,-100)
        #self.upload_menu_bar_pos = (0,((self.disp_h-film_h)/2))
        #self.upload_menu_bar_txt_pos = (50, ((self.disp_h-film_h)/2) +20 )
    
    def gen_upload_info(self):
        film_h = 200
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
 
        self.upload_info_pos = (0,self.disp_h-250)
        self.upload_info = []
        info_bars_txt = ["Hold up your smartphone camera app to this QR code...",
                         "No phone? Dont worry the link will be printed on the Photo!"]
        for txt in info_bars_txt:
            bar = surf.copy()
            font = pygame.font.Font("springtime_in_april.ttf", 75)
            t = font.render(txt, 1, (255,255,255))
            bar.blit( t,(250,50))
            self.upload_info.append(bar)
            

    def gen_qr(self, link):
        qr = qrcode.QRCode( version=1,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=10,
                            border=4 )
        qr.add_data(link)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="transparent")
        img.save('/tmp/tmpqr.png')
        return '/tmp/tmpqr.png'



    def start(self, photo_set, upload_en, print_en):
        self.gpio.set('green_led', 0)
        self.gpio.set('red_led', 0)
        self.gameDisplay.fill((200,200,200))
        
        self.photo_set = photo_set
        
        self.ani_q_img_push( self.upload_bar, self.upload_bar_pos , 0.1, False, False)
        self.ani_q_txt_push( "Uploading....", (255,255,255), 200,self.upload_bar_txt_pos , 0.1, False)
        self.ani_q_cmd_push("UPLOAD")
        self.next()
    
    def state_cmd(self, item ):
        if item['cmd'] == 'UPLOAD':
           self.pcloud_upload_q = Queue()
           #print "pCloud Starting Upload"
           self.pcloud_upload = Thread(target=self.pcloud_uploadfiles,\
                                       args=( self.pCloud,\
                                              self.pcloud_upload_folder,\
                                              self.photo_set,\
                                              self.pcloud_upload_q ))
           self.pcloud_upload.start()
           self.ani_q_cmd_push("UPLOADWAIT")

        elif item['cmd'] == 'UPLOADWAIT':
            if self.pcloud_upload.is_alive(): #While Uploading Continue animation
                self.ani_q_img_push( self.upload_img, self.upload_bar_img_pos, 0.9, True,False,False)
                self.ani_q_img_push( self.upload_bar, self.upload_bar_pos , 0.1, False)
                self.ani_q_txt_push( "Uploading....", (255,255,255), 200,self.upload_bar_txt_pos , 0.1, False)
                self.ani_q_cmd_push("UPLOADWAIT")
            else:
                self.upload_link = self.pcloud_upload_q.get()
                print "pCloud Upload Complete .. {0}".format(self.upload_link)
                self.ani_q_cmd_push("UPLOADQR")

        elif item['cmd'] == 'UPLOADQR':
            self.gpio.set('green_led', 1)
            self.gpio.set('red_led', 0)
            qr_path = self.gen_qr(self.upload_link)
            self.gameDisplay.fill((200,200,200))
            qr_img = pygame.image.load(qr_path)
            qr_pos = (((self.disp_w - qr_img.get_size()[0])/2)+200, ((self.disp_h - qr_img.get_size()[1])/2)-175 )
            link_pos = (((self.disp_w)/2)-100, ((self.disp_h)/2))
            self.ani_q_img_push( qr_img, qr_pos , 0.1, False)
            self.ani_q_txt_push( self.upload_link, (40,40,40), 75, link_pos, 0.1, False)
            self.ani_q_img_push( self.upload_menu, self.upload_menu_pos, 0.1, False)
            self.ani_q_cmd_push("COMPLETE")
            self.ani_q_cmd_push("UPLOADINFO")
        
        elif item['cmd'] == 'UPLOADINFO':
            for info in self.upload_info:
                self.ani_q_img_push( info, self.upload_info_pos , 0.4, True, forceSurfaceAlpha=False)
                self.ani_q_pause_push(3)
            
            self.ani_q_cmd_push("UPLOADINFO")





    def reset(self):
        State.reset(self)
        self.photo_set = []
        self.pcloud_upload = None
        self.upload_link = None
