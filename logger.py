from __future__ import print_function  # accomodate Python 2
from colors import *
from time import gmtime, strftime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Logger():
    @staticmethod
    def log(level, name, msg, c=''):
        s = "{:18} : {:11} : {:8} : {}".format( strftime("%Y-%m-%d %H.%M.%S", gmtime()),
                                                name.upper(),
                                                level.upper(),
                                                msg )

        ansiColMode = True
        if ansiColMode: #ANSI Colors
            print( color( s, fg=c))
        else:          #ASCI Colrs
            if c != '':
                if c == 'yellow': c = bcolors.WARNING
                if c == 'red':    c = bcolors.FAIL
                if c == 'green':  c = bcolors.OKGREEN
                if c == 'blue' :  c = bcolors.OKBLUE
                s = c + s +  bcolors.ENDC
            print(s)
    
    @staticmethod
    def debug(name="", msg=""):
       Logger.log('DEBUG',name,msg)

    @staticmethod
    def info(name="", msg=""):
       Logger.log('INFO',name,msg)
    
    @staticmethod
    def success(name="", msg=""):
       Logger.log('SUCCESS',name,msg, 'green')

    @staticmethod
    def warning(name="", msg=""):
       Logger.log('WARNING',name,msg, 'yellow')

    @staticmethod
    def error(name="", msg=""):
       Logger.log('ERROR',name,msg, 'red')
