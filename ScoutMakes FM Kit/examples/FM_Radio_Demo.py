import time
import board
import busio
import supervisor
import displayio
import terminalio
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import tinkeringtech_rda5807m
from digitalio import DigitalInOut, Direction, Pull

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_bluefruit_connect.packet import Packet
# Only the packet classes that are imported will be known to Packet.
from adafruit_bluefruit_connect.button_packet import ButtonPacket

ble = BLERadio()
uart_service = UARTService()
advertisement = ProvideServicesAdvertisement(uart_service)

switch2 = DigitalInOut(board.D5)
switch2.direction = Direction.INPUT
switch2.pull = Pull.UP

switch1 = DigitalInOut(board.D6)
switch1.direction = Direction.INPUT
switch1.pull = Pull.UP

switch3 = DigitalInOut(board.D9)
switch3.direction = Direction.INPUT
switch3.pull = Pull.UP

switch4 = DigitalInOut(board.D10)
switch4.direction = Direction.INPUT
switch4.pull = Pull.UP

switch5 = DigitalInOut(board.D11)
switch5.direction = Direction.INPUT
switch5.pull = Pull.UP

switch6 = DigitalInOut(board.D12)
switch6.direction = Direction.INPUT
switch6.pull = Pull.UP

# Display
displayio.release_displays()

presets = [  # Preset stations
    8930,
    9510,
    9710,
    9950,
    10100,
    10110,
    10650
]
i_sidx = 3  # Starting at station with index 3

# Initialize i2c bus
i2c = busio.I2C(board.SCL, board.SDA)

# Receiver i2c communication
address = 0x11
radio_i2c = I2CDevice(i2c, address)

vol = 1  # Default volume
band = "FM"

radio = tinkeringtech_rda5807m.Radio(radio_i2c, presets[i_sidx], vol)
radio.setBand(band)  # Minimum frequency - 87 Mhz, max - 108 Mhz
rds = tinkeringtech_rda5807m.RDSParser()

# Display initialization
initial_time = time.monotonic()  # Initial time - used for timing
toggle_frequency = 5  # Frequency at which the text changes between radio frequnecy and rds in seconds
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)
rdstext = "No rds data"


