import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from utils.console_utils import clearConsole
from utils.video_utils import processVideo, getVideoDimensions
from utils.image_utils import processImage
from utils.file_utils import moveUnpairedFiles
from utils.progress_utils import updateProgressBar

# Constants shared across the application
CRF_WEBM = '47'  # Constant Rate Factor for WebM
WEBP_QUALITY = '90'  # Quality for WebP compression
HIDE_CMD_WINDOWS = False  # Toggle to hide or show command prompt windows
MOVE_ORIGINALS_TO_BACKUP = True  # Flag to move original files to a backup folder after processing
LOG_FILE = 'conversion_log.txt'  # Log file for recording operations

# Adjust creation flags based on the operating system and toggle
CREATE_NO_WINDOW = 0x08000000 if HIDE_CMD_WINDOWS and os.name == 'nt' else 0

def main():
  clearConsole()
  inputPath = input('Enter the directory path: ')
  inputFolderName = os.path.basename(os.path.normpath(inputPath))
  
  outputFolder = os.path.join(inputPath, f'{inputFolderName}_compressed')
  movedFolder = os.path.join(inputPath, f'{inputFolderName}_originals_backup')
  unpairedFolder = os.path.join(inputPath, f'{inputFolderName}_unpaired')
  
  os.makedirs(outputFolder, exist_ok=True)
  os.makedirs(movedFolder, exist_ok=True)
  os.makedirs(unpairedFolder, exist_ok=True)
  
  with open(LOG_FILE, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(f"\n--- Script Execution Started: {timestamp} ---\n")
  
  files = [os.path.join(inputPath, file) for file in os.listdir(inputPath) if os.path.isfile(os.path.join(inputPath, file))]
  
  totalFiles = len(files)
  progressBar = updateProgressBar(totalFiles, 'Processing Files')
  
  with ThreadPoolExecutor() as executor:
    for filePath in files:
      if filePath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        executor.submit(lambda p: (
          processImage(Path(p), outputFolder, movedFolder),  # Process the image
          shutil.move(p, os.path.join(movedFolder, os.path.basename(p))),  # Move the original file
          progressBar.update(1)  # Update the progress bar
        ), filePath)
      elif filePath.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')):
        executor.submit(lambda p: (
          processVideo(Path(p), outputFolder, movedFolder),  # Process the video
          progressBar.update(1)  # Update the progress bar
        ), filePath)
  
  progressBar.close()
  moveUnpairedFiles(outputFolder, movedFolder, unpairedFolder)
  
  with open(LOG_FILE, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(f"--- Script Execution Ended: {timestamp} ---\n")

if __name__ == '__main__':
  main()
