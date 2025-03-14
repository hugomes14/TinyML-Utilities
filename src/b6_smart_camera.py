import socket
import io
import threading
from PIL import Image
import numpy as np
import cv2
import datetime
import logging
import time
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Desired window dimensions (width, height)
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
COMMAND = '<LIMA DIR="Request" CMD="Project_GetImage" TYPE="BMP" PATH="Module Application.Smart Camera.Image Monochrome.Grey"/>'
IP = "192.168.249.50"
PORT = 33040

class SmartCamera:
    def __init__(self, ip=IP, port=PORT, file_name='', fps=20, window_width=WINDOW_WIDTH, window_height=WINDOW_HEIGHT, command=COMMAND):
        self.ip = ip
        self.port = port
        self.filename = file_name
        self.fps = fps
        self.window_width = window_width
        self.window_height = window_height
        self.command = command
        self.prev_time = time.time()
        self.real_fps = 0
        self.fps_media = []
        self.time_beggin = time.time()

        # Validate IP and port
        if not self.is_valid_ip(ip):
            raise ValueError(f"Invalid IP address: {ip}")
        if not (0 < port < 65536):
            raise ValueError(f"Invalid port number: {port}")

    def is_valid_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def set_up_writer(self):
        if self.filename:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            name = f"{self.filename}_{timestamp}.avi"
            return cv2.VideoWriter(name, fourcc, self.fps, (self.window_width, self.window_height), isColor=True)
        return None

    def connection(self):
        try:
            # Set up the socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.info("Connecting to camera...")
            sock.connect((self.ip, self.port))
            logging.info("Connected to camera.")

            video_writer = self.set_up_writer()

            # Start thread for reading frames
            stop_event = threading.Event()
            frame_queue = queue.Queue(maxsize=10)  # Queue for frame sharing
            thread = threading.Thread(target=self.stream_video, args=(sock, video_writer, stop_event, frame_queue))
            thread.start()

            # OpenCV window setup
            cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Video Stream", self.window_width, self.window_height)

            while not stop_event.is_set():
                try:
                    # Get frame from the queue
                    frame = frame_queue.get(timeout=0.1)  # Wait briefly for a frame
                    if frame is not None:
                        cv2.imshow("Video Stream", frame)
                    else:
                        logging.warning("No frame available for display.")
                except queue.Empty:
                    continue

                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logging.info(sum(self.fps_media)/len(self.fps_media))
                    stop_event.set()

            thread.join()
            cv2.destroyAllWindows()
            sock.close()
            if video_writer:
                video_writer.release()
                logging.info(f"Video saved as {self.filename}")

        except Exception as e:
            logging.error(f"Error in connection: {e}")

    def stream_video(self, sock, video_writer, stop_event, frame_queue):
        try:
            while not stop_event.is_set():
                frame = self.take_frame(sock)
                if frame is not None:
                    frame = cv2.resize(frame, (self.window_width, self.window_height))
                    frame_queue.put(frame)  # Add frame to the queue
                    if video_writer:
                            video_writer.write(frame)
                else:
                    logging.warning("Failed to retrieve frame.")
        except Exception as e:
            logging.error(f"Error in video streaming: {e}")

    def take_frame(self, sock):
        try:
            # Send the LIMA command to get a BMP image
            sock.send(self.command.encode())

            # Receive the response header
            response_header = sock.recv(62)

            # Extract DATALEN value
            header_str = response_header.decode(errors='ignore')
            data_length_start = header_str.find('DATALEN="') + len('DATALEN="')
            data_length_end = header_str.find('"', data_length_start)
            data_length = int(header_str[data_length_start:data_length_end])

            # Receive the image data
            image_data = bytearray(data_length)
            view = memoryview(image_data)

            while data_length > 0:
                n_bytes = sock.recv_into(view, min(4096, data_length))
                view = view[n_bytes:]
                data_length -= n_bytes

            # Convert image data to OpenCV format
            image_io = io.BytesIO(image_data)
            pil_image = Image.open(image_io)
            frame = np.array(pil_image)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            self.current_time = time.time()
            self.real_fps = 1 / (self.current_time - self.prev_time)
            self.fps_media.append(self.real_fps)
            self.prev_time = self.current_time
            
            cv2.putText(frame, f"Relative time: {(self.real_fps):.5f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            return frame
        except Exception as e:
            logging.error(f"Error in frame retrieval: {e}")
            return None

# Example usage
if __name__ == "__main__":
    camera = SmartCamera(file_name="output_video")
    camera.connection()



