import os
import shutil
import subprocess
from pathlib import Path
from ..main import CRF_WEBM, HIDE_CMD_WINDOWS, MOVE_ORIGINALS_TO_BACKUP, LOG_FILE, CREATE_NO_WINDOW  # Import shared constants

V_CODEC_WEBM = 'libvpx'  # Video codec for WebM
A_CODEC_WEBM = 'libvorbis'  # Audio codec for WebM

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
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error getting dimensions for {videoPath}: {e}\n")  # Log error
  return None, None  # Return None if dimensions cannot be retrieved

def processVideo(videoPath, outputFolder, movedFolder):
  filename = str(videoPath)  # Convert Path object to string
  filenameOut = os.path.join(outputFolder, f'{videoPath.stem}.webm')  # Output file path

  width, height = getVideoDimensions(filename)  # Get video dimensions
  if width is None or height is None:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error getting dimensions for video: {filename}\n")  # Log error
    return
  
  scale = f"640:-2" if width > height else f"-2:640"  # Determine scale parameters
  
  try:
    subprocess.check_call(
      [
        'ffmpeg', '-y', '-i', filename, '-vf', f'scale={scale}',
        '-c:v', V_CODEC_WEBM, '-crf', CRF_WEBM, '-b:v', '1M', '-c:a', A_CODEC_WEBM,
        filenameOut
      ],
      creationflags=CREATE_NO_WINDOW
    )  # Convert to WebM
    with open(LOG_FILE, 'a') as f:
      f.write(f"Processed video: {filename} -> {filenameOut}\n")  # Log success
  except subprocess.CalledProcessError as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error compressing video: {filename}: {e}\n")  # Log error
    return
  
  originalSize = os.path.getsize(filename)  # Get original file size
  compressedSize = os.path.getsize(filenameOut)  # Get compressed file size
  
  if compressedSize >= originalSize:  # Check if the compressed file is larger
    os.remove(filenameOut)  # Delete the compressed file
    shutil.copy(filename, filenameOut)  # Copy original to output folder
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed video larger than original, kept original: {filename}\n")  # Log decision
  else:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed video is smaller, kept compressed: {filename}\n")  # Log decision

  if MOVE_ORIGINALS_TO_BACKUP:  # Check if originals should be moved
    os.makedirs(movedFolder, exist_ok=True)  # Ensure the backup folder exists
    shutil.move(filename, movedFolder)  # Move original to backup folder
    with open(LOG_FILE, 'a') as f:
      f.write(f"Moved original video to backup: {filename}\n")  # Log move