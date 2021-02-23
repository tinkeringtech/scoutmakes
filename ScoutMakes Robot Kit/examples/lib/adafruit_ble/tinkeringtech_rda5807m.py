# The MIT License (MIT)
#
# Copyright (c) 2021 Vid Osep for TinkeringTech
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`tinkeringtech_rda5807m`
================================================================================

CircuitPython helper library for the RDA5807M FM radio module.


* Author(s): TinkeringTech & Vid Osep

Implementation Notes
--------------------

**Hardware:**

.. todo:: Add links to any specific hardware product page(s), or category page(s). Use unordered list & hyperlink rST
   inline format: "* `Link Text <url>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/tinkeringtech/rda5807m.git"

import time

# Registers definitions
FREQ_STEPS = 10
RADIO_REG_CHIPID = 0x00

RADIO_REG_CTRL = 0x02
RADIO_REG_CTRL_OUTPUT = 0x8000
RADIO_REG_CTRL_UNMUTE = 0x4000
RADIO_REG_CTRL_MONO = 0x2000
RADIO_REG_CTRL_BASS = 0x1000
RADIO_REG_CTRL_SEEKUP = 0x0200
RADIO_REG_CTRL_SEEK = 0x0100
RADIO_REG_CTRL_RDS = 0x0008
RADIO_REG_CTRL_NEW = 0x0004
RADIO_REG_CTRL_RESET = 0x0002
RADIO_REG_CTRL_ENABLE = 0x0001

RADIO_REG_CHAN = 0x03
RADIO_REG_CHAN_SPACE = 0x0003
RADIO_REG_CHAN_SPACE_100 = 0x0000
RADIO_REG_CHAN_BAND = 0x000C
RADIO_REG_CHAN_BAND_FM = 0x0000
RADIO_REG_CHAN_BAND_FMWORLD = 0x0008
RADIO_REG_CHAN_TUNE = 0x0010
RADIO_REG_CHAN_NR = 0x7FC0

RADIO_REG_R4 = 0x04
RADIO_REG_R4_EM50 = 0x0800
RADIO_REG_R4_SOFTMUTE = 0x0200
RADIO_REG_R4_AFC = 0x0100

RADIO_REG_VOL = 0x05
RADIO_REG_VOL_VOL = 0x000F

RADIO_REG_RA = 0x0A
RADIO_REG_RA_RDS = 0x8000
RADIO_REG_RA_RDSBLOCK = 0x0800
RADIO_REG_RA_STEREO = 0x0400
RADIO_REG_RA_NR = 0x03FF
RADIO_REG_RA_STC = 0x4000
RADIO_REG_RA_SF = 0x2000

RADIO_REG_RB = 0x0B
RADIO_REG_RB_FMTRUE = 0x0100
RADIO_REG_RB_FMREADY = 0x0080

RADIO_REG_RDSA = 0x0C
RADIO_REG_RDSB = 0x0D
RADIO_REG_RDSC = 0x0E
RADIO_REG_RDSD = 0x0F


