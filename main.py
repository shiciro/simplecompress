import os
import sys
import shutil
import threading  # Import threading for key listener
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import importlib  # Import importlib to check for module availability
import logging  # Import logging module

from utils.console_utils import clearConsole
from utils.video_utils import processVideo, getVideoDimensions
from utils.image_utils import processImage
from utils.file_utils import moveUnpairedFiles
from utils.progress_utils import updateProgressBar
from config import CRF_WEBM, WEBP_QUALITY, HIDE_CMD_WINDOWS, MOVE_ORIGINALS_TO_BACKUP, LOG_FILE, CREATE_NO_WINDOW
from config import USE_THREAD_POOL_FOR_IMAGES, USE_THREAD_POOL_FOR_VIDEOS, ENABLE_DEPENDENCY_CHECK, LOG_METADATA  # Removed ENABLE_KEYBOARD_CHECK
from utils.dependency_utils import checkDependencies  # Import the moved function

# Configure logging
logging.basicConfig(
  filename=LOG_FILE,  # Log file path
  level=logging.INFO,  # Set default log level to INFO
  format='%(asctime)s - %(levelname)s - %(message)s'  # Log format with timestamp, level, and message
)

def logConstants():
  constants = {
    'CRF_WEBM': CRF_WEBM,
    'WEBP_QUALITY': WEBP_QUALITY,
    'HIDE_CMD_WINDOWS': HIDE_CMD_WINDOWS,
    'MOVE_ORIGINALS_TO_BACKUP': MOVE_ORIGINALS_TO_BACKUP,
    'LOG_FILE': LOG_FILE,
    'LOG_METADATA': LOG_METADATA,
    'CREATE_NO_WINDOW': CREATE_NO_WINDOW,
    'USE_THREAD_POOL_FOR_IMAGES': USE_THREAD_POOL_FOR_IMAGES,
    'USE_THREAD_POOL_FOR_VIDEOS': USE_THREAD_POOL_FOR_VIDEOS,
    'ENABLE_DEPENDENCY_CHECK': ENABLE_DEPENDENCY_CHECK
  }  # Removed ENABLE_KEYBOARD_CHECK

  print('\nCurrent Constants:')
  logging.info('Current Constants:')
  for key, value in constants.items():
    print(f'{key}: {value}')  # Print constant name and value
    logging.info(f'{key}: {value}')  # Log constant name and value

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
  
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
  logging.info(f"[{timestamp}] --- Script Execution Started ---")  # Log start time
  logging.info(f"Input folder: {inputPath}")  # Log input folder
  logging.info(f"Output folder: {outputFolder}")  # Log output folder
  logging.info(f"Backup folder: {movedFolder}")  # Log backup folder
  logging.info(f"Unpaired folder: {unpairedFolder}")  # Log unpaired folder
  
  logConstants()  # Log and print constants at the start of the script

  files = [os.path.join(inputPath, file) for file in os.listdir(inputPath) if os.path.isfile(os.path.join(inputPath, file))]
  
  totalFiles = len(files)
  logging.info(f"Total files to process: {totalFiles}")  # Log total file count
  progressBar = updateProgressBar(totalFiles, 'Processing Files')

  with ThreadPoolExecutor() as executor:  # Use ThreadPoolExecutor for parallel processing
    for filePath in files:
      if filePath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):  # Check for image files
        logging.info(f"Processing image file: {filePath}")  # Log image file being processed
        if USE_THREAD_POOL_FOR_IMAGES:  # Check if threading is enabled for images
          executor.submit(lambda p: (
            processImage(Path(p), outputFolder, movedFolder),  # Process the image
            progressBar.update(1)  # Update the progress bar
          ), filePath)
        else:
          processImage(Path(filePath), outputFolder, movedFolder)  # Process sequentially
          progressBar.update(1)  # Update the progress bar
      elif filePath.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')):  # Check for video files
        logging.info(f"Processing video file: {filePath}")  # Log video file being processed
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
  logging.info("Unpaired files moved successfully.")  # Log unpaired file movement
  
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
  logging.info(f"[{timestamp}] --- Script Execution Ended ---")  # Log end time

if __name__ == '__main__':
  if ENABLE_DEPENDENCY_CHECK:  # Check if dependency check is enabled
    checkDependencies()  # Call dependency check
  main()
