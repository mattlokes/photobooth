#!/usr/bin/env python
# Created by br@re-web.eu, 2015

import subprocess
from logger import *
import pygame

cv_enabled = False
gphoto2cffi_enabled = False
piggyphoto_enabled = False
fake_enabled = False

try:
    import cv2 as cv
    cv_enabled = True
    #print('OpenCV available')
except ImportError:
    pass

try:
    import gphoto2cffi as gp
    gpExcept = gp.errors.GPhoto2Error
    gphoto2cffi_enabled = True
    #print('Gphoto2cffi available')
except ImportError:
    pass

if not gphoto2cffi_enabled:
    try:
        import piggyphoto as gp
        gpExcept = gp.libgphoto2error
        piggyphoto_enabled = True
        #print('Piggyphoto available')
    except ImportError:
        pass

import io

class CameraException(Exception):
    """Custom exception class to handle camera class errors"""
    def __init__(self, message, recoverable=False):
        self.message = message
        self.recoverable = recoverable


class Camera_cv:
    def __init__(self, picture_size):
        if cv_enabled:
            self.cap = cv.VideoCapture(0)
            self.cap.set(3, picture_size[0])
            self.cap.set(4, picture_size[1])

    def has_preview(self):
        return True 

    def take_preview(self, filename="/tmp/preview.jpg"):
        self.take_picture(filename)

    def take_picture(self, filename="/tmp/picture.jpg"):
        if cv_enabled:
            r, frame = self.cap.read()
            cv.imwrite(filename, frame)
            return filename
        else:
            raise CameraException("OpenCV not available!")

    def set_idle(self):
        pass


class Camera_gPhoto:
    """Camera class providing functionality to take pictures using gPhoto 2"""

    def __init__(self, picture_size):
        global fake_enabled
        self.picture_size = picture_size
        # Print the capabilities of the connected camera
        try:
            if gphoto2cffi_enabled:
                self.cap = gp.Camera()
                Logger.success(__name__,"{0} Connected".format(self.cap.model_name) )
            elif piggyphoto_enabled:
                self.cap = gp.camera()
                print(self.cap.abilities)
            else:
                print(self.call_gphoto("-a", "/dev/null"))
        except CameraException as e:
            Logger.warning(__name__,"Camera Error, Proceed with Fake Camera Mode...")
            fake_enabled = True
        except gpExcept as e:
            Logger.warning(__name__,"Camera Error, Proceed with Fake Camera Mode...")
            fake_enabled = True

    def call_gphoto(self, action, filename):
        # Try to run the command
        try:
            cmd = "gphoto2 --force-overwrite --quiet " + action + " --filename " + filename
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if "ERROR" in output:
                raise subprocess.CalledProcessError(returncode=0, cmd=cmd, output=output)
        except subprocess.CalledProcessError as e:
            if "EOS Capture failed: 2019" in e.output or "Perhaps no focus" in e.output:
                raise CameraException("Can't focus!\nMove a little bit!", True)
            elif "No camera found" in e.output:
                raise CameraException("No (supported) camera detected!", False)
            elif "command not found" in e.output:
                raise CameraException("gPhoto2 not found!", False)
            else:
                raise CameraException("Unknown error!\n" + '\n'.join(e.output.split('\n')[1:3]), False)
        return output

    def has_preview(self):
        return gphoto2cffi_enabled or piggyphoto_enabled

    def take_preview(self, filename="/tmp/preview.jpg"):
        if gphoto2cffi_enabled:
            self._save_picture(filename, self.cap.get_preview())
        elif piggyphoto_enabled:
            self.cap.capture_preview(filename)	
        else:
            raise CameraException("No preview supported!")

    def get_fast_preview( self, surf):
        #rather than saving to JPEG then reloading, return pygame surface
        jpeg = self.cap.get_preview() #get jpeg string
        surf = pygame.image.load(io.BytesIO(jpeg)) #pygame decodes jpeg to surface
        return surf

    def end_fast_preview( self ):
        self.cap.exit()

    def take_picture(self, filename="/tmp/picture.jpg"):
        if fake_enabled:
            filename = "dbg.jpg"
        elif gphoto2cffi_enabled:
            self._save_picture(filename, self.cap.capture())
        elif piggyphoto_enabled:
            self.cap.capture_image(filename)
        else:
            self.call_gphoto("--capture-image-and-download", filename)
        return filename

    def _save_picture(self, filename, data):
        f = open(filename, 'wb')
        f.write(data)
        f.close()

    def set_idle(self):
        if gphoto2cffi_enabled:
            self.cap._get_config()['actions']['viewfinder'].set(False)
        elif piggyphoto_enabled:
            # This doesn't work...
            self.cap.config.main.actions.viewfinder.value = 0
