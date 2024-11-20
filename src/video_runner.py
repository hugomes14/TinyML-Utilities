import cv2
import os
import matplotlib.pyplot as plt
import numpy as np

class VideoRunner:
    def __init__(self, video_name, dir):
        self.name = video_name
        self.dir = os.path.join(dir, self.name)
        
        self.video = cv2.VideoCapture(self.dir)
        
        if self.video.isOpened():
            self.frame_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        else:
            self.frame_width = None
            self.frame_height = None
            print("Error: Could not open video.")

    def get_dimensions(self):
        return self.frame_width, self.frame_height
    
    def release(self):
        self.video.release()
        
    def play_it(self, speed = 0.001):
 
        plt.ion()      
        fig, ax = plt.subplots()
        img = ax.imshow(np.zeros((self.frame_height, self.frame_width)), cmap='gray', vmin=0, vmax=255)
                
        try:
            while True:
                
                ret, frame = self.video.read()
                
                if not ret: 
                    break
                
                img.set_array(frame)
                plt.draw()
                plt.pause(speed)

        except KeyboardInterrupt: 
            print("exiting")
        finally:
            self.release()
            cv2.destroyAllWindows()
            plt.close()
        