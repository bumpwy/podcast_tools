# podcast_tools

A python-based tool suite for podcast. Tools include:
1. creating audiogram:
    - creates an audiogram from audio input for YouTube
    - runs in parallel using `multiprocessing`

## Dependencies
python libraries:
- `matplotlib`
- `scipy`
- `numpy`
- `moveipy`
- `pydub`
- `mutagen`

Additional:
- ffmpeg


## Examples
### creating audiograms
As shown in the `examples/audiogram` directory, given the following
- `input.mp3`: the input audio file
- `podcast_logo.png`: the podcast logo
-  `specs.json`: a general podcast spec defining colors, box sizes, etc
-  `ep_specs.json`: a more specific episode spec defining title, subtitle, text size and width

  
With the above, the module `/audiogram/audiogram.py` provides the capability to create an audiogram, as shown below:

https://github.com/user-attachments/assets/28ed9ad1-7626-4208-838c-6f5def2c4d94


