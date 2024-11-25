import cv2
import os
import matplotlib.pyplot as plt
import numpy as np


DEFAULT_SPEED = 0.001
class VideoRunner:
    def __init__(self, video_name, dir, frame_by_farme = False):
        """
        Initialize the VideoRunner with a video file.
        
        Args:
            video_name (str): Name of the video file.
            dir (str): Directory where the video file is located.
        """
        self.name = video_name
        self.dir = os.path.join(dir, self.name)
        
        self.video = cv2.VideoCapture(self.dir)
        
        if not self.video.isOpened():
            raise ValueError(f"Error: Could not open video '{self.dir}'.")
        
        self.frame_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            


    def get_dimensions(self):
        return self.frame_width, self.frame_height

 
    def release(self):
        self.video.release()

        
    def play_it(self, speed = DEFAULT_SPEED):

        plt.ion()      
        fig, ax = plt.subplots()
        img = ax.imshow(np.zeros((self.frame_height, self.frame_width)), cmap='gray', vmin=0, vmax=255)
                
        try:
            while True:
                
                ret, frame = self.video.read()
                
                if not ret: 
                    break
                
                img.set_data(frame)
                plt.draw()
                plt.pause(speed)

        except KeyboardInterrupt: 
            print("exiting")
        finally:
            self.release()
            cv2.destroyAllWindows()
            plt.close()
        

"""
This classe provide tools for automate the 
frame 
"""
class VideoCroper(VideoRunner):
    def __init__(self,video_name, dir, positive_dataset, negative_dataset):
        super().__init__(video_name= video_name, dir= dir)
        
        self.negative_dataset = negative_dataset
        self.positive_dataset = positive_dataset
        

        
    def play_it(self):
        pass