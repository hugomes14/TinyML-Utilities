import os
import sys
import subprocess

ARDUINO_IDE_PATH = "C:\Users\hugo.gomes\AppData\Local\Programs\Arduino IDE"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM3"
SKETCH_PATH = "C:\Users\hugo.gomes\Desktop\DAPA\Video-Crop\src\CameraCapture.ino"

class VideoCapture:
    def __init__(self, arduino_ide_path= ARDUINO_IDE_PATH, board= BOARD, port= PORT, sketch_path= SKETCH_PATH):
        """
        Setting up the neccessary information to 
        compile and send instructions to the microcontroller 
        without using the arduino IDE
        """
        self.arduino_ide_path = arduino_ide_path
        self.board = board
        self.port = port
        self.sketch_path = sketch_path
        self.it_was_compiled = False
        
        self.validate_inputs()

   
    def validate_inputs(self):
        """Check if the provided paths and parameters are valid."""
        if not os.path.exists(self.arduino_ide_path):
            print(f"Error: Arduino IDE path '{self.arduino_ide_path}' does not exist.")
            sys.exit(1)

        if not os.path.exists(self.sketch_path):
            print(f"Error: Sketch file '{self.sketch_path}' does not exist.")
            sys.exit(1)

        if not self.board:
            print("Error: Board type is not specified.")
            sys.exit(1)

        if not self.port:
            print("Error: Port is not specified.")
            sys.exit(1)


    def compile(self):
        compile_command = [
            "arduino-cli",
            "compile",
            "--fqbn", self.board,
            self.sketch_path
        ]

        try:
            print("Compiling the sketch...")
            subprocess.run(compile_command, check=True)
            print("Compilation successful.")
            self.it_was_compiled = True
            
        except subprocess.CalledProcessError as e:
            print(f"Compilation failed with return code: {e.returncode}")
            sys.exit(1)
        
    
    def upload(self):
        
        if not self.it_was_compiled:
            self.compile()
        
        
        upload_command = [
            "arduino-cli",
            "upload",
            "-p", self.port,
            "--fqbn", self.board,
            self.sketch_path
        ]

        try:
            print("Uploading the sketch...")
            subprocess.run(upload_command, check=True)
            print("Upload successful.")
        except subprocess.CalledProcessError as e:
            print(f"Upload failed with return code: {e.returncode}")
            sys.exit(1)