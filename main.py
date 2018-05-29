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
from gpio import Gpio as GPIO

from picturelist import *
from introanimation import *
from capture import *
from process import *
from upload import *

def sig_green_handler(signum, frame):
    stim = "GPIO" if frame == None else "Signal"
    print 'Green handler called from ' + stim
    green_event = pygame.event.Event( pygame.USEREVENT, sig='green')
    pygame.event.post(green_event)

def sig_red_handler(signum, frame):
    stim = "GPIO" if frame == None else "Signal"
    print 'Red handler called from ' + stim
    red_event = pygame.event.Event( pygame.USEREVENT, sig='red')
    pygame.event.post(red_event)

def handle_gpio( channel ):
    if channel == gpio_green_button:
        sig_green_handler(None, None)
    elif channel == gpio_red_button:
        sig_red_handler(None, None)
    else:
        print "Warning, dodgy GPIO Seen!"


def green_press ( e ):
    if e.type == pygame.KEYDOWN:      #KEYBOARD 
        if e.key == pygame.K_g:
            return True
    elif e.type == pygame.USEREVENT:  #SIGNAL/GPIO
        if e.sig == "green":
            return True
    else:
        return False

def red_press ( e ):
    if e.type == pygame.KEYDOWN:        #KEYBOARD
        if e.key == pygame.K_r:
            return True
    elif e.type == pygame.USEREVENT:    #SIGNAL/GPIO
        if e.sig == "red":
            return True
    else:
        return False

def main():
    global printer_en
    global upload_en

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

    
    intro_ani = IntroAnimation( gameDisplay, disp_w, disp_h, fps, gpio, pictures )
    capture   = Capture ( gameDisplay, disp_w, disp_h, fps, gpio, camera )
    process  = Process( gameDisplay, disp_w, disp_h, fps, gpio, pictures )
    upload = Upload( gameDisplay, disp_w, disp_h,fps, gpio)

    final_photos = []
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
                        state = "UPLOAD_S"
                    elif red_press( event ): #Retake
                        process.reset()
                        state = "CAPTURE_S"
            process.next()
            pygame.display.update()
        
        ### PRINTER UPLOAD STATES ###
        if state == "UPLOAD_S":
            #Update Photo Upload/ Printer Enable Switch State
            # TODO

            upload.start( final_photos, upload_en, printer_en )
            pygame.display.update()
            state = "UPLOAD"
        
        if state == "UPLOAD":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state = "END"
                elif upload.is_done():
                    if green_press( event):
                        upload.reset()
                        state = "INTRO_S"

            upload.next()
            pygame.display.update()
       
        clock.tick(fps)
    
    pygame.quit()
    quit()


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
gpio_green_button = 6
gpio_green_led = 13
gpio_red_button = 5
gpio_red_led = 19

gpio = GPIO(handle_gpio, 
            [gpio_green_button,gpio_red_button], 
            [gpio_green_led, gpio_red_led],
            in_alias=['green_but','red_but'],
            out_alias=['green_led','red_led'],
           )

# Is Photo Available
upload_en = True

# Printer Option enable?
printer_en = True

# pygame fps
fps = 45

main()
