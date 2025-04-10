import os
import shutil
from pathlib import Path
from PIL import Image
import subprocess
from config import WEBP_QUALITY, MOVE_ORIGINALS_TO_BACKUP, LOG_FILE, CREATE_NO_WINDOW, LOG_METADATA  # Import shared constants
from datetime import datetime  # Import datetime for timestamps
import logging  # Import logging module

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')

def handleFileConflict(filePath, outputFolder, movedFolder):
  baseName = os.path.splitext(os.path.basename(filePath))[0]
  conflictFolder = os.path.join(outputFolder, f'{baseName}_conflict')

  conflictDetected = False

  outputFile = os.path.join(outputFolder, f'{baseName}.webp')
  if os.path.exists(outputFile):
    os.makedirs(conflictFolder, exist_ok=True)
    shutil.move(outputFile, os.path.join(conflictFolder, os.path.basename(outputFile)))
    conflictDetected = True

  originalFile = os.path.join(movedFolder, os.path.basename(filePath))
  if os.path.exists(originalFile):
    os.makedirs(conflictFolder, exist_ok=True)
    shutil.move(originalFile, os.path.join(conflictFolder, os.path.basename(originalFile)))
    conflictDetected = True

  if not conflictDetected and os.path.exists(conflictFolder):
    os.rmdir(conflictFolder)

  if conflictDetected:
    logging.info(f"Conflicting files moved to: {conflictFolder}")  # Log conflict resolution message

def processImage(imagePath, outputFolder, movedFolder):
  filename = str(imagePath)
  filenameOut = os.path.join(outputFolder, f'{imagePath.stem}.webp')

  if os.path.exists(filenameOut) or os.path.exists(os.path.join(movedFolder, os.path.basename(filename))):
    handleFileConflict(filename, outputFolder, movedFolder)

  try:
    subprocess.check_call(
      ['cwebp', '-q', WEBP_QUALITY, filename, '-o', filenameOut],
      creationflags=CREATE_NO_WINDOW
    )
    logging.info(f"Processed image: {filename} -> {filenameOut}")  # Log success
  except subprocess.CalledProcessError as e:
    logging.error(f"Error converting image: {filename}: {e}")  # Log error
    return

  if imagePath.suffix.lower() == '.png':
    try:
      with Image.open(filename) as im:  # Ensure the Image object is properly closed
        userComment = im.info.get('parameters', '')  # Extract metadata
        prompt = im.info.get('prompt', '')  # Extract 'prompt' metadata
        workflow = im.info.get('workflow', '')  # Extract 'workflow' metadata

        # Ensure metadata fields are properly formatted for exiftool
        userComment = userComment.replace('"', '\\"')  # Escape double quotes
        prompt = prompt.replace('"', '\\"')  # Escape double quotes
        workflow = workflow.replace('"', '\\"')  # Escape double quotes

        # Log metadata values for debugging if enabled
        if LOG_METADATA:
          logging.info(f"Read metadata for {filename}: parameters='{userComment}', prompt='{prompt}', workflow='{workflow}'")

      subprocess.check_call(
        ['exiftool', '-overwrite_original', 
         f'-UserComment={userComment}', 
         f'-Prompt={prompt}', 
         f'-Workflow={workflow}', 
         filenameOut],
        creationflags=CREATE_NO_WINDOW
      )  # Add metadata to the compressed file
    except subprocess.CalledProcessError as e:
      logging.error(f"Error copying metadata to {filenameOut}: {e}")  # Log error
    except Exception as e:
      logging.error(f"Error processing PNG metadata for {filename}: {e}")  # Log error
  
  try:
    os.utime(filenameOut, (os.path.getmtime(filename), os.path.getmtime(filename)))  # Update timestamps
  except FileNotFoundError:
    logging.error(f"Error updating timestamps for {filenameOut}: File not found")  # Log error
  
  if not os.path.exists(filenameOut):
    logging.error(f"Failed to create compressed file for: {filename}")
    return

  originalSize = os.path.getsize(filename)
  compressedSize = os.path.getsize(filenameOut)

  if compressedSize >= originalSize:
    os.remove(filenameOut)
    shutil.copy2(filename, filenameOut)
    logging.info(f"Compressed file larger than original, kept original: {filename}")

  if MOVE_ORIGINALS_TO_BACKUP:
    try:
      os.makedirs(movedFolder, exist_ok=True)
      shutil.move(filename, os.path.join(movedFolder, os.path.basename(filename)))
      logging.info(f"Moved original image to backup: {filename}")
    except Exception as e:
      logging.error(f"Error moving original image to backup: {filename}: {e}")