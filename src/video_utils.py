import cv2
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button
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
        
      
        self.fig, self.ax = plt.subplots()
        self.img = self.ax.imshow(np.zeros((self.frame_height, self.frame_width)), cmap='gray', vmin=0, vmax=255)
            


    def get_dimensions(self):
        return self.frame_width, self.frame_height

 
    def release(self):
        self.video.release()

        
    def play_it(self, speed = DEFAULT_SPEED, frame_by_frame = False):
        plt.ion()       
        try:
            while True:
                
                ret, frame = self.video.read()
                
                if not ret: 
                    break
                
                self.img.set_data(frame)
                plt.draw()
                plt.pause(speed)

        except KeyboardInterrupt: 
            print("exiting")
        finally:
            self.release()
            cv2.destroyAllWindows()
            plt.close()


class VideoCrop(VideoRunner):
    def __init__(self, video_name, dir, negative_dataset, positive_dataset):
        super().__init__(video_name= video_name, dir= dir)
        
        self.negative_dataset = os.path.join(dir, negative_dataset)
        self.positive_dataset = os.path.join(dir, positive_dataset)
        
        
        plt.subplots_adjust(bottom=0.2)
        
        ax_positive_dataset = plt.axes([0.1, 0.05, 0.2, 0.075])
        self.button_positive_dataset = Button(ax_positive_dataset, "Positive Dataset")
        self.button_positive_dataset.on_clicked(self.positive_callback)
        
        ax_negative_dataset = plt.axes([0.4, 0.05, 0.2, 0.075])
        self.button_negative_dataset = Button(ax_negative_dataset, "Negative Dataset")
        self.button_negative_dataset.on_clicked(self.negative_callback)
        
        ax_next_frame = plt.axes([0.7, 0.05, 0.2, 0.075])
        self.button_next_frame = Button(ax_next_frame, "Next Frame")
        self.button_next_frame.on_clicked(self.next_callback)

        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        
        #flags
        self.rectangle_created = False
        self.frames_index = 1
        

    
    def positive_callback(self, event):
        i = self.count_files_in_directory(self.positive_dataset)
        cv2.imwrite(os.path.join(self.positive_dataset, f"{i+1}.png"), cv2.cvtColor(self.cropped_frame, cv2.COLOR_RGB2BGR))

        
    def negative_callback(self, event):
        i = self.count_files_in_directory(self.negative_dataset)
        cv2.imwrite(os.path.join(self.negative_dataset, f"{i+1}.png"), cv2.cvtColor(self.cropped_frame, cv2.COLOR_RGB2BGR))


    def next_callback(self, event):
        self.next_frame_pressed = True
    
    
    def on_click(self, event):
        if  not self.rectangle_created:
            if event.inaxes is not None and event.inaxes == self.ax:
                self.create_rectangle_entity()
                self.start_point = (event.xdata, event.ydata)
                self.rect.set_xy(self.start_point)
                plt.draw()



    def on_drag(self, event):
        if self.rectangle_created:
            if self.start_point is not None and event.inaxes is not None and event.inaxes == self.ax:
                self.end_point = (event.xdata, event.ydata)
                # Calculate width and height while maintaining aspect ratio
                
                width = self.end_point[0] - self.start_point[0]
                height = width / self.aspect_ratio  # Maintain aspect ratio
                
                self.rect.set_width(width)
                self.rect.set_height(height)
                self.rect.set_xy(self.start_point)  # Update rectangle position
                plt.draw()

    def on_release(self, event):
        if self.rectangle_created:
            if self.start_point and self.end_point and event.inaxes == self.ax:
                print("choosing where to put the cropped frame")
                x1, y1 = int(min(self.start_point[0], self.end_point[0])), int(min(self.start_point[1], self.end_point[1]))
                x2, y2 = int(max(self.start_point[0], self.end_point[0])), int(max(self.start_point[1], self.end_point[1]))

                # Crop the image
                self.cropped_frame = self.frame[y1:y2, x1:x2]
                self.rect.remove()  # Remove the rectangle from the axes
                self.rectangle_created = False
                self.start_point = None  # Reset start point
                self.end_point = None
                
                self.next_frame_pressed = False

    
      
    def dataset_constructer(self):
        try:
            while True:
                # Read a frame from the video
                ret, frame = self.video.read()
                
                # Break the loop if there are no frames left
                if not ret:
                    break
                
        
                self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.ax.clear()  # Clear the previous frame
                self.ax.imshow(frame)  # Display the current frame
                self.ax.axis('off')  # Hide axis
                plt.draw()  # Update the plot
                self.next_frame_pressed = False
                
                
                        
                while not self.next_frame_pressed:
                    plt.pause(0.01)

        except KeyboardInterrupt: 
            print("Exiting")
        finally:
            # Release the video capture object
            self.video.release()
            cv2.destroyAllWindows()
            plt.close()
    
    
    def create_rectangle_entity(self):
        # Create a rectangle patch
        
        self.rectangle_created = True
        
        self.rect = patches.Rectangle((0, 0), 1, 1, linewidth=1, edgecolor='r', facecolor='none')
        self.ax.add_patch(self.rect)

        # Variables to store the rectangle coordinates
        self.start_point = None
        self.end_point = None
        self.aspect_ratio =  self.frame_width /self.frame_height  

 
    def count_files_in_directory(self, dir):
        try:
            files = os.listdir(dir)
            return len(files)
        except:
            return 0
        


    
    

    
                    
      
        


