import os
import shutil
from datetime import datetime  # Import datetime for timestamps
import logging  # Import logging module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def moveUnpairedFiles(folder1, folder2, outputFolder):
  os.makedirs(outputFolder, exist_ok=True)  # Ensure the output folder exists
  
  files1 = os.listdir(folder1)  # List files in folder1
  files2 = os.listdir(folder2)  # List files in folder2
  
  baseNames1 = {os.path.splitext(f)[0] for f in files1}  # Get base names from folder1
  baseNames2 = {os.path.splitext(f)[0] for f in files2}  # Get base names from folder2
  
  unpairedInFolder1 = baseNames1 - baseNames2  # Find unpaired files in folder1
  unpairedInFolder2 = baseNames2 - baseNames1  # Find unpaired files in folder2
  
  for file in files1:
    baseName = os.path.splitext(file)[0]  # Get base name
    if baseName in unpairedInFolder1:
      src = os.path.join(folder1, file)  # Source file path
      dst = os.path.join(outputFolder, file)  # Destination file path
      try:
        shutil.move(src, dst)  # Attempt to move the file
        logging.info(f"Moved unpaired file from {folder1} to {outputFolder}: {file}")  # Log success
      except OSError:
        shutil.copy2(src, dst)  # Copy the file if move fails
        os.remove(src)  # Delete the original file
        logging.info(f"Copied and removed unpaired file from {folder1} to {outputFolder}: {file}")  # Log fallback

  for file in files2:
    baseName = os.path.splitext(file)[0]  # Get base name
    if baseName in unpairedInFolder2:
      src = os.path.join(folder2, file)  # Source file path
      dst = os.path.join(outputFolder, file)  # Destination file path
      try:
        shutil.move(src, dst)  # Attempt to move the file
        logging.info(f"Moved unpaired file from {folder2} to {outputFolder}: {file}")  # Log success
      except OSError:
        shutil.copy2(src, dst)  # Copy the file if move fails
        os.remove(src)  # Delete the original file
        logging.info(f"Copied and removed unpaired file from {folder2} to {outputFolder}: {file}")  # Log fallback

  logging.info(f"Unpaired files have been successfully moved to: {outputFolder}")  # Print completion message

def handleFileConflict(filePath, outputFolder, movedFolder):
  """
  Handle file name conflicts by moving conflicting files to a new folder with a '_conflict' suffix.
  :param filePath: Path of the input file.
  :param outputFolder: Path of the output folder.
  :param movedFolder: Path of the originals backup folder.
  """
  baseName = os.path.splitext(os.path.basename(filePath))[0]  # Get base name of the file
  conflictFolder = os.path.join(outputFolder, f'{baseName}_conflict')  # Create conflict folder path

  conflictDetected = False  # Track if a conflict is detected

  # Check and move conflicting files from outputFolder
  outputFile = os.path.join(outputFolder, f'{baseName}.webp')
  if os.path.exists(outputFile):
    os.makedirs(conflictFolder, exist_ok=True)  # Ensure the conflict folder exists
    shutil.move(outputFile, os.path.join(conflictFolder, os.path.basename(outputFile)))  # Move conflicting output file
    conflictDetected = True

  # Check and move conflicting files from movedFolder
  originalFile = os.path.join(movedFolder, os.path.basename(filePath))
  if os.path.exists(originalFile):
    os.makedirs(conflictFolder, exist_ok=True)  # Ensure the conflict folder exists
    shutil.move(originalFile, os.path.join(conflictFolder, os.path.basename(originalFile)))  # Move conflicting original file
    conflictDetected = True

  # Remove the conflict folder if no conflicts were detected
  if not conflictDetected and os.path.exists(conflictFolder):
    os.rmdir(conflictFolder)  # Remove the empty conflict folder

  if conflictDetected:
    logging.info(f"Conflicting files moved to: {conflictFolder}")  # Print conflict resolution message