def drawText(text):
    # Write text on display
    global display
    # Make the display context
    splash = displayio.Group(max_size=10)
    display.show(splash)

    color_bitmap = displayio.Bitmap(128, 32, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0x000000  # Black

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Split text into two lines
    temp = text.split(" ")
    line1 = temp[0]
    line2 = " ".join(temp[1:])
    # Check that lines are not empty
    if not line1.strip() or not line2.strip():
        warning = "Unclear rds data"
        text_area_1 = label.Label(terminalio.FONT, text=warning, color=0xFFFF00, x=5, y=5)
        splash.append(text_area_1)
    else:
        # Line 1
        text_area_1 = label.Label(terminalio.FONT, text=line1, color=0xFFFF00, x=5, y=5)
        splash.append(text_area_1)
        # Line 2
        text_area_2 = label.Label(terminalio.FONT, text=line2, color=0xFFFF00, x=5, y=20)
        splash.append(text_area_2)


# RDS text handle
def textHandle(rdsText):
    global rdstext
    rdstext = rdsText
    print(rdsText)


rds.attachTextCallback(textHandle)


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
    global presets
    if cmd == "?":
        print("? help")
        print("+ increase volume")
        print("- decrease volume")
        print("> next preset")
        print("< previous preset")
        print(". scan up ")
        print(", scan down ")
        print("f direct frequency input")
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
            radio.setVolume(v + 1)
    elif cmd == "-":
        v = radio.volume
        if v > 0:
            radio.setVolume(v - 1)

    # Toggle mute mode
    elif cmd == "u":
        radio.setMute(not radio.mute)
    # Toggle stereo mode
    elif cmd == "s":
        radio.setMono(not radio.mono)
    # Toggle bass boost
    elif cmd == "b":
        radio.setBassBoost(not radio.bassBoost)

    # Frequency control
    elif cmd == ">":
        # Goes to the next preset station
        if i_sidx < (len(presets) - 1):
            i_sidx = i_sidx + 1
            radio.setFreq(presets[i_sidx])
    elif cmd == "<":
        # Goes to the previous preset station
        if i_sidx > 0:
            i_sidx = i_sidx - 1
            radio.setFreq(presets[i_sidx])

    # Set frequency
    elif cmd == "f":
        radio.setFreq(value)

    # Seek up/down
    elif cmd == ".":
        radio.seekUp()
    elif cmd == ",":
        radio.seekDown()

    # Display current signal strength
    elif cmd == "r":
        print("RSSI: " + str(radio.getRssi()))

    # Soft reset chip
    elif cmd == "e":
        radio.softReset()

    # Not in help
    elif cmd == "!":
        radio.term()

    elif cmd == "i":
        # Display chip info
        s = radio.formatFreq()
        print("Station: " + s)
        print("Radio info: ")
        print("RDS -> " + str(radio.rds))
        print("TUNED -> " + str(radio.tuned))
        print("STEREO -> " + str(not radio.mono))
        print("Audio info: ")
        print("BASS -> " + str(radio.bassBoost))
        print("MUTE -> " + str(radio.mute))
        print("SOFTMUTE -> " + str(radio.softMute))
        print("VOLUME -> " + str(radio.volume))


print_rds = False
radio.sendRDS = rds.processData
runSerialCommand("?", 0)

print("-> ", end="")

while True:

    ble.start_advertising(advertisement)

    while ble.connected:
        if uart_service.in_waiting:
            # Packet is arriving.
            packet = Packet.from_stream(uart_service)
            if isinstance(packet, ButtonPacket) and packet.pressed:
                if packet.button == ButtonPacket.RIGHT:  # UP button pressed
                    radio.seekUp()
                elif packet.button == ButtonPacket.LEFT:  # DOWN button pressed
                    radio.seekDown()
                elif packet.button == ButtonPacket.BUTTON_1:  # BUTTON 1 button pressed
                    # Goes to the next preset station
                    if i_sidx < (len(presets) - 1):
                        i_sidx = i_sidx + 1
                        radio.setFreq(presets[i_sidx])
                    elif i_sidx == 6:
                        i_sidx = 0
                        radio.setFreq(presets[i_sidx])
                elif packet.button == ButtonPacket.BUTTON_2:  # BUTTON 2 button pressed
                    radio.setMute(not radio.mute)
                elif packet.button == ButtonPacket.BUTTON_3:  # BUTTON 3 button pressed
                    # Goes preset station 2
                    radio.setFreq(presets[2])
                elif packet.button == ButtonPacket.BUTTON_4:  # BUTTON 4 button pressed
                    # Goes preset station 4
                    radio.setFreq(presets[4])
                elif packet.button == ButtonPacket.UP:  # UP button pressed
                    v = radio.volume
                    if v < 15:
                        radio.setVolume(v + 1)
                elif packet.button == ButtonPacket.DOWN:  # DOWN button pressed
                    v = radio.volume
                    if v > 0:
                        radio.setVolume(v - 1)
        serial_read()
        radio.checkRDS()
        new_time = time.monotonic()
        if (new_time - initial_time) > toggle_frequency:
            print_rds = not print_rds
            if print_rds:
                if rdstext == "":
                    drawText("No rds data")
                else:
                    if len(rdstext.split(" ")) > 1:
                        drawText(rdstext)
                    else:
                        drawText("Unclear rds data")
            else:
                drawText(radio.formatFreq())
            initial_time = new_time

    while not ble.connected:
        # Wait for a connection.
        # Main loop
        if not switch1.value:
            print("Seek Up pressed - button 1")
            radio.seekUp()
        time.sleep(0.01)  # debounce delay

        if not switch2.value:
            print("Seek Down pressed - button 2")
            radio.seekDown()
        time.sleep(0.01)  # debounce delay

        if not switch3.value:
            print("mute pressed - button 3")
            radio.setMute(not radio.mute)
        time.sleep(0.01)  # debounce delay

        if not switch4.value:
            print("Preset up pressed - button 4")
            # Goes to the next preset station

            print (i_sidx)
            if i_sidx < (len(presets) - 1):
                i_sidx = i_sidx + 1
                radio.setFreq(presets[i_sidx])

            elif i_sidx == 6:
                i_sidx = 0
                radio.setFreq(presets[i_sidx])
        time.sleep(0.01)  # debounce delay

        if not switch5.value:
            print("Volume Up pressed - button 5")
            v = radio.volume
            if v < 15:
                radio.setVolume(v + 1)
        time.sleep(0.08)  # debounce delay

        if not switch6.value:
            print("Volume Down pressed - button 6")
            v = radio.volume
            if v > 0:
                radio.setVolume(v - 1)
        time.sleep(0.01)  # debounce delay


        serial_read()
        radio.checkRDS()
        new_time = time.monotonic()
        if (new_time - initial_time) > toggle_frequency:
            print_rds = not print_rds
            if print_rds:
                if rdstext == "":
                    drawText("No rds data")
                else:
                    if len(rdstext.split(" ")) > 1:
                        drawText(rdstext)
                    else:
                        drawText("Unclear rds data")
            else:
                drawText(radio.formatFreq())
            initial_time = new_time