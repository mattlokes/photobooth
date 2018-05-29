#!/usr/bin/env python

import os
from datetime import datetime
from glob import glob
from sys import exit
from time import sleep, clock
from time import gmtime, strftime

class PictureList:
    """A simple helper class.

    It provides the filenames for the assembled pictures and keeps count
    of taken and previously existing pictures.
    """

    def __init__(self, basename):
        """Initialize filenames to the given basename and search for
        existing files. Set the counter accordingly.
        """

        # Set basename and suffix
        self.basename = basename
        self.suffix = ".jpg"
        self.count_width = 5

        # Ensure directory exists
        dirname = os.path.dirname(self.basename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            self.log_create(dirname)


        self.log = dirname + "/log.csv"
        # Find existing files
        self.count_pattern = "[0-9]" * self.count_width
        pictures = glob(self.basename + self.count_pattern + self.suffix)

        # Get number of latest file
        if len(pictures) == 0:
            self.counter = 0
            self.counter_last = 0
        else:
            pictures.sort()
            last_picture = pictures[-1]
            self.counter = int(last_picture[-(self.count_width+len(self.suffix)):-len(self.suffix)])
            self.counter_last = self.counter - 1

        # Print initial infos
        print("Info: Number of last existing file: " + str(self.counter))
        print("Info: Saving assembled pictures as: " + self.basename + "XXXXX.jpg")

    def get(self, count):
        return self.basename + str(count).zfill(self.count_width) + self.suffix

    def get_last(self):
        return self.get(self.counter)

    def get_last_num(self):
        return self.counter_last

    def get_next(self):
        self.counter_last = self.counter
        self.counter += 1
        return self.get(self.counter)

    def get_list(self):
        if self.counter == 0:
            return [ "default.jpg" ]
        else:
            return glob(self.basename + self.count_pattern + self.suffix)

    def log_add(self, path, link, uploaded, printed ):
        uploaded = "Yes" if uploaded else "No"
        printed = "Yes" if uploaded else "No"
        t =strftime("%d-%m-%Y %H:%M:%S", gmtime())
        f= open(self.log,"a")
        #f.write("Num,Time,Path,Link,Uploaded,Printed")
        f.write("\"{0}\",\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\"\n". format( 
                                                   self.get_last_num(),
                                                   t,
                                                   path,
                                                   link,
                                                   uploaded,
                                                   printed))
        f.close()

    def log_create(self, dirname):
        f= open(dirname + "/log.csv","w+")
        f.write("Num,Time,Path,Link,Uploaded,Printed\n")
        f.close()

