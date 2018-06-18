import pygame
import random
import operator
import os
import signal
from datetime import datetime
from glob import glob
from sys import exit
import sys
from time import sleep, clock

from PIL import Image

from camera import CameraException, Camera_gPhoto as CameraModule
from printer import PrinterModule
from gpio import Gpio as GPIO

from config import *
from picturelist import *
from introanimation import *
from capture import *
from process import *
from upload import *
from prin import *

from logger import *


def sig_green_handler(signum, frame):
    stim = "GPIO" if frame == None else "Signal"
    Logger.debug(__name__,'Green handler called from ' + stim)
    green_event = pygame.event.Event( pygame.USEREVENT, sig='green')
    pygame.event.post(green_event)

def sig_red_handler(signum, frame):
    stim = "GPIO" if frame == None else "Signal"
    Logger.debug(__name__,'Red handler called from ' + stim)
    red_event = pygame.event.Event( pygame.USEREVENT+1, sig='red')
    pygame.event.post(red_event)

def handle_gpio( channel ):
    if channel == gpio_green_button:
        sig_green_handler(None, None)
    elif channel == gpio_red_button:
        sig_red_handler(None, None)
    else:
        Logger.warning(__name__,"dodgy GPIO Seen!")


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
    elif e.type == (pygame.USEREVENT+1):    #SIGNAL/GPIO
        if e.sig == "red":
            return True
    else:
        return False

def reset_combo( el ):
    if len(el) < 2:
        return False
    if el[0].type != pygame.USEREVENT:
        return False
    elif el[1].type != pygame.USEREVENT+1:
        return False
    else:
        return True

def main():

    ### Initialisation ###
    Logger.info(__name__,"Initialising.... ")
    pygame.init()
    gameDisplay = pygame.display.set_mode((disp_w,disp_h),pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    pygame.display.set_caption('Photobooth')
    clock = pygame.time.Clock()

    pictures = PictureList(cfg, picture_basename)

    #pkill -USR1 python
    signal.signal(signal.SIGUSR1, sig_green_handler)
    #pkill -USR2 python
    signal.signal(signal.SIGUSR2, sig_red_handler)

    camera = CameraModule(image_size)
    printer  = PrinterModule(cfg)
    
    intro_ani = IntroAnimation( cfg, gameDisplay, disp_w, disp_h, fps, gpio, pictures )
    capture   = Capture ( cfg, gameDisplay, disp_w, disp_h, 15, gpio, camera )
    process  = Process( cfg, gameDisplay, disp_w, disp_h, fps, gpio, pictures )
    upload = Upload( cfg, gameDisplay, disp_w, disp_h,fps, gpio)
    prin  = Prin( cfg, gameDisplay, disp_w, disp_h,fps, gpio, printer )


    Logger.success(__name__,"Initialisation Complete! ")
    state = "INTRO_S"
    retake = False
    while not state == "END":
      
        event_list = pygame.event.get()

        if reset_combo(event_list):
            Logger.warning(__name__,"Restarting...")
            intro_ani.stop()
            capture.stop()
            process.stop()
            upload.stop()
            os.execv(sys.executable, ['python'] + sys.argv)

        ### INTRO ANIMATION STATES ###
        if state == "INTRO_S":
            retake = False
            final_photos = []
            final_link = ""
            final_uploaded = False
            final_printed = False

            intro_ani.start()
            pygame.display.update()
            state = "INTRO"

        if state == "INTRO":
            for event in event_list:
                if event.type == pygame.QUIT:
                    state = "END"
                elif green_press( event ):
                    state = "CAPTURE_S"

            intro_ani.next()                                     
            pygame.display.update()

        ### CAPTURE STATES ###
        if state == "CAPTURE_S":
            capture.start(retake)
            pygame.display.update()
            state = "CAPTURE"

        if state == "CAPTURE":
            for event in event_list:
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
            for event in event_list:
                if event.type == pygame.QUIT:
                    state = "END"
                elif process.is_done():
                    if green_press( event):  
                        final_photos = process.get_result()
                        process.reset()

                        if cfg.get("upload__enabled"):
                            state = "UPLOAD_S"
                        elif cfg.get("printer__enabled"):
                            state = "PRINT_S"
                        else:
                            state = "DONE"

                    elif red_press( event ): #Retake
                        process.reset()
                        retake = True
                        state = "CAPTURE_S"
            process.next()
            pygame.display.update()
        
        ### PRINTER UPLOAD STATES ###
        if state == "UPLOAD_S":
            #Update Photo Upload/ Printer Enable Switch State
            # TODO

            upload.start( final_photos )
            pygame.display.update()
            state = "UPLOAD"
        
        if state == "UPLOAD":
            for event in event_list:
                if event.type == pygame.QUIT:
                    state = "END"
                elif upload.is_done():
                    final_link = upload.upload_link
                    #TODO upload success
                    if green_press( event):
                        upload.reset()
                        final_uploaded = True

                        if cfg.get("printer__enabled"):
                            state = "PRINT_S"
                        else:
                            state = "DONE"

            upload.next()
            pygame.display.update()
        
        ### PRINTER UPLOAD STATES ###
        if state == "PRINT_S":
            #Update Photo Upload/ Printer Enable Switch State
            # TODO

            prin.start( final_photos, final_link )
            pygame.display.update()
            state = "PRINT"
        
        if state == "PRINT":
            for event in event_list:
                if event.type == pygame.QUIT:
                    state = "END"
            
            if prin.is_done():
                #TODO Get print success value
                prin.reset()
                state = "DONE"
                final_printed = True

            prin.next()
            pygame.display.update()

        if state == "DONE":
            pictures.log_add( final_photos[0], final_link, final_uploaded, final_printed )
            state = "INTRO_S"
       
        if "CAPTURE" in state:
            clock.tick(15)
        else:
            clock.tick(fps)
    
    pygame.quit()
    quit()


### Configuration ###

cfg = Config("config.yaml")

# Screen size
disp_w = 1824
disp_h = 984

# Maximum size of assembled image
image_size = (2352, 1568)

# Size of pictures in the assembled image
thumb_size = (1176, 784)

# Image basename
picture_basename = "{0}/{1}/{2}/pic".format( cfg.get("photo_dir"), 
                                             cfg.get("event_name"),
                                             datetime.now().strftime("%Y-%m-%d") )

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

# pygame fps
fps = 45

main()
