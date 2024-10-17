# podcast_tools

A python-based tool suite for podcast. Tools include:
1. creating audiogram:
    - creates an audiogram from audio input for YouTube
    - runs in parallel using `multiprocessing`
    - handles Chinese/English mixed text justification (see example below)

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
-  `ep_specs.json`: a more specific episode spec defining episode title and font size. The episode can be chinese/english mixed text.

the module `/audiogram/audiogram.py` provides the capability to create an audiogram, as shown below. Notably, the `/audiogram/text_util.py` module will fit Chinese/English mixed text into the box with the correct line width.

https://github.com/user-attachments/assets/72adce6d-4623-475e-ae55-679771674875




