#!/usr/bin/python3
# coding: utf8

# Music Library Converter
# by JoeJoeTV - 2020,2021
# Required Python libraries: python-resize-image, Pillow, colorama, blessings
# Other Requirements: ffmpeg


import sys
import os
import shutil
import subprocess
import time
import logging
import tempfile
import getopt
from PIL import Image
from resizeimage import resizeimage
import re
import colorama
from blessed import Terminal

#Arguments
# - Source Path
# - Destination Path
# - Options
#   - --copy-lyrics
#   - --scale-cover <size>
#   - --convert-cover
#   - --no-log-file

#Variables and Constants
#------------------------

version="1.0.0"

short_options = "hvls:cn"
long_options = ["help", "version", "copy-lyrics", "scale-cover=", "convert-cover", "no-log-file"]
settings = {
    "copy_lyrics": False,
    "scale_cover": False,
    "cover_scale": 0,
    "convert_cover": False,
    "generate_logfile": True,
    "replace_files": False
}
helptext = "USAGE: {0} <Source Directory> <Destination Directory> [OPTIONS]\n\nConvert Music Libraries containing MP3 and FLAC files to better fit smaller file size limitations.\n\nArguments:\n   <Source Path>                       The path where the original audio files, which are to be converted, are stored\n   <Destination Path>                  The path where the converted files should be stored\n\n   -h          --help                  Displays this Help Message and exits\n   -l          --copy-lyrics           Also copy matching Lyric-Files(LRC)\n   -s <size>   --scale-cover=<size>    Scales the cover to fit in a box width with and height of <size>\n   -c          --convert-cover         Converts the cover to the JPEG format\n   -n          --no-log-file           Disables the normally generated LOG-file"
summarytext = "\nSUMMARY:\n  Found {0} files!\n    - Converted:\n      - Success: {1}\n      - Failure: {2}\n    - Copied:\n      - Success: {3}\n      - Failure: {4}\n    - Exists: {5}\n    - LRC-Files Copied:\n      - Success: {6}\n      - Failure: {7}"
configurationtext = "\nCONFIGURATION:\n  - Source Path: {0}\n  - Destination Path: {1}\n  - Generate Logfile: {2}\n  - Convert Cover to JPG: {3}\n  - Resize Cover: {4}\n  - Copy Lyrics: {5}\n"
tmpdir = tempfile.mkdtemp(prefix="cml_")

sourcepath = ""
destpath = ""
counters = {
    "copy_success": 0,
    "copy_failure": 0,
    "convert_success": 0,
    "convert_failure": 0,
    "lrc_copy_success": 0,
    "lrc_copy_failure": 0,
    "exists": 0
}

#Functions
#----------

# Function: isint
# Arguments:
#   - val: Any value
# Description: Checks wether a given value is an integer

def isint(val):
    try:
        int(val)
        return True
    except ValueError:
        return False

# Function: path_leaf
# Arguments:
#   - path: Any path
# Description: Returns the leaf of a path

def path_leaf(path):
    head, tail = os.path.split(path)
    return tail or os.path.basename(head)

# Function: checkParameters()
# Description: Checks if passed arguments are valid and sets the 'settings'-variables as well as 'sourcepath' and 'destpath' accordingly.

