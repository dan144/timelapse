#!/usr/bin/python3.6

from moviepy.editor import VideoFileClip, ImageSequenceClip
from PIL import Image
import os
import requests
import shutil
import sys
import tempfile
import threading
import time

class ClipMaster():
    print_lock = threading.Lock()
    gps_dimensions = (480, 480)

    def print_safe(self, output):
        self.print_lock.acquire()
        print(output)
        self.print_lock.release()

    def get_gps_frames(self, gps_filename):
        positions = []
        with open(gps_filename, 'r') as f:
            i = 0
            for line in f:
                i += 1
                if i % gps_freq != 0:
                    continue
                line = line.split(',')

                longitude = round((float(line[3][:2]) + (float(line[3][2:]) / 60)) *
                                  (-1 if line[4] == 'S' else 1), 6)
                latitude  = round((float(line[5][:2]) + (float(line[5][2:]) / 60)) *
                                  (-1 if line[6] == 'W' else 1), 6)

                positions.append('{},{}'.format(longitude, latitude))

        gps_directory = tempfile.mkdtemp()
        gps_filenames = []
        for index in range(len(positions)):
            urlparams = {'center': positions[index],
                         'zoom': str(17),
                         'size': '%dx%d' % self.gps_dimensions,
                         'maptype': 'roadmap',
                         'scale': 1}
            response = requests.get('http://maps.google.com/maps/api/staticmap', params=urlparams)
            filename = os.path.join(gps_directory, 'image_{}.png'.format(index))
            with open(filename, 'wb') as f:
                f.write(response.content)
            gps_filenames.append(filename)
        return gps_filenames, gps_directory

    def extract_from_clip(self, clip_index):
        clip, clip_name, gps_file, frame_count, offset = self.clips[clip_index]
        if gps_file:
            gps_images, gps_directory = self.get_gps_frames(gps_file)

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
            clip.save_frame(frame_name, t=t-1)

            if has_gps:
                # add GPS overlay
                image = Image.open(frame_name)
                gps_overlay_location = (image.size[0] - self.gps_dimensions[0], image.size[1] - self.gps_dimensions[1])
                image.paste(Image.open(gps_images[index-offset-1]), gps_overlay_location)
                image.save(frame_name)

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

        if has_gps:
            shutil.rmtree(gps_directory)

def formatted_remaining(rem):
    s_rem = '{}:{}'.format(int(rem/60), rem%60)
    if s_rem[-2] == ':':
        s_rem = s_rem[:-1] + '0' + s_rem[-1]
    return s_rem

def video_and_gps(names):
    if len(names) != 2:
        return False
    gps, videos = sorted(names)
    return os.path.isdir(videos) and os.path.split(videos)[1] == 'videos' and os.path.isdir(gps) and os.path.split(gps)[1] == 'gps' 

c = ClipMaster()

# get input/output files
clip_names = []
clip_name = None
while clip_name == None:
    clip_name = "D:\\integ_test"#input('Path to clip [empty to continue]: ')
    if os.path.isdir(clip_name):
        names = [os.path.join(clip_name, file_name) for file_name in sorted(os.listdir(clip_name))]
        if video_and_gps(names):
            gps_names = [os.path.join(clip_name, 'gps', file_name) for file_name in sorted(os.listdir(os.path.join(clip_name, 'gps')))]
            clip_names = [os.path.join(clip_name, 'videos', file_name) for file_name in sorted(os.listdir(os.path.join(clip_name, 'videos')))]
            has_gps = True
        else:
            clip_names = names
            gps_names = []

        c.print_safe("Input files:")
        if len(gps_names) > 0:
            print("Videos:")
        for name in clip_names:
            c.print_safe(name)
        if len(gps_names) > 0:
            print("GPS:")
            for name in gps_names:
                print(name)
        answer = ''
        while answer not in set('ynYN'):
            answer = input('Are these input files correct, including order? [y/n] ')
        if answer in set('yY'):
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
    output_name = "D:\\map_overlay_4.mp4"#input('Output clip path and name: ')
    if not output_name.endswith('.mp4'):
        c.print_safe('Output must be an mp4 file')
        output_name = ''

# general settings
if has_gps:
    gps_sample_freq = 1#int(input('GPS samples per second [1]: '))
input_fps = 30#int(input('FPS in input video [30]: '))
extract_f_per_x_f = 120#int(input('Extract 1 frame per x frames of input video: '))
extract_f_per_x_s = int(extract_f_per_x_f / input_fps)
if has_gps:
    gps_freq = int(gps_sample_freq * extract_f_per_x_s)
output_fps = 30#int(input('FPS in output video: '))

# create directories to stare data
directory = tempfile.mkdtemp()
c.print_safe('Extracted frames will be stored in {}'.format(directory))

c.clips = []
total_frames = 0
for clip_index in range(len(clip_names)):
    clip_name = clip_names[clip_index]
    gps_name = gps_names[clip_index] if has_gps else None

    clip = VideoFileClip(clip_name)
    frame_count = int(clip.end) + 1
    frame_count = int(frame_count / extract_f_per_x_s)
    c.print_safe("Will extract {} frames from {}".format(frame_count, clip_name))
    c.clips.append((clip, clip_name, gps_name, frame_count, total_frames))
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
