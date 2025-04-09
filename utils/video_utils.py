import os
import shutil
import subprocess
import logging  # Import logging module
from pathlib import Path
from config import CRF_WEBM, HIDE_CMD_WINDOWS, MOVE_ORIGINALS_TO_BACKUP, LOG_FILE, CREATE_NO_WINDOW, DEFAULT_SCALE_WIDTH, DEFAULT_SCALE_HEIGHT, WEBM_BITRATE  # Use absolute import
from datetime import datetime  # Import datetime for timestamps

V_CODEC_WEBM = 'libvpx'  # Video codec for WebM
A_CODEC_WEBM = 'libvorbis'  # Audio codec for WebM

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')  # Configure logging

def getVideoDimensions(videoPath):
  try:
    result = subprocess.run(
      ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', videoPath],
      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=CREATE_NO_WINDOW
    )  # Run ffprobe to get video dimensions
    output = result.stdout.strip()  # Trim the output
    dimensions = output.split('x')  # Split dimensions
    if len(dimensions) >= 2:
      return map(int, dimensions[:2])  # Return width and height as integers
  except Exception as e:
    logging.error(f"Error getting dimensions for {videoPath}: {e}")  # Log error
  return None, None  # Return None if dimensions cannot be retrieved

def processVideo(videoPath, outputFolder, movedFolder):
  filename = str(videoPath)  # Convert Path object to string
  filenameOut = os.path.join(outputFolder, f'{videoPath.stem}.webm')  # Output file path

  width, height = getVideoDimensions(filename)  # Get video dimensions
  if width is None or height is None:
    logging.error(f"Error getting dimensions for video: {filename}")  # Log error
    return
  
  scale = f'{DEFAULT_SCALE_WIDTH}:-2' if width > height else f'-2:{DEFAULT_SCALE_HEIGHT}'  # Determine scale parameters
  
  try:
    subprocess.check_call(
      [
        'ffmpeg', '-y', '-i', filename, '-vf', f'scale={scale}',
        '-c:v', V_CODEC_WEBM, '-crf', CRF_WEBM, '-b:v', WEBM_BITRATE, '-c:a', A_CODEC_WEBM,
        filenameOut
      ],
      creationflags=CREATE_NO_WINDOW
    )  # Convert to WebM
    logging.info(f"Processed video: {filename} -> {filenameOut}")  # Log success

    # Set the modified date of the compressed file to match the original
    try:
      os.utime(filenameOut, (os.path.getatime(filename), os.path.getmtime(filename)))  # Update timestamps
    except FileNotFoundError:
      logging.error(f"Error updating timestamps for {filenameOut}: File not found")  # Log error
  except subprocess.CalledProcessError as e:
    logging.error(f"Error compressing video: {filename}: {e}")  # Log error
    return
  
  originalSize = os.path.getsize(filename)  # Get original file size
  compressedSize = os.path.getsize(filenameOut)  # Get compressed file size
  
  if compressedSize >= originalSize:  # Check if the compressed file is larger
    os.remove(filenameOut)  # Delete the compressed file
    shutil.copy(filename, filenameOut)  # Copy original to output folder
    logging.info(f"Compressed video larger than original, kept original: {filename}")  # Log decision
  else:
    logging.info(f"Compressed video is smaller, kept compressed: {filename}")  # Log decision

  if MOVE_ORIGINALS_TO_BACKUP:  # Check if originals should be moved
    os.makedirs(movedFolder, exist_ok=True)  # Ensure the backup folder exists
    shutil.move(filename, movedFolder)  # Move original to backup folder
    logging.info(f"Moved original video to backup: {filename}")  # Log move