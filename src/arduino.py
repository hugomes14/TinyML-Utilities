import os
import sys
import subprocess
import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
import serial
import datetime

# Update this to point to your actual Arduino CLI path if necessary
ARDUINO_CLI_PATH = "arduino-cli"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM3"
SKETCH_PATH = "src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino"  # Point to the .ino file
FRAMES_WIDTH = 320
FRAMES_HEIGHT = 240
BAUD_RATE = 256000
BYTES_PER_PIXEL = 1
FPS = 3

class SketchConfig:
    def __init__(self, arduino_cli_path= ARDUINO_CLI_PATH, 
                board= BOARD, port= PORT, sketch_path= SKETCH_PATH,
                frames_widht= FRAMES_WIDTH, frames_height= FRAMES_HEIGHT,
                baud_rate= BAUD_RATE):
        
        self.arduino_cli_path = arduino_cli_path
        self.board = board
        self.port = port
        self.sketch_path = sketch_path
        self.frames_width = frames_widht
        self.frames_height = frames_height
        self.baud_rate = baud_rate
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
    
    def available_ports(self):
        self.ports_command = ["wmic", "path", "Win32_SerialPort", "get", "DeviceID"]
        
        try:
            return subprocess.run(self.ports_command)
        except subprocess.CalledProcessError as e:
            print(e)

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
        
        self.upload_command = [
            self.arduino_cli_path,
            "upload",
            "-p", self.port,
            "--fqbn", self.board,
            self.sketch_path
        ]

        try:
            print("Uploading the sketch...")
            subprocess.run(self.upload_command, check=True)
            print("Upload successful.")
        except subprocess.CalledProcessError as e:
            print(f"Upload failed with return code: {e.returncode}")
            sys.exit(1)
            





class VideoCapture:
    def __init__(self, port, baud_rate, width, height, bytes_per_pixel, fps=3, filename=""):
        self.port = port
        self.baud_rate = baud_rate
        self.width = width
        self.height = height
        self.bytes_per_pixel = bytes_per_pixel
        self.frame_size = self.width * self.height * self.bytes_per_pixel
        self.fps = fps
        self.filename = filename

    def set_up_writer(self):
        if self.filename:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec
            
            time = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            name = self.filename + time + ".avi"
            
            return cv2.VideoWriter(name, fourcc, self.fps, (self.width, self.height), isColor=False)
        return None

    def process_frame(self, frame_data, video_writer):
        # Convert the frame data to a new numpy array
        frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((self.height, self.width))

        if video_writer:
            video_writer.write(frame)  # Write the frame to the video

        cv2.imshow('Real-time Image from Arduino', frame)  # Display the frame

    def capture(self):
        # Set up the serial connection
        ser = serial.Serial(self.port, self.baud_rate)
        time.sleep(2)  # Wait for the connection to establish
        
        video_writer = self.set_up_writer()

        data = bytearray(self.frame_size)  # Initialize data buffer
        i = 0

        try:
            ser.write(bytes([0xC0]))  # Send command to start receiving frames
            
            while True:
                # Check if enough data is available
                if ser.in_waiting > 0:
                    incoming_data = ser.read(ser.in_waiting)
                    
                    data[i:i+len(incoming_data)] = incoming_data
                    i += len(incoming_data)
                    
                    # Process frames as long as there is enough data
                    if i >= self.frame_size:
                        data = data[:self.frame_size]
                        self.process_frame(data, video_writer)
                        i = 0
                        ser.write(bytes([0xC0]))

                # Check for key press to exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            print("Exiting...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            ser.close()  # Close the serial connection
            if video_writer:
                video_writer.release()  # Release the video writer
                print(f"Video saved as {self.filename}")
            cv2.destroyAllWindows()  # Close all OpenCV windows


