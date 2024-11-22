import os
import sys

from src.video_capture import ArduinoSketchConfig

ARDUINO_CLI_PATH = "arduino-cli"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM3"
SKETCH_PATH = "src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino"
FRAMES_WIDTH = 320
FRAMES_HEIGHT = 240
BAUD_RATE = 256000

arduino_settings = ArduinoSketchConfig(arduino_cli_path= ARDUINO_CLI_PATH, 
                                        board= BOARD, 
                                        port= PORT, 
                                        sketch_path= SKETCH_PATH, 
                                        frames_widht= FRAMES_WIDTH,
                                        frames_height= FRAMES_HEIGHT,
                                        baud_rate= BAUD_RATE
                                       )

arduino_settings.compile()

#arduino_settings.upload()

#For a simpler way, uncomment the following line
#arduino_settings.dummy_compile_and_upload()

print(arduino_settings.__dict__.values())