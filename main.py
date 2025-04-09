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
from config import USE_THREAD_POOL_FOR_IMAGES, USE_THREAD_POOL_FOR_VIDEOS  # Import new constants

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
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
    f.write(f"[{timestamp}] --- Script Execution Started ---\n")  # Log start time
  
  files = [os.path.join(inputPath, file) for file in os.listdir(inputPath) if os.path.isfile(os.path.join(inputPath, file))]
  
  totalFiles = len(files)
  progressBar = updateProgressBar(totalFiles, 'Processing Files')
  
  with ThreadPoolExecutor() as executor:  # Use ThreadPoolExecutor for parallel processing
    for filePath in files:
      if filePath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):  # Check for image files
        if USE_THREAD_POOL_FOR_IMAGES:  # Check if threading is enabled for images
          executor.submit(lambda p: (
            processImage(Path(p), outputFolder, movedFolder),  # Process the image
            progressBar.update(1)  # Update the progress bar
          ), filePath)
        else:
          processImage(Path(filePath), outputFolder, movedFolder)  # Process sequentially
          progressBar.update(1)  # Update the progress bar
      elif filePath.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')):  # Check for video files
        if USE_THREAD_POOL_FOR_VIDEOS:  # Check if threading is enabled for videos
          executor.submit(lambda p: (
            processVideo(Path(p), outputFolder, movedFolder),  # Process the video
            progressBar.update(1)  # Update the progress bar
          ), filePath)
        else:
          processVideo(Path(filePath), outputFolder, movedFolder)  # Process sequentially
          progressBar.update(1)  # Update the progress bar
  
  progressBar.close()
  moveUnpairedFiles(outputFolder, movedFolder, unpairedFolder)
  
  with open(LOG_FILE, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
    f.write(f"[{timestamp}] --- Script Execution Ended ---\n")  # Log end time

if __name__ == '__main__':

  main()
