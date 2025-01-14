import socket
import io
from PIL import Image
import numpy as np
import cv2
import time
import math
import datetime

# Desired window dimensions (width, height)
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
COMMAND = '<LIMA DIR="Request" CMD="Project_GetImage" TYPE="BMP" PATH="Module Application.Smart Camera.Image Monochrome.Grey"/>'
IP = "xxx.xxx.xxx.xxx"
PORT = 33040

class SmartCamera:
    def __init__(self, ip = IP, port = PORT, file_name= '', fps = 20, window_width = WINDOW_WIDTH, window_height= WINDOW_HEIGHT, comand= COMMAND):
        self.ip = ip
        self.port = port
        self.filename = file_name
        self.fps = fps 
        self.window_width = window_width
        self.window_height = window_height
        self.comand = comand
    
    def set_up_writer(self):
        if self.filename:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec
            
            time = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            name = self.filename + time + ".avi"
            
            return cv2.VideoWriter(name, fourcc, self.fps, (self.window_width, self.window_height), isColor=False)
        return None  
    
    def connection(self):
        # Set up the socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.ip, self.port))

        video_writer = self.set_up_writer()
        
        # OpenCV window setup
        cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Video Stream", self.window_width, self.window_height)

        try:
            while True:
                # Capture a frame
                frame = self.take_frame(sock)
                if frame is not None:
                    
                    frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
                    cv2.imshow("Video Stream", frame)

                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            cv2.destroyAllWindows()
            sock.close()
            if video_writer:
                video_writer.release()  # Release the video writer
                print(f"Video saved as {self.filename}")
        

    def take_frame(self, sock):
        
        # Send the LIMA command to get a BMP image
        sock.send(self.command.encode())

        # Receive the response header
        response_header = sock.recv(62)

        # Extract DATALEN value
        header_str = response_header.decode(errors='ignore')
        try:
            data_length_start = header_str.find('DATALEN="') + len('DATALEN="')
            data_length_end = header_str.find('"', data_length_start)
            data_length = int(header_str[data_length_start:data_length_end])
        except ValueError:
            return None

        # Receive the image data
        image_data = bytearray(data_length)
        view = memoryview(image_data)
        
        while data_length > 0:
            n_bytes = sock.recv_into(view, min(4096, data_length))
            view = view[n_bytes:]
            data_length -= n_bytes

        # Convert image data to OpenCV format
        try:
            image_io = io.BytesIO(image_data)
            pil_image = Image.open(image_io)
            frame = np.array(pil_image)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception:
            return None





