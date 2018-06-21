#!/usr/bin/python3.6

from moviepy.editor import *
import os
import time

clip_name = "D:/test.mov"
clip = VideoFileClip(clip_name)
frame_count = int(clip.end) + 1
print("Extracting {} frames from {}".format(frame_count, clip_name))
frame_digits = len(str(frame_count))

start_time = time.time()
rolling = []
for t in range(1, frame_count + 1):
    zeros = ''.join('0' for i in range(frame_digits - len(str(t))))
    frame_name = zeros + str(t)
    if t == 1 or t % 5 == 0:
        print("Saving frame {}".format(frame_name))
    frame_start = time.time()
    image = clip.save_frame("D:/images/test_image{}.png".format(frame_name), t=t-1)
    elapsed_time = time.time() - frame_start

    if len(rolling) > frame_count / 10 and len(rolling) > 5:
        # keep the rolling average based on up to the last 10% of the input video
        rolling = rolling[1:]
    rolling.append(elapsed_time)
    if t == 1 or t % 10 == 0:
        # print rolling average and est. time remaining every 10 frames
        avg = sum(rolling)/float(len(rolling))
        print("Average extraction time per frame: {}".format(avg))
        rem = int((frame_count - t) * avg)
        print("Estimated remaining time: {}s".format(rem))
print("Total elapsed time for extraction: {}s".format(int(time.time() - start_time)))

frames = 30
directory = 'D:/images/'

# stitch images together into output video
names = [directory + name for name in os.listdir(directory) if name[-4:] == ".png"]
clip = ImageSequenceClip(names, fps = frames)
clip.write_videofile('D:/test_out.mp4', fps = frames)
