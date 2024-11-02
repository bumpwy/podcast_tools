#!/usr/bin/env python
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import multiprocessing
# math libraries
import numpy as np
from scipy.fftpack import fft
# movie/audio related libraries
from pydub import AudioSegment
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
from moviepy.editor import ImageSequenceClip, AudioFileClip
# utilities
import podcast_tools.audiogram.text_util as tu
from functools import partial
import json, os, shutil, math
import time, glob

def create_audiogram_data(chunk):
    # remove DC term
    chunk -= chunk.mean()
    
    # Perform FFT (Fast Fourier Transform) to get the frequency components
    N = len(chunk)
    xf = np.linspace(0,1,N//2)
    yf = 2/N * np.abs(fft(chunk)[:N//2])

    return xf, yf

def worker_audiogram_frames(queue,canvas):
    w,h = canvas['box_size']
    fig, ax = canvas['fig'], canvas['ax']
    temp_dir, color = canvas['temp_dir'], canvas['color']
    while True:
        task = queue.get()
        # 1. Poison Pill, terminate...
        if not task:
            queue.task_done()
            break
        # 2. Otherwise...
        i, chunk, temp_dir = task
        xf, yf = create_audiogram_data(chunk)
        n = len(xf)

        # plot audiogram within the box (re-scaling and translation)
        xf = xf[:n//2]
        xf = (0.4*w/xf.max())*xf + 0.5*w
        yf = (0.1*h/yf.max())*yf[:n//2] + (h-0.4*w)/2 
        if canvas['graph']:
            canvas['graph'].remove()
        canvas['graph'] = ax.fill_between(xf,yf,(h-0.4*w)/2,color=color)
        plt.savefig(f'{temp_dir}/frame_{i}.png')

        queue.task_done()
def worker_write_clip(in_files, out_file, fps=1):
    clip = ImageSequenceClip(in_files, fps=fps)  # 10 frames per second
    clip.write_videofile(out_file, codec="libx264", audio_codec="aac")


class AudioGram:
    def __init__(self,audio_file,audio_md,podcast_md):

        # podcast meta data
        self.podcast_md = podcast_md

        # episode meta data
        self.audio_md = audio_md

        # load audio file and its meta data
        self.audio_file = audio_file
        file_type = audio_file.split('.')[-1]
        self.audio = AudioSegment.from_file(audio_file,format=file_type)

    def create_audiogram_movie(self,out_file=None,n_cores=4):
        t1 = time.time()
        ##### 1. Create frames (parallel) #####
        temp_dir = 'audiogram_frames'
        self.create_audiogram_frames(temp_dir,n_cores=n_cores)

        ##### 2. Write frames to clips (parallel) #####
        n_frames = len(glob.glob(f'{temp_dir}/frame_*.png'))
        self.create_clips(n_frames,temp_dir, n_cores)

        ##### 3. Combine videos with ffmpeg (no re-encoding) #####
        # 3.1 Combine clips into one video
        os.system(f'ffmpeg -f concat -safe 0 -i {temp_dir}/clips.txt -c copy {temp_dir}/clips_combined.mp4')

        # 3.2 add audio track
        if not out_file:
            out_file = self.audio_file.split('.')[0] + '_audiogram.mp4'
        os.system(f'ffmpeg -i {temp_dir}/clips_combined.mp4 -i {self.audio_file} -c:v copy -c:a aac -shortest {out_file}')

        ##### 4. Clean up #####
        shutil.rmtree(temp_dir)
        
        print(f'Total processing time: {time.time()-t1} secs')
        
    def create_clips(self,n_frames,temp_dir,n_cores):
        # partition frames for each processors
        q,r = n_frames//n_cores, n_frames%n_cores
        chunk_sizes = [q+1 if i<r else q for i in range(n_cores)]

        frame_files = []
        start = 0
        for n in range(n_cores):
            frame_files.append([f'{temp_dir}/frame_{i}.png' for i in range(start,start+chunk_sizes[n])])
            start += chunk_sizes[n]

        out_files = [f'{temp_dir}/clip_{i}.mp4' for i in range(n_cores)]
        fps = 1000/self.podcast_md['audio']['frame_duration_ms']

        # multiproces mapping worker function to each chunk
        worker_func = partial(worker_write_clip,fps=fps)
        with multiprocessing.Pool(n_cores) as pool:
            pool.starmap(worker_func, zip(frame_files,out_files))

        # write out text file of all clip files
        with open(f'{temp_dir}/clips.txt','wt') as f:
            for i in range(n_cores):
                f.write(f'file clip_{i}.mp4\n')

    def create_audiogram_frames(self,temp_dir,n_cores=4):
        
        # Convert stereo to mono if needed
        audio = self.audio.set_channels(1)
        samples = np.array(audio.get_array_of_samples(),dtype='float')
        
        # Parameters
        sample_rate = audio.frame_rate  # Sample rate of the audio
        duration = len(samples) / sample_rate  # Duration of the audio in seconds
        frame_duration_samples = int(sample_rate * self.podcast_md['audio']['frame_duration_ms']/1000)  # Convert frame duration to samples
        n_frames = math.ceil(len(samples)/frame_duration_samples)
        
        ##### Parallel Processing #####
        # Create a directory to store the frames (plots)
        os.makedirs(temp_dir, exist_ok=True)

        # spawn workers (external)
        queue = multiprocessing.JoinableQueue()
        workers = []
        for _ in range(n_cores):
            fig, ax = self.create_background()
            canvas = {'box_size':self.podcast_md['box']['size'],'fig':fig,'ax':ax,'graph':None,
                      'temp_dir':temp_dir,'color':self.podcast_md['audio']['audiogram_color']}
            worker = multiprocessing.Process(target=worker_audiogram_frames,args=(queue,canvas))
            worker.start()
            workers.append(worker)

        # put tasks into queue
        for i in range(n_frames):
            chunk = samples[i*frame_duration_samples:(i+1)*frame_duration_samples]
            queue.put((i,samples[i*frame_duration_samples:(i+1)*frame_duration_samples],temp_dir))
        queue.join()

        # terminate workers
        for _ in range(n_cores):
            queue.put(None)
        for worker in workers:
            worker.join()
        ##### Parallel Processing (End) #####

    def create_background(self):
        
        ##### 1. Canvas #####
        canvas = self.podcast_md['canvas']
        fig = plt.figure(figsize=canvas['size'])
        fig.patch.set_facecolor(canvas['color'])
        
        ##### 2. Middle Box #####
        box = self.podcast_md['box']
        W, H = canvas['size']
        w, h = box['size']
        ax = fig.add_axes([(1-w/W)/2,(1-h/H)/2,w/W,h/H])
        ax.set_xlim(0,w)
        ax.set_ylim(0,h)
        ax.patch.set_facecolor(box['color'])
        ax.set_xticks([])
        ax.set_yticks([])
        
        ##### 3. Podcast Logo #####
        img = mpimg.imread(self.podcast_md['logo']['file_path'])
        ax.imshow(img, extent=(w*0.05,w*0.45, (h-0.4*w)/2, (h+0.4*w)/2),zorder=2)
        
        ##### 4. Textual: podcast name, title, and subtitle #####
        # 4.1 podcast name
        matplotlib.rcParams['font.family'] = 'Heiti TC'
        ax.text(0.725*w,(h+0.4*w)/2, self.audio_md['podcast_name'], 
                ha = 'center', va = 'top',
                fontsize=self.audio_md['podcast_name_fs'])
        # 4.2 episode title & subtitle
        title_fs = self.audio_md['title_fs']
        char_width = tu.get_char_width(fig,ax,title_fs)
        text_width = 0.4*w/char_width
        title = tu.textwrap_mixed(self.audio_md['title'],text_width)
        ax.text(0.5*w,0.5*h,'\n'.join(title),
                ha='left',va='center',fontsize=self.audio_md['title_fs'])

        return fig, ax

        
