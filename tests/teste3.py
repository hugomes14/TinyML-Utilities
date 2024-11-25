import os
import sys

from src.arduino import VideoCapture, SketchConfig

ARDUINO_CLI_PATH = "arduino-cli"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM10"
SKETCH_PATH = "src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino"
FRAMES_WIDTH = 320
FRAMES_HEIGHT = 240
BAUD_RATE = 256000
BYTES_PER_PIXEL = 1
FPS= 1
FILE_NAME = "Output"

arduino_settings = SketchConfig(arduino_cli_path= ARDUINO_CLI_PATH, 
                                        board= BOARD, 
                                        port= PORT, 
                                        sketch_path= SKETCH_PATH, 
                                        frames_widht= FRAMES_WIDTH,
                                        frames_height= FRAMES_HEIGHT,
                                        baud_rate= BAUD_RATE)

#print(arduino_settings.available_ports())

#arduino_settings.compile()

#arduino_settings.upload()

#if the filename is empty no capture will be saved
video = VideoCapture(port= PORT, baud_rate= BAUD_RATE, 
                    width= FRAMES_WIDTH, height= FRAMES_HEIGHT,
                    bytes_per_pixel= BYTES_PER_PIXEL, fps= FPS, filename="")



video.capture()

