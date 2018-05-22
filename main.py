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
from printupload import *

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
    upload_en = True
   
    # Printer Option enable?
    printer_en = True

    # pygame fps
    fps = 45
    
    ### Initialisation ###
    pygame.init()
    gameDisplay = pygame.display.set_mode((disp_w,disp_h),pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    pygame.display.set_caption('Photobooth')
    clock = pygame.time.Clock()

    pictures = PictureList(picture_basename)

    #pkill -USR1 python
    signal.signal(signal.SIGUSR1, sig_green_handler)
    #pkill -USR2 python
    signal.signal(signal.SIGUSR2, sig_red_handler)

    camera = CameraModule(image_size)
    
    if printer_en:
        from printer import PrinterModule
        printer  = PrinterModule()
        if printer == None:
            printer_en = False
        else:
            printer_en = True

    intro_ani = IntroAnimation( gameDisplay, disp_w, disp_h, pictures )
    capture   = Capture ( gameDisplay, disp_w, disp_h, camera, fps )
    process  = Process( gameDisplay, disp_w, disp_h, pictures, fps )
    printupload = PrintUpload( gameDisplay, disp_w, disp_h,fps, printer)

    final_photos = []
    #state = "INTRO_S"
    state = "PRINTUP_S"
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

        ### CAPTURE STATES ###
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
        
        ### PROCESS STATES ###
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
                        final_photos = process.get_result()
                        process.reset()
                        state = "PRINTUP_S"
                    elif red_press( event ): #Retake
                        process.reset()
                        state = "CAPTURE_S"
            process.next()
            pygame.display.update()
        
        ### PRINTER UPLOAD STATES ###
        if state == "PRINTUP_S":

            #Update Photo Upload/ Printer Enable Switch State
            # TODO

            printupload.start( final_photos, upload_en, printer_en )
            pygame.display.update()
            state = "PRINTUP"
        
        if state == "PRINTUP":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state = "END"
                elif printupload.is_done():
                    state = "INTRO_S"

            printupload.next()
            pygame.display.update()
       
        clock.tick(fps)
    
    pygame.quit()
    quit()


main()
