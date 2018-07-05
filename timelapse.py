#!/usr/bin/python3.6

from moviepy.editor import VideoFileClip, ImageSequenceClip
import os
import shutil
import sys
import tempfile
import time

def formatted_remaining(rem):
    s_rem = '{}:{}'.format(int(rem/60), rem%60)
    if s_rem[-2] == ':':
        s_rem = s_rem[:-1] + '0' + s_rem[-1]
    return s_rem

# get input/output files
clip_count = int(input('Number of input videos: '))
clip_names = []
for n in range(clip_count):
    clip_name = ''
    while clip_name == '':
        clip_name = input('Path to clip {}: '.format(n+1))
        if not os.path.exists(clip_name):
            print('Clip does not exit at given path: {}'.format(clip_name))
            clip_name = ''
    clip_names.append(clip_name)
output_name = ''
while output_name == '':
    output_name = input('Output clip path and name: ')
    if not output_name.endswith('.mp4'):
        print('Output must be an mp4 file')
        output_name = ''

# general settings
extract_f_per_x_s = int(input('Extract 1 frame per x second of input video: '))
output_fps = int(input('FPS in output video: '))
directory = tempfile.mkdtemp()
print('Extracted frames will be stored in {}'.format(directory))

clips = []
total_frames = 0
for clip_name in clip_names:
    clip = VideoFileClip(clip_name)
    frame_count = int(clip.end) + 1
    frame_count = int(frame_count / extract_f_per_x_s)
    total_frames += frame_count
    print("Will extract {} frames from {}".format(frame_count, clip_name))
    clips.append((clip, clip_name, frame_count))
print('{} will be {}'.format(output_name, formatted_remaining(total_frames / output_fps)))

# extract frames
start_time = time.time()
rolling = []
image_files = []
index = 0
for clip, clip_name, frame_count in clips:
    print("Processing input file {}".format(clip_name))
    frame_digits = len(str(frame_count))
    for t in range(1, frame_count*extract_f_per_x_s + 1, extract_f_per_x_s):
        index += 1
        zeros = ''.join('0' for i in range(frame_digits - len(str(index))))
        frame_name = zeros + str(index)
        if index == 1 or index % 5 == 0:
            print("Saving frame {}".format(frame_name))
        frame_name = os.path.join(directory, "test_image{}.png".format(frame_name))
        frame_start = time.time()
        image = clip.save_frame(frame_name, t=t-1)
        elapsed_time = time.time() - frame_start
        image_files.append(frame_name)

        if len(rolling) > frame_count / 10 and len(rolling) > 5:
            # keep the rolling average based on up to the last 10% of the input video
            rolling = rolling[1:]
        rolling.append(elapsed_time)
        if index == 1 or index % 5 == 0:
            # print rolling average and est. time remaining every 10 frames
            avg = sum(rolling)/float(len(rolling))
            print("Average extraction time per frame: {}".format(avg))
            s_rem = formatted_remaining(int((total_frames - index) * avg))
            print("Estimated remaining time: {}".format(s_rem))
total_time = formatted_remaining(int(time.time() - start_time))
print("Total elapsed time for extraction: {}".format(total_time))

# stitch images together into output video
clip = ImageSequenceClip(image_files, fps = output_fps)
clip.write_videofile(output_name, fps = output_fps)

# cleanup
answer = ''
while answer not in set('ynYN'):
    answer = input('Erase image frame files? [y/n] ')
if answer in set('yY'):
    shutil.rmtree(directory)
