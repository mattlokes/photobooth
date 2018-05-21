import getpass

cups_fail = False
try:
   import cups
except:
    print "Looks like you need pycups to use this printer"
    cups_fail = True

class PrinterModule:
    """A PrinterModule Class"""

    def __init__( self ):
        if cups_fail:
            return None
        self.conn = cups.Connection()
        self.printers_list = self.conn.getPrinters()
        self.printer_name = self.printers_list.keys()[0]
        cups.setUser(getpass.getuser())

    def set_cups_user ( self, user ):
        cups.setUser(user)

    def print_image( self, path ):
        return self.conn.printFile(self.printer_name, path, "print_photo_booth", {})

    def get_attributes( self ):
        return self.conn.getPrinterAttributes( self.printer_name )
