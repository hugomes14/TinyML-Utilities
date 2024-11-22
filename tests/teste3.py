import os
import sys

from src.video_capture import VideoCapture

ARDUINO_CLI_PATH = "arduino-cli"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM3"
SKETCH_PATH = "src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino"
FRAMES_WIDTH = 320
FRAMES_HEIGHT = 240
BAUD_RATE = 256000
BYTES_PER_PIXEL = 1
FPS= 1
FILE_NAME = "Output"

video = VideoCapture(port= PORT, baud_rate= BAUD_RATE, 
                    width= FRAMES_WIDTH, height= FRAMES_HEIGHT,
                    bytes_per_pixel= BYTES_PER_PIXEL, record= False)

video.video_settings(fps= FPS, video_filename= FILE_NAME)

print(video.__dict__.items())