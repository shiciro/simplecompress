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
  clearConsole()  # Clear the console
  inputPath = input('Enter the directory path: ')  # Get input path from user

  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
  logging.info(f"[{timestamp}] --- Script Execution Started ---")  # Log start time
  logging.info(f"Input folder: {inputPath}")  # Log input folder

  logConstants()  # Log and print constants at the start of the script

  filesToProcess = []  # List to collect (filePath, outputFolder, movedFolder, unpairedFolder)

  # Walk through all subdirectories, skipping ignored folders
  for root, dirs, filenames in os.walk(inputPath):
    folderName = os.path.basename(os.path.normpath(root))  # Get current folder name

    # Define output, backup, and unpaired folders for this subfolder
    outputFolder = os.path.join(root, f'{folderName}_compressed')
    movedFolder = os.path.join(root, f'{folderName}_originals_backup')
    unpairedFolder = os.path.join(root, f'{folderName}_unpaired')

    # Ignore traversing into any of these folders
    ignoreFolders = {
      os.path.basename(outputFolder),
      os.path.basename(movedFolder),
      os.path.basename(unpairedFolder)
    }
    dirs[:] = [d for d in dirs if d not in ignoreFolders]

    filesInThisFolder = []  # Collect files for this folder

    for file in filenames:
      filePath = os.path.join(root, file)
      # Skip files inside any of the special folders
      if any(filePath.startswith(os.path.join(root, f'{folderName}_{suffix}')) for suffix in ['compressed', 'originals_backup', 'unpaired']):
        continue
      filesInThisFolder.append((filePath, outputFolder, movedFolder, unpairedFolder))

    if filesInThisFolder:  # Only create folders if there are files to process
      os.makedirs(outputFolder, exist_ok=True)
      os.makedirs(movedFolder, exist_ok=True)
      os.makedirs(unpairedFolder, exist_ok=True)
      filesToProcess.extend(filesInThisFolder)

  totalFiles = len(filesToProcess)  # Count total files
  logging.info(f"Total files to process: {totalFiles}")  # Log total file count


  from concurrent.futures import as_completed
  progressBar = tqdm(total=totalFiles, desc='Processing Files', ncols=80)
  futures = []
  results = []

  with ThreadPoolExecutor() as executor:
    for filePath, outputFolder, movedFolder, unpairedFolder in filesToProcess:
      ext = filePath.lower()
      if ext.endswith(('.jpg', '.jpeg', '.png', '.webp')) and USE_THREAD_POOL_FOR_IMAGES:
        futures.append(executor.submit(processImage, Path(filePath), outputFolder, movedFolder))
      elif ext.endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')) and USE_THREAD_POOL_FOR_VIDEOS:
        futures.append(executor.submit(processVideo, Path(filePath), outputFolder, movedFolder))
      else:
        # Process in main thread if not using thread pool
        if ext.endswith(('.jpg', '.jpeg', '.png', '.webp')):
          result = processImage(Path(filePath), outputFolder, movedFolder)
        elif ext.endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')):
          result = processVideo(Path(filePath), outputFolder, movedFolder)
        else:
          result = None
        if result:
          results.append(result)
        progressBar.update(1)

    for future in as_completed(futures):
      result = future.result()
      if result:
        results.append(result)
      progressBar.update(1)

  progressBar.close()

  # Centralized logging/output for all results (use tqdm.write to keep progress bar at bottom)
  for result in results:
    for msg in result.get('messages', []):
      if result['status'] == 'error':
        tqdm.write(f'[ERROR] {msg}')
        logging.error(msg)
      else:
        tqdm.write(msg)
        logging.info(msg)

  # Move unpaired files for each unique subfolder after processing
  uniqueFolders = set((outputFolder, movedFolder, unpairedFolder) for _, outputFolder, movedFolder, unpairedFolder in filesToProcess)  # Deduplicate folder triplets
  for outputFolder, movedFolder, unpairedFolder in uniqueFolders:
    moveUnpairedFiles(outputFolder, movedFolder, unpairedFolder)  # Move unpaired files for this subfolder

  logging.info('Processing complete.')

  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  logging.info(f'[{timestamp}] --- Script Execution Ended ---')

if __name__ == '__main__':
  if ENABLE_DEPENDENCY_CHECK:  # Check if dependency check is enabled
    checkDependencies()  # Call dependency check
  main()
