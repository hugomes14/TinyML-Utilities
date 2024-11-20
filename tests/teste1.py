import sys
import os


from src.video_runner import VideoRunner

video = VideoRunner("teste2.avi", os.path.dirname(os.path.abspath(__file__)))

video.play_it(speed= 0.1)