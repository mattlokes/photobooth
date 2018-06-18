import getpass
import re
import subprocess
from fuzzywuzzy import fuzz

from logger import *

cups_fail = False
try:
   import cups
except:
    Logger.error(__name__,"Looks like you need pycups to use this printer")
    cups_fail = True

class PrinterModule:
    """A PrinterModule Class"""

    def __init__( self, cfg ):
        if cups_fail:
            return None
        self.cfg = cfg
        self.conn = cups.Connection()
        self.printers_list = self.conn.getPrinters()
        self.printer_name = self.printers_list.keys()[0]
        Logger.info(__name__, "CUPS Printer - {0}".format(self.printer_name))
        cups.setUser(getpass.getuser())
        lsusb_name = self.printer_connected()
        if lsusb_name:
            Logger.success(__name__, "USB Printer - {0}".format(lsusb_name))
        else:
            Logger.warning(__name__, "USB Printer - {0}".format(lsusb_name))

    def set_cups_user ( self, user ):
        cups.setUser(user)

    def print_image( self, path ):
        if self.printer_connected() != None :
            p = self.conn.printFile(self.printer_name, path, 
                                    "print_photo_booth", {'media': self.cfg.get("printer__media")})
            return p
        else:
            #Print Command None
            return None

    def get_attributes( self ):
        return self.conn.getPrinterAttributes( self.printer_name )
    
    def printer_connected( self ):
        device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
        df = subprocess.check_output("lsusb")
        devices = []
        for i in df.split('\n'):
            if i:
                info = device_re.match(i)
                if info:
                    dinfo = info.groupdict()
                    dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
                    devices.append(dinfo)
        for d in devices:
            if fuzz.partial_ratio(d['tag'].replace("_"," ").upper(), 
                                  self.printer_name.replace("_"," ").upper()) > 60:
                return d['tag']
        return None
    