def checkParameters():
    argument_list = sys.argv[1:]
    global sourcepath
    global destpath
    global settings
    
    try:    
        option_args, other_args = getopt.gnu_getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        print("[ERROR] "+str(err))
        sys.exit(2)
    if (len(other_args) >= 2) and os.path.isdir(other_args[0]) and (os.path.isdir(other_args[1]) or ((not os.path.exists(other_args[1]) and os.makedirs(other_args[1])))):
        sourcepath = os.path.abspath(other_args[0])
        destpath = os.path.abspath(other_args[1])

        for arg, val in option_args:
            if arg in ("-h", "--help"):
                print(helptext)
                sys.exit(0)
            elif arg in ("-v", "--version"):
                print("Version "+version)
                sys.exit(0)
            elif arg in ("-l", "--copy-lyrics"):
                settings["copy_lyrics"] = True
            elif arg in ("-s", "--scale-cover"):
                if isint(val) and val != "" and int(val) != 0:
                    settings["scale_cover"] = True
                    settings["cover_scale"] = int(val)
                else:
                    print("[ERROR] Invalid Value for Argument '"+arg+"': "+str(val)+". Expected Integer!")
                    sys.exit(2)
            elif arg in ("-c","--convert-cover"):
                settings["convert_cover"] = True
            elif arg in ("-n", "--no-log-file"):
                settings["generate_logfile"] = False
        
        return True
    elif len(other_args) == 0:
        if len(option_args) > 0:
            for arg, val in option_args:
                if arg in ("-h", "--help"):
                    print(helptext.format(path_leaf(sys.argv[0])))
                    sys.exit(0)
                elif arg in ("-v", "--version"):
                    print("Version "+version)
                    sys.exit(0)
        else:
            print(helptext.format(path_leaf(sys.argv[0])))
            sys.exit(0)
    else:
        print("[ERROR] Invalid source and/or destination path!\nSee '--help' for usage options.")
        sys.exit(2)       

# Function: getLogFileName
# Arguments:
#   - basename: Base name for the log file to identify corresponding application
#   - logdir: Directory in which the log file is stored. Defaults to the current working directory.
# Description: Generates a filename for the log-file using the current date and a counter if another log file already exists.

def getLogFileName(basename, logdir=os.getcwd()):
    filename = basename+"_"+time.strftime("%d-%m-%Y", time.localtime())
    
    if os.path.exists(os.path.join(logdir, filename+".log")):
        filenamefree = False
        i = 1
        
        while not filenamefree:
            if os.path.exists(os.path.join(logdir, filename+"_"+str(i)+".log")):
                i = i + 1
            else:
                filenamefree = True
        
        filename = os.path.join(logdir, filename+"_"+str(i)+".log")
    else:
        filename = os.path.join(logdir, filename+".log")
    
    return filename

# Function: getAudioFileCoverFormat(audio_file)
# Arguments:
#   - audio_file: Path to an audio file with an embedded cover.
# Description: Extracts the file format of the embedded cover of 'audio_file' using 'ffprobe'

