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
from config import CRF_WEBM, WEBP_QUALITY, HIDE_CMD_WINDOWS, MOVE_ORIGINALS_TO_BACKUP, LOG_FILE, CREATE_NO_WINDOW

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
