# Music-Library-Conversion-Script
A Python Script that converts a music library consisting of FLAC and MP3 files to only MP3 Files. It can also copy LRC files and also convert and scale down embedded covers.

## Features
  - Conversion of Music Library consisting of FLAC and MP3 files into a new one that only consists of MP3 files for portable use.
  - Can copy corresponding LRC-files
  - Can convert embedded covers to JPEG for smaller file sizes
  - Can scale down embedded covers for smaller file sizes while keeping aspect ratio
  - Generates extensive log by default
  - Colored terminal output on supported environments for better readablity
  
## Planned Features
  - Multiple conversion/copy processes simultaineously
  - Automatic LRF-file grabbing

## Requirements
  - Python 3
  - ffmpeg

### Python Libraries
  - python_reszize_image
  - Pillow
  - colorama
  - blessings
  
## Usage
  1. Clone the Repository by using the "Download ZIP" button ur using git: `git clone https://github.com/JoeJoeTV/Music-Library-Conversion-Script`.
  2. Change into the cloned directory: `cd Music-Library-Conversion-Script`
  3. Install the required python packages using pip: `pip install -r requirements.txt` or `pip3 install -r requirements.txt`
  4. Install `ffmpeg`:
    - On Linux you can install ffmpeg using your preferred package manager (see https://www.ffmpeg.org/download.html#build-linux)
    - On Windows, you can download builds from https://www.ffmpeg.org/download.html#build-windows
    - On Mac, you can download builds from https://www.ffmpeg.org/download.html#build-mac
  5. Execute the script using python 3: `python3 convert-music-library.py `...
    
    USAGE: convert-music-library.py <Source Directory> <Destination Directory> [OPTIONS]

    Arguments:
       <Source Path>                       The path where the original audio files, which are to be converted, are stored
       <Destination Path>                  The path where the converted files should be stored

       -h          --help                  Displays this Help Message and exits
       -l          --copy-lyrics           Also copy matching Lyric-Files(LRC)
       -s <size>   --scale-cover=<size>    Scales the cover to fit in a box with with and height of <size>
       -c          --convert-cover         Converts the cover to the JPEG format
       -n          --no-log-file           Disables the normally generated LOG-file
       
## Bugs and Contributions
  If you find any bugs or issues with the script, please report them here on the "Issues" tab.