# Radio class definition
class Radio:
    """
    A class for communicating with the rda5807m chip

    ...

    Attributes
    ----------
    registers : list
        virtual registers
    address : int
        chip's address
    maxvolume : int
        maximum volume
    freqLow, freqHigh, freqSteps : int
        min and max frequency for FM band, and frequency steps
    board : busio.i2c object
        used for i2c communication
    frequency : int
        current chip frequency
    volume : int
        current chip volume
    bassBoost : boolean
        toggle bass boost on the chip
    mute : boolean
        toggle mute/unmute
    softMute : boolean
        toggle soft mute (mute if signal strength too low)
    mono : boolean
        toggle stereo mode
    rds : boolean
        toggle rds
    tuned : boolean
        is chip tuned
    band : string
        selected band (FM or FMWORLD)
    """

    # Initialize virtual registers
    registers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # Chip constants
    address = 0x11
    maxvolume = 15

    # FMWORLD Band
    freqLow = 8700
    freqHigh = 10800
    freqSteps = 10

    # Set default frequency and volume
    def __init__(self, board, frequency=10000, volume=1):
        self.board = board
        self.frequency = frequency

        # Basic audio info
        self.volume = volume
        self.bassBoost = False
        self.mute = False
        self.softMute = False

        # Radio features from the chip
        self.mono = False
        self.rds = False
        self.tuned = False

        # Is the signal strong enough to get rds?
        self.rdsReady = False
        self.rdsThreshold = 20  # rssi threshold for accepting rds - change this to value most appropriate
        self.interval = 10  # Used for timing rssi checks - in seconds
        self.initial = time.monotonic()  # Time since boot

        # Band - Default FMWORLD
        # 1. FM
        # 2. FMWORLD
        self.band = "FM"

        # Functions saves register values to virtual registers, sets the basic frequency and volume
        self.setup()
        print("Got to point 1!")
        self.tune()  # Apply volume and frequency

    def setup(self):
        # Initialize registers
        self.registers[RADIO_REG_CHIPID] = 0x58
        self.registers[RADIO_REG_CTRL] = (RADIO_REG_CTRL_RESET | RADIO_REG_CTRL_ENABLE) | (
                RADIO_REG_CTRL_UNMUTE | RADIO_REG_CTRL_OUTPUT)
        # self.registers[RADIO_REG_R4] = RADIO_REG_R4_EM50
        # Initialized to volume - 6 by default
        self.registers[RADIO_REG_VOL] = 0x84D1
        # Other registers are already set to zero
        # Update registers
        self.saveRegister(RADIO_REG_CTRL)
        self.saveRegister(RADIO_REG_VOL)

        self.registers[
            RADIO_REG_CTRL] = RADIO_REG_CTRL_ENABLE | RADIO_REG_CTRL_NEW | RADIO_REG_CTRL_RDS | RADIO_REG_CTRL_UNMUTE | RADIO_REG_CTRL_OUTPUT
        self.saveRegister(RADIO_REG_CTRL)

        # Turn on bass boost and rds
        self.setBassBoost(True)

        self.rds = True
        self.mute = False

    def tune(self):
        # Tunes radio to current frequency and volume
        self.setFreq(self.frequency)
        self.setVolume(self.volume)
        self.tuned = True

    def setFreq(self, freq):
        # Sets frequency to freq
        if freq < self.freqLow:
            freq = self.freqLow
        elif freq > self.freqHigh:
            freq = self.freqHigh
        self.frequency = freq
        newChannel = (freq - self.freqLow) // 10

        regChannel = RADIO_REG_CHAN_TUNE  # Enable tuning
        regChannel = regChannel | (newChannel << 6)

        # Enable output, unmute
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | (
                RADIO_REG_CTRL_OUTPUT | RADIO_REG_CTRL_UNMUTE | RADIO_REG_CTRL_RDS | RADIO_REG_CTRL_ENABLE)
        self.saveRegister(RADIO_REG_CTRL)

        # Save frequency to register
        self.registers[RADIO_REG_CHAN] = regChannel
        self.saveRegister(RADIO_REG_CHAN)
        time.sleep(0.2)

        # Adjust volume
        self.saveRegister(RADIO_REG_VOL)
        time.sleep(0.3)

        # Get frequnecy
        self.getFreq()

        if self.getRssi() > self.rdsThreshold:
            self.rdsReady = True
        else:
            self.rdsReady = False

    def getFreq(self):
        # Read register RA
        self.writeBytes(bytes([RADIO_REG_RA]))
        self.registers[RADIO_REG_RA] = self.read16()

        ch = self.registers[RADIO_REG_RA] & RADIO_REG_RA_NR

        self.frequency = self.freqLow + ch * 10
        return self.frequency

    def formatFreq(self):
        # Formats the current frequency for better readabilitiy
        freq = self.frequency

        s = str(freq)
        s = list(s)
        last_two = s[-2:]
        s[-2] = "."
        s[-1] = last_two[0]
        s.append(last_two[1])
        return ("".join(s)) + " Mhz"

    def setBand(self, band):
        # Changes bands to FM or FMWORLD
        self.band = band
        if band == "FM":
            r = RADIO_REG_CHAN_BAND_FM
        else:
            r = RADIO_REG_CHAN_BAND_FMWORLD
        self.registers[RADIO_REG_CHAN] = (r | RADIO_REG_CHAN_SPACE_100)
        self.saveRegister(RADIO_REG_CHAN)

    def term(self):
        # Terminates all receiver functions
        self.setVolume(0)
        self.registers[RADIO_REG_CTRL] = 0x0000
        self.saveRegisters

    def setBassBoost(self, switchOn):
        # Switches bass boost to true or false
        self.bassBoost = switchOn
        regCtrl = self.registers[RADIO_REG_CTRL]
        if switchOn:
            regCtrl = regCtrl | RADIO_REG_CTRL_BASS
        else:
            regCtrl = regCtrl & (~RADIO_REG_CTRL_BASS)
        self.registers[RADIO_REG_CTRL] = regCtrl
        self.saveRegister(RADIO_REG_CTRL)

    def setMono(self, switchOn):
        # Switches mono to 0 or 1
        self.mono = switchOn
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEK)
        if switchOn:
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_MONO
        else:
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_MONO)
        self.saveRegister(RADIO_REG_CTRL)

    def setMute(self, switchOn):
        # Switches mute off or on
        self.mute = switchOn
        if (switchOn):
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_UNMUTE)
        else:
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_UNMUTE
        self.saveRegister(RADIO_REG_CTRL)

    def setSoftMute(self, switchOn):
        # Switches soft mute off or on
        self.softMute = switchOn
        if switchOn:
            self.registers[RADIO_REG_R4] = self.registers[RADIO_REG_R4] | RADIO_REG_R4_SOFTMUTE
        else:
            self.registers[RADIO_REG_R4] = self.registers[RADIO_REG_R4] & (~RADIO_REG_R4_SOFTMUTE)
        self.saveRegister(RADIO_REG_R4)

    def softReset(self):
        # Soft reset chip
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_RESET
        self.saveRegister(RADIO_REG_CTRL)
        time.sleep(2)
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_RESET)
        self.saveRegister(RADIO_REG_CTRL)

    def seekUp(self):
        # Start seek mode upwards
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_SEEKUP
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_SEEK
        self.saveRegister(RADIO_REG_CTRL)

        # Wait until scan is over
        time.sleep(1)
        self.getFreq()
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEK)
        self.saveRegister(RADIO_REG_CTRL)

    def seekDown(self):
        # Start seek mode downwards
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEKUP)
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_SEEK
        self.saveRegister(RADIO_REG_CTRL)

        # Wait until scan is over
        time.sleep(1)
        self.getFreq()
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEK)
        self.saveRegister(RADIO_REG_CTRL)

    def setVolume(self, volume):
        # Sets the volume
        if (volume > self.maxvolume):
            volume = self.maxvolume
        self.volume = volume
        self.registers[RADIO_REG_VOL] = self.registers[RADIO_REG_VOL] & (~RADIO_REG_VOL_VOL)
        self.registers[RADIO_REG_VOL] = self.registers[RADIO_REG_VOL] | volume
        self.saveRegister(RADIO_REG_VOL)

    def checkRDS(self):
        # Check for rds data
        self.checkThreshold()
        if self.sendRDS and self.rdsReady:
            self.registers[RADIO_REG_RA] = self.read16()

            if (self.registers[RADIO_REG_RA] & RADIO_REG_RA_RDS):
                # Check for new RDS data available
                result = False

                self.writeBytes(bytes([RADIO_REG_RDSA]))

                newData = self.read16()
                if newData != self.registers[RADIO_REG_RDSA]:
                    self.registers[RADIO_REG_RDSA] = newData
                    result = True

                newData = self.read16()
                if newData != self.registers[RADIO_REG_RDSB]:
                    self.registers[RADIO_REG_RDSB] = newData
                    result = True

                newData = self.read16()
                if newData != self.registers[RADIO_REG_RDSC]:
                    self.registers[RADIO_REG_RDSC] = newData
                    result = True

                newData = self.read16()
                if newData != self.registers[RADIO_REG_RDSD]:
                    self.registers[RADIO_REG_RDSD] = newData
                    result = True

                if result:
                    self.sendRDS(self.registers[RADIO_REG_RDSA], self.registers[RADIO_REG_RDSB],
                                 self.registers[RADIO_REG_RDSC], self.registers[RADIO_REG_RDSD])

    def checkThreshold(self):
        # Check every interval if the signal strength is strong enough for receiving rds data
        currentTime = time.monotonic()
        if (currentTime - self.initial) > self.interval:
            if self.getRssi() >= self.rdsThreshold:
                self.rdsReady = True
            else:
                self.rdsReady = False
            self.initial = currentTime

    def getRssi(self):
        # Get the current signal strength
        self.writeBytes(bytes([RADIO_REG_RB]))
        self.registers[RADIO_REG_RB] = self.read16()
        self.rssi = self.registers[RADIO_REG_RB] >> 10
        return self.rssi

    def getRadioInfo(self):
        # Reads info from chip and saves it into virtual memory
        self.readRegisters()
        if self.registers[RADIO_REG_RA] & RADIO_REG_RA_RDS:
            self.rds = True
        self.rssi = self.registers[RADIO_REG_RB] >> 10
        if self.registers[RADIO_REG_RB] & RADIO_REG_RB_FMTRUE:
            self.tuned = True
        if self.registers[RADIO_REG_CTRL] & RADIO_REG_CTRL_MONO:
            self.mono = True

    def saveRegister(self, regN):
        # Write register from memory to receiver
        regVal = self.registers[regN]  # 16 bit value in list
        regVal1 = regVal >> 8
        regVal2 = regVal & 255

        self.writeBytes(bytes([regN, regVal1, regVal2]))  # regN is a register address

    def writeBytes(self, values):
        with self.board:
            self.board.write(values)

    def saveRegisters(self):
        for i in range(2, 7):
            self.saveRegister(i)

    def read16(self):
        # Reads two bytes, returns as one 16 bit integer
        with self.board:
            result = bytearray(2)
            self.board.readinto(result)
        return result[0] * 256 + result[1]

    def readRegisters(self):
        # Reads register from chip to virtual memory
        with self.board:
            self.board.write(bytes([RADIO_REG_RA]))
            for i in range(6):
                self.registers[0xA + i] = self.read16()


