import os
import sys
import shutil
import threading  # Import threading for key listener
import keyboard  # Import keyboard module for key press detection
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
from config import USE_THREAD_POOL_FOR_IMAGES, USE_THREAD_POOL_FOR_VIDEOS  # Import new constants
from utils.dependency_utils import checkDependencies  # Import the moved function

# Configure logging
logging.basicConfig(
  filename=LOG_FILE,  # Log file path
  level=logging.INFO,  # Set default log level to INFO
  format='%(asctime)s - %(levelname)s - %(message)s'  # Log format with timestamp, level, and message
)

# Global flags for pause and cancel
isPaused = False
isCancelled = False

def keyListener():
  global isPaused, isCancelled
  while True:
    if keyboard.is_pressed('p'):  # Listen for 'p' to pause/resume
      isPaused = not isPaused
      print('\nProcessing paused. Press "p" again to resume.') if isPaused else print('\nProcessing resumed.')
      while keyboard.is_pressed('p'):  # Wait for key release
        pass
    elif keyboard.is_pressed('c'):  # Listen for 'c' to cancel
      confirm = input('\nAre you sure you want to cancel? (y/n): ')
      if confirm.lower() == 'y':
        isCancelled = True
        break
      else:
        print('Cancel aborted.')
    if isCancelled:
      break

def logConstants():
  constants = {
    'CRF_WEBM': CRF_WEBM,
    'WEBP_QUALITY': WEBP_QUALITY,
    'HIDE_CMD_WINDOWS': HIDE_CMD_WINDOWS,
    'MOVE_ORIGINALS_TO_BACKUP': MOVE_ORIGINALS_TO_BACKUP,
    'LOG_FILE': LOG_FILE,
    'CREATE_NO_WINDOW': CREATE_NO_WINDOW,
    'USE_THREAD_POOL_FOR_IMAGES': USE_THREAD_POOL_FOR_IMAGES,
    'USE_THREAD_POOL_FOR_VIDEOS': USE_THREAD_POOL_FOR_VIDEOS
  }  # Define constants to log

  print('\nCurrent Constants:')
  logging.info('Current Constants:')
  for key, value in constants.items():
    print(f'{key}: {value}')  # Print constant name and value
    logging.info(f'{key}: {value}')  # Log constant name and value

def main():
  global isPaused, isCancelled
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
  
  logConstants()  # Log and print constants at the start of the script

  files = [os.path.join(inputPath, file) for file in os.listdir(inputPath) if os.path.isfile(os.path.join(inputPath, file))]
  
  totalFiles = len(files)
  progressBar = updateProgressBar(totalFiles, 'Processing Files')
  
  # Start the key listener thread
  listenerThread = threading.Thread(target=keyListener, daemon=True)
  listenerThread.start()

  with ThreadPoolExecutor() as executor:  # Use ThreadPoolExecutor for parallel processing
    for filePath in files:
      while isPaused:  # Pause processing if isPaused is True
        pass
      if isCancelled:  # Stop processing if isCancelled is True
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
        print(f'\n[{timestamp}] Processing cancelled by user.')  # Print with timestamp
        logging.info(f"[{timestamp}] Processing cancelled by user.")
        break
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
  if not isCancelled:
    moveUnpairedFiles(outputFolder, movedFolder, unpairedFolder)
  
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
  logging.info(f"[{timestamp}] --- Script Execution Ended ---")  # Log end time

if __name__ == '__main__':
  #checkDependencies()
  main()
