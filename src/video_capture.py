import os
import sys
import subprocess

# Update this to point to your actual Arduino CLI path if necessary
ARDUINO_CLI_PATH = "arduino-cli"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM3"
SKETCH_PATH = "C:\\Users\\hugo.gomes\\Desktop\\DAPA\\Video-Crop\\src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino"  # Point to the .ino file

class VideoCapture:
    def __init__(self, arduino_cli_path=ARDUINO_CLI_PATH, board=BOARD, port=PORT, sketch_path=SKETCH_PATH):
        self.arduino_cli_path = arduino_cli_path
        self.board = board
        self.port = port
        self.sketch_path = sketch_path
        self.it_was_compiled = False
        
        self.validate_inputs()

    def validate_inputs(self):
        """Check if the provided paths and parameters are valid."""

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
        self.compile_command = [
            self.arduino_cli_path,
            "compile",
            "--fqbn", self.board,
            self.sketch_path
        ]

        try:
            print("Compiling the sketch...")
            subprocess.run(self.compile_command, check=True)
            print("Compilation successful.")
            self.it_was_compiled = True
            
        except subprocess.CalledProcessError as e:
            print(f"Compilation failed with return code: {e.returncode}")
            sys.exit(1)


    def upload(self):
        if not self.it_was_compiled:
            self.compile()
        
        upload_command = [
            self.arduino_cli_path,
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