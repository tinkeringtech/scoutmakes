# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 tinkeringtech for TinkeringTech LLC
#
# SPDX-License-Identifier: Unlicense

# pylint: disable=global-statement, too-many-branches, too-many-statements
import time
import board
import busio
import supervisor
from adafruit_bus_device.i2c_device import I2CDevice
import tinkeringtech_rda5807m

presets = [8930, 9510, 9710, 9950, 10100, 10110, 10650]  # Preset stations
i_sidx = 3  # Starting at station with index 3

# Initialize i2c bus
i2c = busio.I2C(board.SCL, board.SDA)

# Receiver i2c communication
address = 0x11
vol = 3  # Default volume
band = "FM"

rds = tinkeringtech_rda5807m.RDSParser()

# Display initialization
initial_time = time.monotonic()  # Initial time - used for timing
toggle_frequency = (
    5  # Frequency at which the text changes between radio frequnecy and rds in seconds
)

rdstext = "No rds data"

# RDS text handle
def textHandle(rdsText):
    global rdstext
    rdstext = rdsText
    print(rdsText)


rds.attach_text_callback(textHandle)

# Initialize the radio classes for use.
radio_i2c = I2CDevice(i2c, address)
radio = tinkeringtech_rda5807m.Radio(radio_i2c, rds, presets[i_sidx], vol)
radio.set_band(band)  # Minimum frequency - 87 Mhz, max - 108 Mhz

# Read input from serial
def serial_read():
    if supervisor.runtime.serial_bytes_available:
        command = input()
        command = command.split(" ")
        cmd = command[0]
        if cmd == "f":
            value = command[1]
            runSerialCommand(cmd, int(value))
        else:
            runSerialCommand(cmd)
        time.sleep(0.3)
        print("-> ", end="")


def runSerialCommand(cmd, value=0):
    # Executes a command
    # Starts with a character, and optionally followed by an integer, if required
    global i_sidx
    if cmd == "?":
        print("? help")
        print("+ increase volume")
        print("- decrease volume")
        print("> next preset")
        print("< previous preset")
        print(". scan up ")
        print(", scan down ")
        print(
            "f direct frequency input e.g 99.50 MHz is f 9950 or 101.10 MHz is f 10110"
        )
        print("i station status")
        print("s mono/stereo mode")
        print("b bass boost")
        print("u mute/unmute")
        print("r get rssi data")
        print("e softreset chip")
        print("q stops the program")

    # Volume and audio control
    elif cmd == "+":
        v = radio.volume
        if v < 15:
            radio.set_volume(v + 1)
    elif cmd == "-":
        v = radio.volume
        if v > 0:
            radio.set_volume(v - 1)

    # Toggle mute mode
    elif cmd == "u":
        radio.set_mute(not radio.mute)
    # Toggle stereo mode
    elif cmd == "s":
        radio.set_mono(not radio.mono)
    # Toggle bass boost
    elif cmd == "b":
        radio.set_bass_boost(not radio.bass_boost)

    # Frequency control
    elif cmd == ">":
        # Goes to the next preset station
        if i_sidx < (len(presets) - 1):
            i_sidx = i_sidx + 1
            radio.set_freq(presets[i_sidx])
    elif cmd == "<":
        # Goes to the previous preset station
        if i_sidx > 0:
            i_sidx = i_sidx - 1
            radio.set_freq(presets[i_sidx])

    # Set frequency
    elif cmd == "f":
        radio.set_freq(value)

    # Seek up/down
    elif cmd == ".":
        radio.seek_up()
    elif cmd == ",":
        radio.seek_down()

    # Display current signal strength
    elif cmd == "r":
        print("RSSI: " + str(radio.get_rssi()))

    # Soft reset chip
    elif cmd == "e":
        radio.soft_reset()

    # Not in help
    elif cmd == "!":
        radio.term()

    elif cmd == "i":
        # Display chip info
        s = radio.format_freq()
        print("Station: " + s)
        print("Radio info: ")
        print("RDS -> " + str(radio.rds))
        print("TUNED -> " + str(radio.tuned))
        print("STEREO -> " + str(not radio.mono))
        print("Audio info: ")
        print("BASS -> " + str(radio.bass_boost))
        print("MUTE -> " + str(radio.mute))
        print("SOFTMUTE -> " + str(radio.soft_mute))
        print("VOLUME -> " + str(radio.volume))


print_rds = False
runSerialCommand("?", 0)

print("-> ", end="")

while True:
    serial_read()
    radio.check_rds()
    new_time = time.monotonic()
    serial_read()
