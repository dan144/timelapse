#!/usr/bin/python3.6

from moviepy.editor import *
import os

clip = VideoFileClip("D:/test.mov")
frame_count = int(clip.end) + 1
print("Saving {} frames".format(frame_count))

frame_digits = len(str(frame_count))

for t in range(frame_count):
    zeros = ''.join('0' for i in range(frame_digits - len(str(t+1))))
    frame_name = zeros + str(t+1)
    print("Saving frame {}".format(frame_name))
    image = clip.save_frame("D:/images/test_image{}.png".format(frame_name), t=t)

frames = 30
directory = 'D:/images/'

names = [directory + name for name in os.listdir(directory) if name[-4:] == ".png"]

clip = ImageSequenceClip(names, fps = frames)

clip.write_videofile('D:/test_out.mp4', fps = frames)
