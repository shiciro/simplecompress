import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Constants
WEBP_QUALITY = '90'
V_CODEC_WEBM = 'libvpx'
A_CODEC_WEBM = 'libvorbis'
CRF_WEBM = '47'
DELETE_ORIGINALS = True
LOG_FILE = 'conversion_log.txt'

# Add CREATE_NO_WINDOW for Windows
CREATE_NO_WINDOW = 0x08000000 if sys.platform.startswith('win') else 0

def clearConsole():
  if sys.platform.startswith('win'):
    os.system('cls')
  else:
    os.system('clear')

def getVideoDimensions(videoPath):
  try:
    result = subprocess.run(
      ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', videoPath],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      creationflags=CREATE_NO_WINDOW
    )
    output = result.stdout.strip()
    dimensions = output.split('x')
    if len(dimensions) >= 2:
      return map(int, dimensions[:2])
  except Exception as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error getting dimensions for {videoPath}: {e}\n")
  return None, None

def moveUnpairedFiles(folder1, folder2, outputFolder):
  os.makedirs(outputFolder, exist_ok=True)
  
  files1 = os.listdir(folder1)
  files2 = os.listdir(folder2)
  
  baseNames1 = {os.path.splitext(f)[0] for f in files1}
  baseNames2 = {os.path.splitext(f)[0] for f in files2}
  
  unpairedInFolder1 = baseNames1 - baseNames2
  unpairedInFolder2 = baseNames2 - baseNames1
  
  for file in files1:
    baseName = os.path.splitext(file)[0]
    if baseName in unpairedInFolder1:
      shutil.move(os.path.join(folder1, file), os.path.join(outputFolder, file))
  
  for file in files2:
    baseName = os.path.splitext(file)[0]
    if baseName in unpairedInFolder2:
      shutil.move(os.path.join(folder2, file), os.path.join(outputFolder, file))

  print(f"Unpaired files have been moved to: {outputFolder}")

def processImage(imagePath, outputFolder, movedFolder):
  filename = str(imagePath)
  filenameOut = os.path.join(outputFolder, f'{imagePath.stem}.webp')
  try:
    subprocess.check_call(
      ['cwebp', '-q', WEBP_QUALITY, filename, '-o', filenameOut],
      creationflags=CREATE_NO_WINDOW
    )
    with open(LOG_FILE, 'a') as f:
      f.write(f"Processed image: {filename} -> {filenameOut}\n")
  except subprocess.CalledProcessError as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error converting image: {filename}: {e}\n")
    return
  
  if imagePath.suffix.lower() == '.png':
    try:
      im = Image.open(filename)
      userComment = im.info.get('parameters', '')
      subprocess.check_call(
        ['exiftool', '-overwrite_original', f'-UserComment={userComment}', filenameOut],
        creationflags=CREATE_NO_WINDOW
      )
    except Exception as e:
      with open(LOG_FILE, 'a') as f:
        f.write(f"Error processing PNG metadata for {filename}: {e}\n")
  
  os.utime(filenameOut, (os.path.getmtime(filename), os.path.getmtime(filename)))
  
  if not os.path.exists(filenameOut):
    with open(LOG_FILE, 'a') as f:
      f.write(f"Failed to create compressed file for: {filename}\n")
    return
  
  originalSize = os.path.getsize(filename)
  compressedSize = os.path.getsize(filenameOut)
  
  if originalSize < compressedSize:
    shutil.copy2(filename, filenameOut)
    os.remove(filenameOut)
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed file larger than original, kept original: {filename}\n")

  if DELETE_ORIGINALS:
    os.makedirs(movedFolder, exist_ok=True)
    shutil.move(filename, movedFolder)
    with open(LOG_FILE, 'a') as f:
      f.write(f"Moved original image to backup: {filename}\n")

def processVideo(videoPath, outputFolder, movedFolder):
  filename = str(videoPath)
  filenameOut = os.path.join(outputFolder, f'{videoPath.stem}.webm')
  
  width, height = getVideoDimensions(filename)
  if width is None or height is None:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error getting dimensions for video: {filename}\n")
    return
  
  scale = f"640:-2" if width > height else f"-2:640"
  codec = V_CODEC_WEBM
  
  try:
    subprocess.check_call(
      [
        'ffmpeg', '-i', filename, '-vf', f'scale={scale}',
        '-c:v', codec, '-crf', CRF_WEBM, '-b:v', '1M', '-c:a', A_CODEC_WEBM,
        filenameOut
      ],
      creationflags=CREATE_NO_WINDOW
    )
    with open(LOG_FILE, 'a') as f:
      f.write(f"Processed video: {filename} -> {filenameOut}\n")
  except subprocess.CalledProcessError as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error compressing video: {filename}: {e}\n")
    return
  
  originalSize = os.path.getsize(filename)
  compressedSize = os.path.getsize(filenameOut)
  
  if compressedSize >= originalSize:
    os.remove(filenameOut)
    shutil.copy(filename, filenameOut)
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed video larger than original, kept original: {filename}\n")
  else:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed video is smaller, kept compressed: {filename}\n")

  if DELETE_ORIGINALS:
    os.makedirs(movedFolder, exist_ok=True)
    shutil.move(filename, movedFolder)
    with open(LOG_FILE, 'a') as f:
      f.write(f"Moved original video to backup: {filename}\n")

def main():
  clearConsole()
  inputPath = input('Enter the directory path: ')
  inputFolderName = os.path.basename(os.path.normpath(inputPath))
  outputFolder = f'{inputFolderName}_compressed'
  movedFolder = f'{inputFolderName}_originals_backup'
  unpairedFolder = f'{inputFolderName}_unpaired'
  os.makedirs(outputFolder, exist_ok=True)
  os.makedirs(movedFolder, exist_ok=True)
  os.makedirs(unpairedFolder, exist_ok=True)
  
  with open(LOG_FILE, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(f"\n--- Script Execution Started: {timestamp} ---\n")
  
  files = [os.path.join(inputPath, file) for file in os.listdir(inputPath) if os.path.isfile(os.path.join(inputPath, file))]
  
  with ThreadPoolExecutor() as executor:
    for filePath in files:
      if filePath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        executor.submit(processImage, Path(filePath), outputFolder, movedFolder)
      elif filePath.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')):
        executor.submit(processVideo, Path(filePath), outputFolder, movedFolder)
  
  moveUnpairedFiles(outputFolder, movedFolder, unpairedFolder)
  
  with open(LOG_FILE, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(f"--- Script Execution Ended: {timestamp} ---\n")

if __name__ == '__main__':
  main()