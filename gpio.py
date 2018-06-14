#!/usr/bin/env python
from logger import *

try:
    import RPi.GPIO as GPIO
    gpio_enabled = True
except ImportError:
    gpio_enabled = False

class Gpio:
    def __init__(self, handle_function, input_channels = [], output_channels = [], in_alias=None,out_alias=None):
        if gpio_enabled:
            self.outs = {}
            self.ins = {}

            # Display initial information
            Logger.info(__name__,"Your Raspberry Pi is board revision " + str(GPIO.RPI_INFO['P1_REVISION']))
            Logger.info(__name__,"RPi.GPIO version is " + str(GPIO.VERSION))

            # Choose BCM numbering system
            GPIO.setmode(GPIO.BCM)

            # Disable warnings
            GPIO.setwarnings(False)

            # Setup the input channels
            for idx,input_channel in enumerate(input_channels):
                GPIO.setup(input_channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(input_channel, GPIO.RISING, callback=handle_function, bouncetime=200)
                if in_alias != None:
                    self.ins[input_channel] = {'alias':in_alias[idx]}

            # Setup the output channels
            for idx,output_channel in enumerate(output_channels):
                GPIO.setup(output_channel, GPIO.OUT)
                GPIO.output(output_channel, GPIO.LOW)
                if out_alias != None:
                    self.outs[output_channel] = {'alias':out_alias[idx],'state':0 }
                else:
                    self.outs[output_channel] = { 'state':0 }
            
        else:
            Logger.warning(__name__,"RPi.GPIO could not be loaded. GPIO disabled.")

    def teardown(self):
        if gpio_enabled:
            GPIO.cleanup()

    def set_output(self, channel, value=0):
        if gpio_enabled:
            GPIO.output(channel, GPIO.HIGH if value==1 else GPIO.LOW)
            self.outs[channel]['state'] = value

    def toggle_output(self, channel):
        if gpio_enabled:
            state = 0 if self.outs[channel]['state'] else 1 #Toggle State
            self.set_output(channel, state)

    def unalias(self, alias):
        m = [ x[0] for x in self.outs.items()+self.ins.items() if x[1]['alias'] == alias]
        if len(m) == 1: return m[0]
        else:      return None #Multi Match no match
        
    def set(self, alias, value):
        chan = self.unalias(alias)
        if chan == None:
            Logger.warning(__name__,"call to set unaliased output \""+alias+"\"")
        else:
            self.set_output(chan, value)
   
    def toggle(self, alias):
        chan = self.unalias(alias)
        if chan == None:
            Logger.warning(__name__,"call to toggle unaliased output \""+alias+"\"")
        else:
            self.toggle.output(chan)



