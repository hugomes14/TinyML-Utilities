import sys
import os


from src.video_utils import VideoRunner


video = VideoRunner("videos/digital_mp4_preto.mp4", os.path.dirname(os.path.abspath(__file__)))

video.play_it(speed= 0.0001)

video.release()