#!/usr/bin/env python

# Currently just a test to see if we can send data to the clock tamer.

# Import things to know about clock tamer
# It implements SPI with CPOL=1 and CPHA=0
# meaning we read on falling edge of SCK and change on rising edge

# Here are our pinouts:
# nSS  = io_rx_08 = 0x0100 : active low
# SCK  = io_rx_09 = 0x0200
# MOSI = io_rx_10 = 0x0400 : USRP->ClockTamer
# MISO = io_rx_11 = 0x0800 : ClockTamer->USRP
# nRST = io_rx_12 = 0x1000 : active low

from gnuradio import usrp
from struct import *
from time import sleep
import optparse, sys

class ClockTamer:
    def __init__(self, usrp, which):
        self.__usrp = usrp
        self.__side = which
        self.NSS = 0x0100
        self.SCK = 0x0200
        self.MOSI = 0x0400
        self.MISO = 0x0800
        self.NRST = 0x1000
        self.__usrp._write_oe(self.__side, self.NSS | self.SCK | self.MOSI | self.NRST, self.NSS | self.SCK | self.MOSI | self.MISO | self.NRST )
        self.set_hi(self.NSS)
        self.set_hi(self.NRST)

        # Cycle the reset
        self.set_lo(self.NRST)
        self.set_hi(self.NRST)
        sleep(0.5)

    def set_lo( self, pin ):
        self.__usrp.write_io(self.__side, 0x0000, pin )
    def set_hi( self, pin ):
        self.__usrp.write_io(self.__side, 0xFFFF, pin )
    def get_pin( self, pin ):
        return self.__usrp.read_io(self.__side) & pin

    def clean( self, text ):
        return "".join(i for i in text if ord(i)<128 and ord(i)>31) 

    def write( self, text ):
        result_string = ""
        for c in text:
            b = ord(c)
            char_buffer = 0x00

            # Prep the first bit
            value = (b >> 7) & 1
            if ( value > 0 ):
                self.set_hi(self.MOSI)
            else:
                self.set_lo(self.MOSI)
            
            # Start sending
            self.set_hi(self.SCK)
            self.set_lo(self.NSS)

            for i in xrange(7,-1,-1):
                self.set_hi(self.SCK)
                value = (b >> i) & 1
                if ( value > 0 ):
                    self.set_hi(self.MOSI)
                else:
                    self.set_lo(self.MOSI)
                self.set_lo(self.SCK)
                bit = self.get_pin(self.MISO)
                if ( bit > 0 ):
                    char_buffer = (char_buffer << 1) | 0x01
                else:
                    char_buffer = char_buffer << 1
            self.set_hi(self.SCK)
            self.set_hi(self.NSS)
            result_string += chr(char_buffer)
        return result_string

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main():
    try:
        try:
            usage = "usage: clock_tamer.py [--reset][--set_clock N][--cmd \"\"]"
            parser = optparse.OptionParser(usage=usage)
            parser.set_defaults(reset=False)
            parser.set_defaults(clock=0)
            parser.set_defaults(cmd="")
            parser.add_option("-r","--reset", dest="reset",
                              action="store_true",
                              help="Only reset the Clock Tamer")
            parser.add_option("--set_clock", dest="clock",
                              help="Set the output clock",type="int")
            parser.add_option("--cmd", dest="cmd",
                              help="Commands to send to Clock Tamer",type="string")
            (options, args) = parser.parse_args()

            if not options.reset and options.clock < 1 and options.cmd == "":
                parser.error("Need input arguments")

        except optparse.OptionError, msg:
            raise Usage(msg)

        clock = ClockTamer(usrp.source_c(0), 0)
        if not options.reset:
            if not options.cmd == "":
                cmds = options.cmd.split(";")
                for cmd in cmds:
                    print "Wrote: "+cmd
                    clock.write(cmd+"\r")
                    result = clock.write("".center(48))
                    print "Response: "+clock.clean(result)
            else:
                cmd = "SET,,OUT,"+str(options.clock)
                print "Wrote: "+cmd
                clock.write(cmd+"\r")
                result = clock.write("".center(48))
                print "Response: "+clock.clean(result)
        else:
            print "ClockTamer cycled"

    except Usage, err:
        print >>sys.stderr, err.msg
        return 2

#    except Exception, err:
#        sys.stderr.write( str(err) + '\n' )
#        return 1

if __name__ == "__main__":
    sys.exit(main())
