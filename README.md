# photobooth
A Raspberry-Pi powered photobooth using gPhoto 2.

## Description
Python application to build your own photobooth using a [Raspberry Pi](https://www.raspberrypi.org/), [gPhoto2](http://gphoto.sourceforge.net/) and [pygame](https://www.pygame.org).

Code started life as https://github.com/reuterbal/photobooth however this fork is an almost complete rewrite with additional features:

* Greatly Improved GUI
* Support for Google Photos Upload
* Support for CUPS Printer
* Support for Light Up Arcade Buttons
* Support for Webcam for improved preview.

## Requirements

### Software stack
The following is required for running this photobooth application. I used the versions given in brackets, others might work just as well.

* [Python](https://www.python.org) (2.7.3)
* [Pygame](https://www.pygame.org) (1.9.1)
* [Pillow](http://pillow.readthedocs.org) (2.8.1)
* [gPhoto](http://gphoto.sourceforge.net/) (2.5.6 or later) or [OpenCV](http://opencv.org)
* Optional: [RPi.GPIO](https://pypi.python.org/pypi/RPi.GPIO) (0.5.11)
* Optional: [gphoto2-cffi](https://github.com/jbaiter/gphoto2-cffi) or [Piggyphoto](https://github.com/alexdu/piggyphoto)
* Optional: Google Drive API - " pip install --upgrade google-api-python-client"

RPi.GPIO is necessary to use external buttons as a trigger but it works just fine without. Triggering is then only possible using 'g' & 'r' key (Context Related).

### Hardware
* [Raspberry Pi](https://www.raspberrypi.org/) (Due to improved GUI needs to be raspberry pi 2 or newer)
* Camera supported by gPhoto. I've used a Canon EOS 550D.
* Optional: GPIO PIN TODO

## Usage
Simply download `main.py` or clone the repository and run it.
It opens the GUI, prints the features of the connected camera, e.g.,
```
$ ./main.py 
Abilities for camera             : Canon EOS 500D
Serial port support              : no
USB support                      : yes
Capture choices                  :
                                 : Image
                                 : Preview
Configuration support            : yes
Delete selected files on camera  : yes
Delete all files on camera       : no
File preview (thumbnail) support : yes
File upload support              : yes
```

Available actions:

* Press `q`: Exit the application
* Press `g` or GPIO**: does green action (context sensitive) normally an yes/accept/proceed action.
* Press `r` or GPIO**: does red action (context sensitive) normally an no/decline/cancel action.
* Press GPIO**: Hidden button to disable printer.
* Press GPIO**: Hidden button to disable upload.
 
All pictures taken are stored in a subfolder of the current working directory, named `YYYY-mm-dd` after the current date. Existing files are not overwritten.

## Installation
A brief description on how to set-up a Raspberry Pi to use this photobooth software.

1. Download latest Raspbian image and set-up an SD-card. You can follow [these instruction](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

2. Insert the SD-card into your Raspberry Pi and fire it up. Use the `raspi-config` tool that is shown automatically on the first boot to configure your system (e.g., expand partition, change hostname, password, enable SSH, configure to boot into GUI, etc.).

3. Reboot and open a terminal. Type `sudo rpi-update` to install the latest software versions. Reboot.

4. Run `sudo apt-get update` and `sudo apt-get upgrade` to upgrade all installed software.

5. Install any additionally required software:
  * Pillow: 

    ```
    sudo apt-get install python-dev python-pip libjpeg8-dev
    sudo pip install Pillow
    ```

  * gPhoto2: Unfortunately, the version in the repositories is too old to work (some USB-bugs), hence one must use [Gonzalos installer script](https://github.com/gonzalo/gphoto2-updater)

    ```
    git clone https://github.com/gonzalo/gphoto2-updater
    sudo gphoto2-updater/gphoto2-updater.sh
    ```

    To ensure the camera can be controlled properly via USB, remove some files:

    ```
    sudo rm /usr/share/dbus-1/services/org.gtk.Private.GPhoto2VolumeMonitor.service
    sudo rm /usr/share/gvfs/mounts/gphoto2.mount
    sudo rm /usr/share/gvfs/remote-volume-monitors/gphoto2.monitor
    sudo rm /usr/lib/gvfs/gvfs-gphoto2-volume-monitor
    ```

6. Reboot.

7. Clone the Photobooth repository
   ```
   git clone https://github.com/mattlokes/photobooth
   ```
   and run `main.py`

8. Optional but highly recommended, as it improves performance significantly: install some Python bindings for gPhoto2. [gphoto2-cffi](https://github.com/jbaiter/gphoto2-cffi) can be used.

   8.1 Installing gphoto2-cffi:
   Install [cffi](https://bitbucket.org/cffi/cffi)
   ```
   sudo apt-get install libffi6 libffi-dev python-cffi
   ```
   Download and install gphoto2-cffi for gPhoto2
   ```
   git clone https://github.com/jbaiter/gphoto2-cffi.git
   cd gphoto2-cffi
   python setup.py build
   sudo python setup.py install
   ```

