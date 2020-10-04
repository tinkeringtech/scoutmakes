from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.accelerometer_packet import AccelerometerPacket
from adafruit_bluefruit_connect.magnetometer_packet import MagnetometerPacket
from adafruit_bluefruit_connect.gyro_packet import GyroPacket
from adafruit_bluefruit_connect.quaternion_packet import QuaternionPacket

import time
import board
import pulseio

pin1 = pulseio.PWMOut(board.D5, frequency=60000, duty_cycle=0)
pin2 = pulseio.PWMOut(board.D6, frequency=10000, duty_cycle=0)
pin3 = pulseio.PWMOut(board.D9, frequency=60000, duty_cycle=0)
pin4 = pulseio.PWMOut(board.D10, frequency=10000, duty_cycle=0)

ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

while True:
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass

    # Now we're connected

    while ble.connected:
        if uart.in_waiting:
            packet = Packet.from_stream(uart)
            if isinstance(packet, AccelerometerPacket):
                x = packet.x
                y = packet.y
                #print (y)
                if x<-1.5:
                        pin1.duty_cycle = int(60000)
                        pin2.duty_cycle = int(30000)
                        pin3.duty_cycle = int(30000)
                        pin4.duty_cycle = int(60000)
                elif x>1.5:
                        pin1.duty_cycle = int(30000)
                        pin2.duty_cycle = int(60000)
                        pin3.duty_cycle = int(60000)
                        pin4.duty_cycle = int(30000)
                elif y<-1.5:
                        pin1.duty_cycle = int(60000)
                        pin2.duty_cycle = int(30000)
                        pin3.duty_cycle = int(60000)
                        pin4.duty_cycle = int(10000)
                        #time.sleep(0.01)
                        #print ("less")
                elif y>1.5:
                        pin1.duty_cycle = int(10000)
                        pin2.duty_cycle = int(60000)
                        pin3.duty_cycle = int(30000)
                        pin4.duty_cycle = int(60000)
                        #time.sleep(0.01)
                        #print ("more")
                elif y<1.5 and y>-1.5:
                        pin1.duty_cycle = int(60000)
                        pin2.duty_cycle = int(60000)
                        pin3.duty_cycle = int(60000)
                        pin4.duty_cycle = int(60000)
                elif x<1.5 and x>-1.5:
                        pin1.duty_cycle = int(60000)
                        pin2.duty_cycle = int(60000)
                        pin3.duty_cycle = int(60000)
                        pin4.duty_cycle = int(60000)