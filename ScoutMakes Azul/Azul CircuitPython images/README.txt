The CircuitPython images contained in this directory are special builds to accomodate for a change in the make and model of the on-board flash memory chip on the Azul due to the chip shortage. The image at https://circuitpython.org/board/tinkeringtech_scoutmakes_azul/ is the original image based on the GD25Q16C whereas the new memory chip is the W25Q16JVxQ.

Instructions on building CircuitPython from Adafruit https://learn.adafruit.com/building-circuitpython/linux

In order to accomodate this change, the below change was made to the CircuitPython source code prior to building. Note the change in EXTERNAL_FLASH_DEVICES = "W25Q16JVxQ" for this new chip.

circuitpython/ports/nrf/boards/tinkeringtech_scoutmakes_azul/mpconfigboard.mk

USB_VID = 0x239A
USB_PID = 0x80BE
USB_PRODUCT = "TinkeringTech ScoutMakes Azul"
USB_MANUFACTURER = "TinkeringTech LLC"

MCU_CHIP = nrf52840

QSPI_FLASH_FILESYSTEM = 1
EXTERNAL_FLASH_DEVICES = "W25Q16JVxQ"


