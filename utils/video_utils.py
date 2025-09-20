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
      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, creationflags=CREATE_NO_WINDOW
    )
    output = result.stdout.strip()
    dimensions = output.split('x')
    if len(dimensions) >= 2:
      return map(int, dimensions[:2])
  except Exception as e:
    logging.error(f"Error getting dimensions for {videoPath}: {e}")
  return None, None

def processVideo(videoPath, outputFolder, movedFolder):
  filename = str(videoPath)
  filenameOut = os.path.join(outputFolder, f'{videoPath.stem}.webm')
  messages = []
  status = 'success'

  width, height = getVideoDimensions(filename)
  if width is None or height is None:
    status = 'error'
    messages.append(f"Error getting dimensions for video: {filename}")
    return {'status': status, 'messages': messages, 'file': filename}

  scale = f'{DEFAULT_SCALE_WIDTH}:-2' if width > height else f'-2:{DEFAULT_SCALE_HEIGHT}'

  try:
    subprocess.check_call(
      [
        'ffmpeg', '-y', '-i', filename, '-vf', f'scale={scale}',
        '-c:v', V_CODEC_WEBM, '-crf', CRF_WEBM, '-b:v', WEBM_BITRATE, '-c:a', A_CODEC_WEBM,
        filenameOut
      ],
      creationflags=CREATE_NO_WINDOW,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL
    )
    messages.append(f"Processed video: {filename} -> {filenameOut}")

    try:
      original_atime = os.path.getatime(filename)
      original_mtime = os.path.getmtime(filename)
      os.utime(filenameOut, (original_atime, original_mtime))
      messages.append(f"Timestamps updated for: {filenameOut}")
    except Exception as e:
      status = 'error'
      messages.append(f"Error updating timestamps for {filenameOut}: {e}")
  except subprocess.CalledProcessError as e:
    status = 'error'
    messages.append(f"Error compressing video: {filename}: {e}")
    return {'status': status, 'messages': messages, 'file': filename}

  originalSize = os.path.getsize(filename)
  compressedSize = os.path.getsize(filenameOut)

  if compressedSize >= originalSize:
    os.remove(filenameOut)
    shutil.copy(filename, filenameOut)
    try:
      original_atime = os.path.getatime(filename)
      original_mtime = os.path.getmtime(filename)
      os.utime(filenameOut, (original_atime, original_mtime))
      messages.append(f"Timestamps updated for copied file: {filenameOut}")
    except Exception as e:
      status = 'error'
      messages.append(f"Error updating timestamps for copied file {filenameOut}: {e}")
    messages.append(f"Compressed video larger than original, kept original: {filename}")
  else:
    messages.append(f"Compressed video is smaller, kept compressed: {filename}")

  if MOVE_ORIGINALS_TO_BACKUP:
    try:
      os.makedirs(movedFolder, exist_ok=True)
      shutil.move(filename, movedFolder)
      messages.append(f"Moved original video to backup: {filename}")
    except Exception as e:
      status = 'error'
      messages.append(f"Error moving original video to backup: {filename}: {e}")

  return {'status': status, 'messages': messages, 'file': filename}