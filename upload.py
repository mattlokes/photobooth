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
from multiprocessing import Process as Thread
from multiprocessing import Queue


class Upload(State):

    def __init__(self, gd, w, h, fps):
        State.__init__(self, gd, w, h, fps)
        self.pcloud_pass_file = ".pcloud_pass"
        self.pcloud_path = "/photobooth/craig_lucy_wedding_2018"

        self.gen_upload_bar()

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



    def start(self, photo_set, upload_en, print_en):
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
                self.ani_q_cmd_push("COMPLETE")

    def stop(self):
        pass

    def reset(self):
        State.reset(self)
        self.photo_set = []
        self.pcloud_upload = None
        self.upload_link = None
