#!/usr/bin/env python 
from podcast_tools.audiogram.audiogram import AudioGram

if __name__ == '__main__':
    ag = AudioGram('input.mp3','./specs.json','./ep_specs.json')
    ag.create_audiogram_movie(out_file='output_audiogram.mp4',n_cores=1)