def replaceElement(index, text, newchar):
    # Replaces char in string at index with newchar
    newlist = list(text)
    if type(newchar) is int:
        if newchar < 127 and newchar > 31:
            newlist[index] = chr(newchar)
        else:
            newlist[index] = " "
    else:
        newlist[index] = newchar
    return "".join(newlist)


class RDSParser:
    """
    A class used for parsing rds data into readable strings
    """

    def __init__(self):
        # RDS Values
        self.rdsGroupType = None
        # Traffic programme
        self.rdsTP = None
        # Program type
        self.rdsPTY = None
        # RDS text chars get stored here
        self.textAB = None
        self.last_textAB = None
        # Time
        self.lastMinutes1 = 0
        self.lastMinutes2 = 0
        # Previous index
        self.lastTextIDX = 0
        # Functions initialization
        self.sendServiceName = None
        self.sendText = None
        self.sendTime = None
        # Radio text
        self.RDSText = " " * 66
        # Station names
        self.PSName1 = "--------"
        self.PSName2 = self.PSName1
        self.programServiceName = "        "

    def init(self):
        self.RDSText = " " * 66
        self.PSName1 = "--------"
        self.PSName2 = self.PSName1
        self.programServiceName = "        "
        self.lastTextIDX = 0

    def attachServicenNameCallback(self, newFunction):
        self.sendServiceName = newFunction

    def attachTextCallback(self, newFunction):
        self.sendText = newFunction

    def attachTimeCallback(self, newFunction):
        self.sendTime = newFunction

    def processData(self, block1, block2, block3, block4):

        # Analyzing block 1
        if block1 == 0:
            # If block1 set to zero, reset all RDS info
            self.init()
            if self.sendServiceName:
                self.sendServiceName(self.programServiceName)
            if self.sendText:
                self.sendText("")
            return 0

        # Block 2
        rdsGroupType = 0x0A | ((block2 & 0xF000) >> 8) | ((block2 & 0x0800) >> 11)
        self.rdsTP = block2 & 0x0400
        self.rdsPTY = block2 & 0x0400

        # rdsGroupType cases
        if rdsGroupType == 0x0A:
            pass

        elif rdsGroupType == 0x0B:
            # Data received is part of Service Station name
            idx = 2 * (block2 & 0x0003)

            c1 = block4 >> 8
            c2 = block4 & 0x00FF

            # Check that the data was successfuly received
            if ((self.PSName1[idx] == c1) and (self.PSName1[idx + 1] == c2)):
                self.PSName2 = replaceElement(idx, self.PSName2, c1)
                self.PSName2 = replaceElement(idx + 1, self.PSName2, c2)
                if (idx == 6) and (self.PSName2 == self.PSName1):
                    if self.programServiceName != self.PSName2:
                        # Publish station name
                        self.programServiceName = self.PSName2
                        if self.sendServiceName:
                            self.sendServiceName(self.programServiceName)

            if (self.PSName1[idx] != c1) or (self.PSName1[idx + 1] != c2):
                self.PSName1 = replaceElement(idx, self.PSName1, c1)
                self.PSName1 = replaceElement(idx + 1, self.PSName1, c2)

        elif rdsGroupType == 0x2A:
            time.sleep(0.1)
            self.textAB = block2 & 0x0010
            idx = 4 * (block2 & 0x000F)
            if idx < self.lastTextIDX:
                if (self.sendText):
                    self.sendText(self.RDSText)
            self.lastTextIDX = idx

            if (self.textAB != self.last_textAB):
                # Clear buffer
                self.last_textAB = self.textAB
                self.RDSText = " " * 66

            self.RDSText = replaceElement(idx, self.RDSText, block3 >> 8)
            idx += 1
            self.RDSText = replaceElement(idx, self.RDSText, block3 & 0x00FF)
            idx += 1
            self.RDSText = replaceElement(idx, self.RDSText, block4 >> 8)
            idx += 1
            self.RDSText = replaceElement(idx, self.RDSText, block4 & 0x00FF)
            idx += 1
        elif rdsGroupType == 0x4A:
            time.sleep(0.1)
            off = (block4) & 0x3F
            mins = (block4 >> 6) & 0x3F
            mins += 60 * (((block3 & 0x0001) << 4) | ((block4 >> 12) & 0x0F))
            if off & 0x20:
                mins -= 30 * (off & 0x1F)
            else:
                mins += 30 * (off & 0x1F)

            # Check if function sendTime was set, and chek if the time is different from last time
            if (self.sendTime) and (mins != self.lastMinutes1):
                # Checks if time appeared in the last two instances - To avoid noise
                if self.lastMinutes1 + 1 == mins or self.lastMinutes2 + 1 == mins or self.lastMinutes1 == 0 or self.lastMinutes2 == 0:
                    self.lastMinutes2 = self.lastMinutes1
                    self.lastMinutes1 = mins
                    self.sendTime(mins // 60, mins % 60)
