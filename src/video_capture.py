import os
import sys
import subprocess
import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
import serial


# Update this to point to your actual Arduino CLI path if necessary
ARDUINO_CLI_PATH = "arduino-cli"
BOARD = "arduino:mbed_nano:nano33ble"
PORT = "COM3"
SKETCH_PATH = "src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino"  # Point to the .ino file
FRAMES_WIDTH = 320
FRAMES_HEIGHT = 240
BAUD_RATE = 256000
BYTES_PER_PIXEL = 1

class ArduinoSketchConfig:
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
            
    def dummy_compile_and_upload(self):
        
        self.compile()
        time.sleep(1)
        self.upload()
        
    


class VideoCapture:
    def __init__(self, port= PORT, baud_rate= BAUD_RATE, 
                width= FRAMES_WIDTH, height= FRAMES_HEIGHT, 
                bytes_per_pixel= BYTES_PER_PIXEL, record= False):
        self.port = port
        self.baud_rate = baud_rate
        self.width = width
        self.height = height
        self.bytes_per_pixel = bytes_per_pixel
        self.frame_size = self.width * self.height * self.bytes_per_pixel
        self.record = record
        
        
    
    def inicialize_serial_communication(self):
        self.ser = serial.Serial(self.port, self.baud_rate)
        time.sleep(2)
        
        
    def close_serial_communication(self):
        try:
            self.ser.close()
        except serial.SerialException:
            raise serial.SerialException


    def video_settings(self, fps, video_filename):
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.fps = fps
        self.video_filename = str(video_filename) + str(time.time()) + ".avi"
        return(f"The video will be recorded at {self.fps} fps and will be named {self.video_filename}")
 
    
    def video_recorder(self):
        self.video_writer = cv2.VideoWriter(self.video_filename, self.fourcc, self.fps, (self.width, self.height), isColor=False)

   
 
    def live(self):
        
        if self.record:
            self.video_recorder()
            
        plt.ion()  # Turn on interactive mode
        fig, ax = plt.subplots()
        img = ax.imshow(np.zeros((self.height, self.width)), cmap='gray', vmin=0, vmax=255)  # Create an empty image
        ax.set_title("Real-time Image from Arduino")
        data = bytearray()
        try:
            self.ser.write(bytes([0xC0]))  # Send command to start receiving frames
            
            while True:
                # Check if enough data is available
                if self.ser.in_waiting > 0:
                    # Read available data
                    incoming_data = self.ser.read(self.ser.in_waiting)
                    data += incoming_data
                    
                    # Process frames as long as there is enough data
                    if len(data) >= self.frame_size:
                        # Extract the frame data
                        frame_data = data[:self.frame_size]
                        data = data.clear()

                        # Convert the frame data to a numpy array
                        frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((self.height, self.width))
                        
                        # Write the frame to the video
                        if self.record:
                            self.video_writer.write(frame)
                        # Update the image
                        img.set_array(frame)
                        plt.draw()
                        #plt.pause(0.001)  # Keep this low for responsiveness

        except KeyboardInterrupt:
            print("Exiting...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            #plt.close(fig)  # Close the figure
            self.close_serial_communication()  # Close the serial connection
            if self.record:
                self.video_writer.release()  # Release the video writer

