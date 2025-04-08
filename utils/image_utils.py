import os
import shutil
from pathlib import Path
from PIL import Image
import subprocess
from config import WEBP_QUALITY, MOVE_ORIGINALS_TO_BACKUP, LOG_FILE, CREATE_NO_WINDOW  # Import shared constants

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
    print(f'Conflicting files moved to: {conflictFolder}')

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
    with open(LOG_FILE, 'a') as f:
      f.write(f"Processed image: {filename} -> {filenameOut}\n")
  except subprocess.CalledProcessError as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error converting image: {filename}: {e}\n")
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

        # Log metadata values for debugging
        with open(LOG_FILE, 'a') as f:
          f.write(f"Read metadata for {filename}: parameters='{userComment}', prompt='{prompt}', workflow='{workflow}'\n")

      subprocess.check_call(
        ['exiftool', '-overwrite_original', 
         f'-UserComment={userComment}', 
         f'-Prompt={prompt}', 
         f'-Workflow={workflow}', 
         filenameOut],
        creationflags=CREATE_NO_WINDOW
      )  # Add metadata to the compressed file
    except subprocess.CalledProcessError as e:
      with open(LOG_FILE, 'a') as f:
        f.write(f"Error copying metadata to {filenameOut}: {e}\n")  # Log error
    except Exception as e:
      with open(LOG_FILE, 'a') as f:
        f.write(f"Error processing PNG metadata for {filename}: {e}\n")  # Log error
  
  try:
    os.utime(filenameOut, (os.path.getmtime(filename), os.path.getmtime(filename)))  # Update timestamps
  except FileNotFoundError:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error updating timestamps for {filenameOut}: File not found\n")  # Log error
  
  if not os.path.exists(filenameOut):
    with open(LOG_FILE, 'a') as f:
      f.write(f"Failed to create compressed file for: {filename}\n")
    return

  originalSize = os.path.getsize(filename)
  compressedSize = os.path.getsize(filenameOut)

  if compressedSize >= originalSize:
    os.remove(filenameOut)
    shutil.copy2(filename, filenameOut)
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed file larger than original, kept original: {filename}\n")

  if MOVE_ORIGINALS_TO_BACKUP:
    try:
      os.makedirs(movedFolder, exist_ok=True)
      shutil.move(filename, os.path.join(movedFolder, os.path.basename(filename)))
      with open(LOG_FILE, 'a') as f:
        f.write(f"Moved original image to backup: {filename}\n")
    except Exception as e:
      with open(LOG_FILE, 'a') as f:
        f.write(f"Error moving original image to backup: {filename}: {e}\n")