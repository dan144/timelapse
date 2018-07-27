import requests
import tempfile, shutil, os, time

from moviepy.editor import ImageSequenceClip

position_data = []
with open('gpsdata.log', 'r') as f:
    i = 0
    for line in f:
        i += 1
        if i % 4 != 0:
            continue
        line = line.split(',')

        longitude = round((float(line[3][:2]) + (float(line[3][2:]) / 60)) *
                          (-1 if line[4] == 'S' else 1), 6)
        latitude  = round((float(line[5][:2]) + (float(line[5][2:]) / 60)) *
                          (-1 if line[6] == 'W' else 1), 6)

        position_data.append('{},{}'.format(longitude, latitude))
        print(".", end='')
print()

directory = tempfile.mkdtemp()
print(directory)
filenames = []
for index in range(len(position_data)):
    if index % 5 == 0 or index == 1:
        print('Grabbing index {} of {}'.format(index+1, len(position_data)))
    urlparams = {'center': position_data[index],
                 'zoom': str(17),
                 'size': '%dx%d' % (480,480),
                 'maptype': 'roadmap',
                 'scale': 1}
    response = requests.get('http://maps.google.com/maps/api/staticmap', params=urlparams)
    filename = os.path.join(directory, 'image_{}.png'.format(index))
    with open(filename, 'wb') as f:
        f.write(response.content)
    filenames.append(filename)
clip = ImageSequenceClip(filenames, fps = 60)
clip.write_videofile('D:/testing.mp4', fps = 60)
shutil.rmtree(directory)
