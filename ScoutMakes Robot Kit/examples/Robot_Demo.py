from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.accelerometer_packet import AccelerometerPacket
from adafruit_bluefruit_connect.magnetometer_packet import MagnetometerPacket
from adafruit_bluefruit_connect.gyro_packet import GyroPacket
from adafruit_bluefruit_connect.quaternion_packet import QuaternionPacket
from adafruit_bluefruit_connect.button_packet import ButtonPacket

import time
import board
import pulseio
import neopixel
import simpleio
import busio
import terminalio
from digitalio import DigitalInOut, Direction, Pull

from adafruit_display_text import label
import adafruit_displayio_ssd1306
import displayio
# Display
displayio.release_displays()

# Initialize i2c bus
i2c = busio.I2C(board.SCL, board.SDA)

display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)
oled_text = "Robot Ready!"

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
    text_area_1 = label.Label(terminalio.FONT, text=oled_text, color=0xFFFF00, x=30, y=15)
    splash.append(text_area_1)

pixel_pin = board.D12  #Pin that the NEOPIXELS are attached to.
num_pixels = 4

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.3, auto_write=False)

RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)

def color_chase(color, wait):
    for i in range(num_pixels):
        pixels[i] = color
        time.sleep(wait)
        pixels.show()
    time.sleep(0.5)

# Define pin connected to piezo buzzer.
PIEZO_PIN = board.D11

# Define a list of tones/music notes to play on the buzzer.
TONE_FREQ = [ 262,  # C4
              294,  # D4
              330,  # E4
              349,  # F4
              392,  # G4
              440,  # A4
              494 ] # B4

#motor pin definitions
motor1A = DigitalInOut(board.D5)
motor1B = DigitalInOut(board.D6)
motor2A = DigitalInOut(board.D9)
motor2B = DigitalInOut(board.D10)

motor1A.direction = Direction.OUTPUT
motor1B.direction = Direction.OUTPUT
motor2A.direction = Direction.OUTPUT
motor2B.direction = Direction.OUTPUT

ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)
while True:
    drawText("")  #Robot ready splash
    pixels.fill(BLUE)
    pixels.show()
    ble.start_advertising(advertisement)

    while not ble.connected:
        pass

    # Now we're connected

    while ble.connected:
        if uart.in_waiting:
            packet = Packet.from_stream(uart)
            if isinstance(packet, ButtonPacket) and packet.pressed:

                if packet.button == ButtonPacket.RIGHT:  #RIGHT
                        pixels.fill(BLUE)
                        pixels.show()
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[5], duration=0.05)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[4], duration=0.1)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[0], duration=0.05)
                        motor1A.value = False
                        motor1B.value = True
                        motor2A.value = False
                        motor2B.value = True

                elif packet.button == ButtonPacket.LEFT:  # LEFT
                        pixels.fill(YELLOW)
                        pixels.show()
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[6], duration=0.05)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[5], duration=0.1)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[0], duration=0.05)
                        motor1A.value = True
                        motor1B.value = False
                        motor2A.value = True
                        motor2B.value = False

                elif packet.button == ButtonPacket.UP:  # FORWARD
                        pixels.fill(GREEN)
                        pixels.show()
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[2], duration=0.1)
                        motor1A.value = False
                        motor1B.value = True
                        motor2A.value = True
                        motor2B.value = False

                elif packet.button == ButtonPacket.DOWN:  # REVERSE
                        pixels.fill(RED)
                        pixels.show()
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[3], duration=0.1)
                        motor1A.value = True
                        motor1B.value = False
                        motor2A.value = False
                        motor2B.value = True

                elif packet.button == ButtonPacket.BUTTON_1:  # button 1
                        pixels.fill(YELLOW)
                        pixels.show()
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[6], duration=0.2)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[3], duration=0.1)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[0], duration=0.4)
                        print("released button 1")

                elif packet.button == ButtonPacket.BUTTON_2:  # button 2
                        pixels.fill(RED)
                        pixels.show()
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[0], duration=0.2)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[3], duration=0.1)
                        simpleio.tone(PIEZO_PIN, TONE_FREQ[6], duration=0.4)
                        print("released button 2")

                elif packet.button == ButtonPacket.BUTTON_3:  # button 3
                        pixels.fill(BLUE)
                        pixels.show()
                        print("released button 3")

                elif packet.button == ButtonPacket.BUTTON_4:  # button 4
                        pixels.fill(CYAN)
                        pixels.show()
                        print("released button 4")
                else:
                        pixels.fill(WHITE)
                        pixels.show()
                        print("stopped")
                        drawText("")  #Robot ready splash
                        motor1A.value = False
                        motor1B.value = False
                        motor2A.value = False
                        motor2B.value = False

            elif isinstance(packet, ButtonPacket) and not packet.pressed:
                if packet.button == ButtonPacket.RIGHT:
                    print("released right")
                    motor1A.value = False
                    motor1B.value = False
                    motor2A.value = False
                    motor2B.value = False
                if packet.button == ButtonPacket.LEFT:
                    print("released left")
                    motor1A.value = False
                    motor1B.value = False
                    motor2A.value = False
                    motor2B.value = False
                if packet.button == ButtonPacket.UP:
                    print("released forward")
                    motor1A.value = False
                    motor1B.value = False
                    motor2A.value = False
                    motor2B.value = False
                if packet.button == ButtonPacket.DOWN:
                    print("released reverse")
                    motor1A.value = False
                    motor1B.value = False
                    motor2A.value = False
                    motor2B.value = False