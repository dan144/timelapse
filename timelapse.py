#!/usr/bin/python3.6

from moviepy.editor import VideoFileClip, ImageSequenceClip
import os
import shutil
import sys
import tempfile
import threading
import time

class ClipMaster():
    print_lock = threading.Lock()

    def print_safe(self, output):
        self.print_lock.acquire()
        print(output)
        self.print_lock.release()

    def extract_from_clip(self, clip_index):
        clip, clip_name, frame_count, offset = self.clips[clip_index]
        start_time = time.time()
        self.rolling[clip_index] = []
        self.image_files[clip_index] = []
        index = offset
        self.print_safe("[{}] - Processing input file".format(clip_name))
        for t in range(1, frame_count*extract_f_per_x_s + 1, extract_f_per_x_s):
            index += 1
            zeros = ''.join('0' for i in range(self.frame_digits - len(str(index))))
            frame_name = zeros + str(index)
            if index == 1 or index % 5 == 0:
                self.print_safe("[{}] - Saving frame {}".format(clip_name, index - offset))
            frame_name = os.path.join(directory, "image{}.png".format(frame_name))
            frame_start = time.time()
            image = clip.save_frame(frame_name, t=t-1)
            elapsed_time = time.time() - frame_start
            self.image_files[clip_index].append(frame_name)

            if len(self.rolling[clip_index]) > total_frames / 10 and len(self.rolling[clip_index]) > 5:
                # keep the rolling average based on up to the last 10% of the input files
                self.rolling[clip_index] = self.rolling[clip_index][1:]
            self.rolling[clip_index].append(elapsed_time)
            if index == 1 or index % 5 == 0:
                # print rolling average and est. time remaining every 10 frames
                avg = sum(self.rolling[clip_index])/float(len(self.rolling[clip_index]))
                self.print_safe("[{}] - Average extraction time per frame: {}".format(clip_name, avg))
                s_rem = formatted_remaining(int((total_frames - index) * avg))
                self.print_safe("[{}] - Estimated remaining time: {}".format(clip_name, s_rem))
        total_time = formatted_remaining(int(time.time() - start_time))
        self.print_safe("[{}] - Total elapsed time for extraction: {}".format(clip_name, total_time))

def formatted_remaining(rem):
    s_rem = '{}:{}'.format(int(rem/60), rem%60)
    if s_rem[-2] == ':':
        s_rem = s_rem[:-1] + '0' + s_rem[-1]
    return s_rem

c = ClipMaster()

# get input/output files
clip_names = []
clip_name = None
while clip_name == None:
    clip_name = input('Path to clip [empty to continue]: ')
    if os.path.isdir(clip_name):
        names = [os.path.join(clip_name, file_name) for file_name in sorted(os.listdir(clip_name))]
        c.print_safe("Input files:")
        for name in names:
            c.print_safe(name)
        answer = ''
        while answer not in set('ynYN'):
            answer = input('Are these input files correct, including order? [y/n] ')
        if answer in set('yY'):
            clip_names = names
            break
        else:
            clip_name = None
    elif os.path.exists(clip_name) and os.path.isfile(clip_name):
        clip_names.append(clip_name)
        clip_name = None
    elif clip_name != '':
        c.print_safe('Clip does not exist at given path: {}'.format(clip_name))
        clip_name = None
if len(clip_names) == 0:
    c.print_safe("No input files given")
    sys.exit(1)
output_name = ''
while output_name == '':
    output_name = input('Output clip path and name: ')
    if not output_name.endswith('.mp4'):
        c.print_safe('Output must be an mp4 file')
        output_name = ''

# general settings
extract_f_per_x_s = int(input('Extract 1 frame per x second of input video: '))
output_fps = int(input('FPS in output video: '))
directory = tempfile.mkdtemp()
c.print_safe('Extracted frames will be stored in {}'.format(directory))

c.clips = []
total_frames = 0
for clip_name in clip_names:
    clip = VideoFileClip(clip_name)
    frame_count = int(clip.end) + 1
    frame_count = int(frame_count / extract_f_per_x_s)
    c.print_safe("Will extract {} frames from {}".format(frame_count, clip_name))
    c.clips.append((clip, clip_name, frame_count, total_frames))
    total_frames += frame_count
c.print_safe('{} will be {}'.format(output_name, formatted_remaining(total_frames / output_fps)))
c.frame_digits = len(str(total_frames))
clip_count = len(c.clips)

# extract frames
start_time = time.time()
c.rolling = [None] * clip_count
c.image_files = [None] * clip_count
thread_list = []
for clip_index in range(len(c.clips)):
    t = threading.Thread(target = c.extract_from_clip, args = (clip_index,))
    t.start()
    thread_list.append(t)
for t in thread_list:
    t.join()
total_time = formatted_remaining(int(time.time() - start_time))
c.print_safe("Total elapsed time for extraction: {}".format(total_time))

# stitch images together into output video
image_files = []
for image_set in c.image_files:
    image_files += image_set
clip = ImageSequenceClip(image_files, fps = output_fps)
clip.write_videofile(output_name, fps = output_fps)

# cleanup
answer = ''
while answer not in set('ynYN'):
    answer = input('Erase image frame files? [y/n] ')
if answer in set('yY'):
    shutil.rmtree(directory)