def getAudioFileCoverFormat(audio_file):
    if os.path.exists(audio_file) and os.path.isfile(audio_file):
        result_probe_format = subprocess.run(["ffprobe", "-hide_banner", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-loglevel", "quiet", audio_file], capture_output=True, text=True)
        in_stream_section = False
        codec_name = ""
        
        if result_probe_format.returncode == 0:
            for line in result_probe_format.stdout.split('\n'):
                if "[STREAM]" in line:
                    in_stream_section = True
                    codec_name = ""
                elif "[/STREAM]" in line and in_stream_section: 
                    in_stream_section = False
                elif in_stream_section:
                    match = re.search(r"^codec_name=([a-z\-_]+)",line)
                    if match:
                        codec_name = match.group(1)
            return codec_name
        else:
            return ""
    else:
        return ""

# Function: convertCover(input_file, output_filename, convert_cover=True, cover_size=0)
# Arguments:
#   - input_file: Path to cover image file, which should be converted
#   - output_filename: Filename of output file
#   - convert_cover: If the cover should be converted. Defaults to True.
#   - cover_size: The size the cover should be scaled to. Any value greater than 0 means that the cover will get scaled. Defaults to 0.
# Description: Converts the given image file according to the other arguments and outputs it as a file ('output_filename').

def convertCover(input_file, output_filename, convert_cover=True, cover_size=0):
    if os.path.exists(input_file) and os.path.isfile(input_file):
        cover = Image.open(input_file)  
        original_format = cover.format

        if cover_size > 0:
            if (cover.height > cover_size) or (cover.width > cover_size):
                cover = resizeimage.resize_thumbnail(cover, [cover_size, cover_size])

        if convert_cover and cover.format != "JPEG":
            cover = cover.convert("RGB")
            cover.save(output_filename, format="JPEG")
        else:
            cover.save(output_filename, format=original_format)

#Setup Code
#-----------

#Init Colorama
colorama.init()

#Init Blessings
term = Terminal()

print("{term.green}Music Library Converter {term.normal}by {term.cyan}JoeJoeTV{term.normal}\n".format(term=term))

#Check for dependencies
result_check_ffmpeg = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=False)
if result_check_ffmpeg.returncode != 0:
    print(term.red("[ERROR] Missing dependency 'ffmpeg'! Please install it from https://ffmpeg.org."))

#Check Parameters
checkParameters()

#Setup Logging
if settings["generate_logfile"]:
    logging.basicConfig(filename=getLogFileName("cml"), filemode="a", format="[%(asctime)s](%(levelname)s) %(message)s", datefmt="%H:%M:%S", level=logging.INFO)
    
logging.info("Music Library Converter by JoeJoeTV")

configstring = configurationtext.format(sourcepath, destpath, str(settings["generate_logfile"]), str(settings["convert_cover"]), str(settings["scale_cover"])+"("+str(settings["cover_scale"])+")", str(settings["copy_lyrics"]))
print(configstring)
for s in configstring.split("\n"):
    logging.info(s)

#Get Starting Time
starttime = time.time()

#Main Code
#----------

#Recurse through all subdirectories
for root, dirs, files in os.walk(sourcepath):
    for filename in files:
        extension = os.path.splitext(filename)[1][1:]
        name = os.path.splitext(filename)[0]
        relpath = os.path.relpath(root, sourcepath)
        newpath = os.path.join(destpath, relpath)
        originalfilepath = os.path.join(root, filename)
        
        #Check for file type using file extension
        if extension == "mp3":
            #New File Path is the same relative path added to the destination path
            newfilepath = os.path.join(newpath, filename)
            
            #Check if file with new filename already exists (Convert)
            if os.path.exists(newfilepath):
                print("{term.bright_magenta}[EXISTS] {term.bright_blue}{0}".format(newfilepath, term=term))
                logging.info("EXISTS: "+newfilepath)
                counters["exists"] += 1
            else:
                #If new file path does not exist, create it
                if not (os.path.exists(newpath)):
                    os.makedirs(newpath)
                
                print("{term.green}[COPY] {term.bright_blue}{0} {term.normal}-> {term.bright_cyan}{1}{term.normal}... ".format(originalfilepath, newfilepath, term=term), end="")
                
                #If Setting 'convert_cover' or 'scale_cover' are selected...
                if settings["convert_cover"] or settings["scale_cover"]:
                    # Extract Cover
                    
                    #Get typ of cover
                    extracted_cover_format = getAudioFileCoverFormat(originalfilepath)
                    
                    #Only continue the processs if there is a cover present
                    if extracted_cover_format != "":
                        #Specify file paths for extraction and conversion
                        extracted_cover_filename = os.path.join(tmpdir, "tmp_extractedcover")
                        new_cover_filename = os.path.join(tmpdir, "tmp_newcover")
                        
                        #Extract the cover using ffmpeg
                        result_extract_cover = subprocess.run(["ffmpeg", "-i", originalfilepath, "-c:v", "copy", "-loglevel", "quiet", "-f", "image2", extracted_cover_filename], capture_output=True, text=False)
                        
                        #Check if the extraction process was successful
                        if result_extract_cover.returncode == 0:
                            #Convert cover according to set settings
                            convertCover(extracted_cover_filename, new_cover_filename, settings["convert_cover"], settings["cover_scale"])
                            
                            #Re-insert cover into audio file using ffmpeg
                            result_replace_cover = subprocess.run(["ffmpeg","-i", originalfilepath, "-f", "image2", "-i", new_cover_filename, "-c", "copy", "-map", "0:a", "-map", "1:v", "-write_xing", "0", newfilepath], capture_output=True, text=True)

                            if result_replace_cover.returncode == 0:
                                print(term.green("SUCCESS (CONVERT)"))
                                logging.info("COPY - SUCCESS: "+originalfilepath+" -> "+newfilepath)
                                counters["copy_success"] += 1
                            else:
                                print(term.red("FAIL"))
                                print(term.red("[ERROR] There was a problem while replacing the cover!"))
                                logging.warning("COPY - FAIL: "+originalfilepath+" -> "+newfilepath)
                                logging.error("There was a problem while replacing the cover!")    
                                
                                counters["copy_failure"] += 1                        
                        else:
                            print(term.red("FAIL"))
                            print(term.red("[ERROR] There was a problem while extracting the cover!"))
                            logging.warning("COPY - FAIL: "+originalfilepath+" -> "+newfilepath)
                            logging.error("There was a problem while extracting the cover!") 
                            counters["copy_failure"] += 1   
                            
                        if os.path.exists(extracted_cover_filename):
                            os.remove(extracted_cover_filename)      
                        if os.path.exists(new_cover_filename):
                            os.remove(new_cover_filename)
                            
                else:
                    result_copy = shutil.copyfile(originalfilepath, newfilepath)

                    if os.path.exists(newfilepath) and os.path.samefile(newfilepath, result_copy):
                        print(term.green("SUCCESS (COPY ONLY)"))
                        logging.info("COPY - SUCCESS: "+originalfilepath+" -> "+newfilepath)
                        counters["copy_success"] += 1
                    else:
                        print(term.red("FAIL"))
                        logging.warning("COPY - FAIL: "+originalfilepath+" -> "+newfilepath)
                        counters["copy_failure"] += 1
        elif extension == "flac":
            newfilepath = os.path.join(newpath, name+".mp3")
            
            #Check if file with new filename already exists (Convert)
            if os.path.exists(newfilepath):
                print("{term.bright_magenta}[EXISTS] {term.bright_blue}{0}".format(newfilepath, term=term))
                logging.info("EXISTS: "+newfilepath)
                counters["exists"] += 1
            else:
                #If new file path does not exist, create it
                if not (os.path.exists(newpath)):
                    os.makedirs(newpath)
                    
                print("{term.blue}[CONVERT] {term.bright_blue}{0} {term.normal}-> {term.bright_cyan}{1}{term.normal}... ".format(originalfilepath, newfilepath, term=term), end="")
                
                #If Setting 'convert_cover' or 'scale_cover' are selected...
                if settings["convert_cover"] or settings["scale_cover"]:
                    # Extract Cover
                    
                    #Get typ of cover
                    extracted_cover_format = getAudioFileCoverFormat(originalfilepath)
                    
                    #Only continue the process if there is a cover present
                    if extracted_cover_format != "":
                        #Specify file paths for extraction and conversion
                        extracted_cover_filename = os.path.join(tmpdir, "tmp_extractedcover")
                        new_cover_filename = os.path.join(tmpdir, "tmp_newcover")
                        
                        #Extract the cover using ffmpeg
                        result_extract_cover = subprocess.run(["ffmpeg", "-i", originalfilepath, "-c:v", "copy", "-loglevel", "quiet", "-f", "image2", extracted_cover_filename], capture_output=True, text=False)
                        
                        #Check if the extraction process was successful
                        if result_extract_cover.returncode == 0:
                            #Convert cover according to set settings
                            convertCover(extracted_cover_filename, new_cover_filename, settings["convert_cover"], settings["cover_scale"])

                            result_convert_file = subprocess.run(["ffmpeg", "-i", originalfilepath, "-f", "image2", "-i", new_cover_filename, "-hide_banner", "-loglevel", "quiet", "-c:v", "copy", "-map", "0:a", "-map", "1:v", "-c:a", "mp3", "-b:a", "320k", "-map_metadata", "0", "-id3v2_version", "3", "-write_xing", "0", newfilepath], capture_output=True, text=True)

                            if result_convert_file.returncode == 0:
                                print(term.green("SUCCESS (CONVERT)"))
                                logging.info("CONVERT - SUCCESS: "+originalfilepath+" -> "+newfilepath)
                                counters["convert_success"] += 1
                            else:
                                print(term.red("FAIL"))
                                logging.warning("CONVERT - FAIL: "+originalfilepath+" -> "+newfilepath)
                                print(term.red("[ERROR] There was an error during the conversion process!"))
                                logging.error("There was an error during the conversion process!")
                                counters["convert_failure"] += 1
                        else:
                            print(term.red("FAIL"))
                            logging.warning("CONVERT - FAIL: "+originalfilepath+" -> "+newfilepath)
                            print(term.red("[ERROR] There was a problem while extracting the cover!"))
                            logging.error("There was a problem while extracting the cover!")
                            
                            counters["convert_failure"] += 1
                            
                        if os.path.exists(extracted_cover_filename):
                            os.remove(extracted_cover_filename)      
                        if os.path.exists(new_cover_filename):
                            os.remove(new_cover_filename)
                else:
                    result_convert_file = subprocess.run(["ffmpeg", "-i", originalfilepath, "-hide_banner", "-loglevel", "quiet", "-c:v", "copy", "-b:a", "320k", "-map_metadata", "0", "-c:a", "mp3", "-id3v2_version", "3", "-write_xing", "0", newfilepath], capture_output=True)
                    
                    if result_convert_file.returncode == 0:
                        print(term.green("SUCCESS (TO MP3 ONLY)"))
                        logging.info("CONVERT - SUCCESS: "+originalfilepath+" -> "+newfilepath)
                        counters["convert_success"] += 1
                    else:
                        print(term.red("FAIL"))
                        logging.warning("CONVERT - FAIL: "+originalfilepath+" -> "+newfilepath)
                        print(term.red("[ERROR] There was an error during the conversion process!"))
                        logging.error("There was an error during the conversion process!")
                        counters["convert_failure"] += 1
        elif extension == "lrc":
            newfilepath = os.path.join(newpath, filename)
            
            if settings["copy_lyrics"]:
                if os.path.exists(os.path.join(root, name+".mp3")) or os.path.exists(os.path.join(root, name+".flac")):
                    if os.path.exists(newfilepath):
                        print("{term.bright_magenta}[EXISTS] {term.bright_blue}{0}".format(newfilepath, term=term))
                        logging.info("EXISTS: "+newfilepath)
                        counters["exists"] += 1
                    else:
                        result_copy = shutil.copyfile(originalfilepath, newfilepath)
                        
                        print("{term.bright_yellow}[COPY LRC] {term.bright_blue}{0} {term.normal}-> {term.bright_cyan}{1}{term.normal}... ".format(originalfilepath, newfilepath, term=term), end="")
                        
                        if os.path.exists(newfilepath) and os.path.samefile(newfilepath, result_copy):
                            print(term.green("SUCCESS"))
                            logging.info("COPY LRC - SUCCESS: "+originalfilepath+" -> "+newfilepath)
                            counters["lrc_copy_success"] += 1
                        else:
                            print(term.red("FAIL"))
                            logging.warning("COPY LRC - FAIL: "+originalfilepath+" -> "+newfilepath)
                            counters["lrc_copy_failure"] += 1

#Get elapsed Time
endtime = time.time()
timetaken = endtime - starttime

print(term.green("\nDONE in "+str(timetaken)+" seconds!"))
logging.info("")
logging.info("DONE in "+str(timetaken)+" seconds!")

totalfiles = 0
for key in counters:
    totalfiles += counters[key]

summarystring = summarytext.format(totalfiles, counters["convert_success"], counters["convert_failure"], counters["copy_success"], counters["copy_failure"], counters["exists"], counters["lrc_copy_success"], counters["lrc_copy_failure"])

print(term.bold_bright_green(summarystring))
for s in summarystring.split("\n"):
    logging.info(s)