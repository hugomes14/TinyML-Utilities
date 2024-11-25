import os
import sys

from src.arduino import SketchConfig

ARDUINO_CLI_PATH = "arduino-cli"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM10"
SKETCH_PATH = "src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino"
FRAMES_WIDTH = 320
FRAMES_HEIGHT = 240
BAUD_RATE = 256000

arduino_settings = SketchConfig(arduino_cli_path= ARDUINO_CLI_PATH, 
                                        board= BOARD, 
                                        port= PORT, 
                                        sketch_path= SKETCH_PATH, 
                                        frames_widht= FRAMES_WIDTH,
                                        frames_height= FRAMES_HEIGHT,
                                        baud_rate= BAUD_RATE
                                       )

print(arduino_settings.available_ports())

arduino_settings.compile()

arduino_settings.upload()



print(arduino_settings.__dict__.values())