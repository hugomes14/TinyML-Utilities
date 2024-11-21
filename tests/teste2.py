import os
import sys

from src.video_capture import VideoCapture

board = "arduino:mbed_nano:nano33ble"

video_capture = VideoCapture()

video_capture.compile()

print(video_capture.__dict__.values())