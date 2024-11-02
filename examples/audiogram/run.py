#!/usr/bin/env python 
from podcast_tools.audiogram.audiogram import AudioGram
import json

if __name__ == '__main__':
    with open('./specs.json','rt') as f:
        podcast_md = json.load(f)
    with open('./ep_specs.json','rt') as f:
        audio_md = json.load(f)
    ag = AudioGram('input.mp3',audio_md=audio_md,podcast_md=podcast_md)
    ag.create_audiogram_movie(out_file='output_audiogram.mp4',n_cores=1)
