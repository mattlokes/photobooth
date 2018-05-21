import pygame
import random
import operator
import os
import signal
from datetime import datetime
from glob import glob
from sys import exit
from time import sleep, clock

from PIL import Image

from camera import CameraException, Camera_gPhoto as CameraModule
from events import Rpi_GPIO as GPIO

from picturelist import *
from introanimation import *
from capture import *
from process import *

def sig_green_handler(signum, frame):
    print 'Green handler called with signal'
    green_event = pygame.event.Event( pygame.USEREVENT, sig='green')
    pygame.event.post(green_event)

def sig_red_handler(signum, frame):
    print 'Red handler called with signal'
    red_event = pygame.event.Event( pygame.USEREVENT, sig='red')
    pygame.event.post(red_event)

def green_press ( e ):
    if e.type == pygame.KEYDOWN:             #KEYBOARD 
        if e.key == pygame.K_g:
            return True
    elif e.type == 3:                        #GPIO
        pass #TODO
    elif e.type == pygame.USEREVENT:  #SIGNAL
        if e.sig == "green":
            return True
    else:
        return False

def red_press ( e ):
    if e.type == pygame.KEYDOWN:             #KEYBOARD
        if e.key == pygame.K_r:
            return True
    elif e.type == 3:                        #GPIO
        pass #TODO
    elif e.type == pygame.USEREVENT:  #SIGNAL
        if e.sig == "red":
            return True
    else:
        return False


def main():
    ### Configuration ###

    # Screen size
    disp_w = 1824
    disp_h = 984

    # Maximum size of assembled image
    image_size = (2352, 1568)

    # Size of pictures in the assembled image
    thumb_size = (1176, 784)

    # Image basename
    picture_basename = datetime.now().strftime("%Y-%m-%d/pic")

    # GPIO channels
    gpio_shutdown_channel = 24 # pin 18 in all Raspi-Versions
    gpio_green_channel = 23 # pin 16 in all Raspi-Versions
    gpio_lamp_channel = 4 # pin 7 in all Raspi-Versions

    pose_time = 3

    # Is Photo Available
    photo_upload = False
   
    # Printer Option enable?
    printer_enable = True

    # pygame fps
    fps = 45
    
    ### Initialisation ###
    pygame.init()
    gameDisplay = pygame.display.set_mode((disp_w,disp_h),pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    pygame.display.set_caption('photobooth')
    clock = pygame.time.Clock()

    pictures = PictureList(picture_basename)

    #pkill -USR1 python
    signal.signal(signal.SIGUSR1, sig_green_handler)
    #pkill -USR2 python
    signal.signal(signal.SIGUSR2, sig_red_handler)

    camera = CameraModule(image_size)
    
    if printer_enable:
        from printer import PrinterModule
        printer  = PrinterModule()
        if printer == None:
            printer_enable = False
        else:
            printer_enable = True

    intro_ani = IntroAnimation( gameDisplay, disp_w, disp_h, pictures )
    capture   = Capture ( gameDisplay, disp_w, disp_h, camera, fps )
    process  = Process( gameDisplay, disp_w, disp_h, pictures, fps )
    #printupload = PrintUpload( gameDisplay, disp_w, disp_h, printer, uploader,fps)


    state = "INTRO_S"
    while not state == "END":
      
        ### INTRO ANIMATION STATES ###
        if state == "INTRO_S":
            intro_ani.start()
            pygame.display.update()
            state = "INTRO"

        if state == "INTRO":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state = "END"
                elif green_press( event ):
                    state = "CAPTURE_S"

            intro_ani.next()                                     
            pygame.display.update()

        ### INTRO CAPTURE STATES ###
        if state == "CAPTURE_S":
            capture.start()
            pygame.display.update()
            state = "CAPTURE"

        if state == "CAPTURE":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state = "END"

            capture.next()
            pygame.display.update()

            if capture.is_done():
                capture.reset()
                photo_set = capture.cap_path
                photo_set_thumbs = capture.cap_thumbs
                state = "PROCESS_S"
        
        ### INTRO PROCESS STATES ###
        if state == "PROCESS_S":
            process.start( photo_set, photo_set_thumbs )
            pygame.display.update()
            state = "PROCESS"
        
        if state == "PROCESS":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state = "END"
                elif process.is_done():
                    if green_press( event):  
                        process.reset()
                        state = "PRINTUP_S"
                    elif red_press( event ): #Retake
                        process.reset()
                        state = "CAPTURE_S"

            process.next()
            pygame.display.update()


       
        clock.tick(fps)
    
    pygame.quit()
    quit()


main()
