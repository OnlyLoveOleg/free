#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import base64
import requests
import subprocess
import uuid

from tqdm import tqdm
from moviepy.editor import *


url = input('enter [master|playlist].json url: ')
name = input('enter output name: ')
# url = sys.argv[1]
# name = sys.argv[2]

tmp_id = str(uuid.uuid1())

if 'master.json' in url:
    url = url[:url.find('?')] + '?query_string_ranges=1'
    url = url.replace('master.json', 'master.mpd')
    print(url)
    subprocess.run(['youtube-dl', url, '-o', name])
    sys.exit(0)


def download(what, to, base):
    print('saving', what['mime_type'], 'to', to)
    with open(to, 'wb') as file:
        init_segment = base64.b64decode(what['init_segment'])
        file.write(init_segment)

        for segment in tqdm(what['segments']):
            segment_url = base + segment['url']
            resp = requests.get(segment_url, stream=True)
            if resp.status_code != 200:
                print('not 200!')
                print(segment_url)
                break
            for chunk in resp:
                file.write(chunk)
    print('done')


name += '.mp4'
base_url = url[:url.rfind('/', 0, -26) + 1]
content = requests.get(url).json()

vid_heights = [(i, d['height']) for (i, d) in enumerate(content['video'])]
vid_idx, _ = max(vid_heights, key=lambda _h: _h[1])

audio_quality = [(i, d['bitrate']) for (i, d) in enumerate(content['audio'])]
audio_idx, _ = max(audio_quality, key=lambda _h: _h[1])

video = content['video'][vid_idx]
audio = content['audio'][audio_idx]
base_url = base_url + content['base_url']

video_tmp_file = tmp_id + '-video.mp4'
audio_tmp_file = tmp_id + '-audio.mp4'

download(video, video_tmp_file, base_url + video['base_url'])
download(audio, audio_tmp_file, base_url + audio['base_url'])

video_clip = VideoFileClip(video_tmp_file)
audio_clip = AudioFileClip(audio_tmp_file)
video_clip_with_audio = video_clip.set_audio(audio_clip)
video_clip_with_audio.write_videofile(name)

os.remove(video_tmp_file)
os.remove(audio_tmp_file)